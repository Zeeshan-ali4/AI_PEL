"""End-to-end policy gate pipeline for the T13 integration milestone.

This module is orchestration glue only. It does not encode allow/block/escalate
business rules: the binding decision comes from OPA, except for the explicit
fail-closed cases permitted by the spec when required context/sensors/OPA fail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.audit.store import AuditStore, get_audit_store
from app.context import resolver as context_resolver
from app.enforcement.approval_queue import ApprovalQueue
from app.enforcement.handler import enforce
from app.normaliser.normaliser import normalise
from app.policy import opa_client
from app.schemas.action import ActionType, EnforcementMode
from app.schemas.audit import EvidenceRecord, RecordType
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence
from app.semantic import evidence_builder
from app.settings_store import SettingsStore
from scenarios.scenarios import get_raw_tool_call

FAIL_CLOSED_FRAMEWORK_MAPPINGS = [
    "Internal AI Governance Policy (safe-default)",
    "ISO/IEC 42001 (robustness)",
]


class UnknownScenarioError(ValueError):
    """Raised when the JSON endpoint is asked to run a non-existent scenario."""


@dataclass(frozen=True)
class PipelineResult:
    """Structured result returned by one full pipeline run."""

    record: EvidenceRecord
    enforcement_outcome: Any

    @property
    def decision(self) -> Decision:
        return self.record.decision

    def response_payload(self) -> dict[str, Any]:
        """Return the minimal stable JSON envelope required by T13."""

        payload: dict[str, Any] = {
            "decision": self.decision.model_dump(mode="json"),
            "record_hash": self.record.record_hash,
            "record_id": self.record.id,
            "correlation_id": str(self.record.correlation_id),
            "executed": self.record.executed,
            "enforcement": self.enforcement_outcome.model_dump(mode="json"),
        }
        return payload


@dataclass
class PolicyPipeline:
    """Orchestrates intercept → normalise → context → evidence → OPA → enforce → audit."""

    settings_store: SettingsStore = field(default_factory=SettingsStore)
    audit_store: AuditStore = field(default_factory=get_audit_store)
    approval_queue: ApprovalQueue = field(default_factory=ApprovalQueue)
    opa_url: str | None = None

    def run_scenario(self, scenario_id: int) -> PipelineResult:
        """Run one canonical scenario number through the full policy gate."""

        try:
            raw_tool_call = get_raw_tool_call(scenario_id)
        except ValueError as exc:
            raise UnknownScenarioError(str(exc)) from exc
        return self.run_raw_tool_call(raw_tool_call)

    def run_raw_tool_call(self, raw_tool_call: dict[str, Any]) -> PipelineResult:
        """Run one already-intercepted raw tool call through the pipeline."""

        action = normalise(raw_tool_call)
        context = context_resolver.resolve(
            action,
            force_failure=bool(raw_tool_call.get("force_context_failure", False)),
        )
        evidence = self._build_evidence(action)
        settings = self.settings_store.read_settings()
        config = settings.to_policy_config()

        decision = self._decide(action, context, evidence, config)
        outcome = enforce(
            decision,
            action.enforcement_mode,
            approval_queue=self.approval_queue,
            control_modes={key: EnforcementMode(value) for key, value in settings.control_modes.items()},
            correlation_id=str(action.correlation_id),
        )
        record = self.audit_store.write_record(
            action=action,
            context_used=context,
            evidence=evidence,
            decision=decision,
            enforcement_mode=action.enforcement_mode,
            executed=outcome.executed,
            record_type=RecordType.ACTION_EVALUATION,
            correlation_id=action.correlation_id,
        )
        return PipelineResult(record=record, enforcement_outcome=outcome)

    def _build_evidence(self, action) -> Evidence:
        """Build semantic evidence, preserving the payment path's unevaluated evidence."""

        if action.action_type != ActionType.COMMUNICATION_EMAIL_SEND:
            return evidence_builder.build_evidence(action)
        try:
            return evidence_builder.build_evidence(action)
        except Exception:
            # Defensive fail-closed guard. The T07 builder normally converts sensor
            # exceptions to sensor_error evidence; if a boundary escapes, T13 still
            # writes a fail-closed record instead of guessing.
            return Evidence(
                evaluated=True,
                contains_personal_data=False,
                contains_special_category_data=False,
                sensitivity_level="low",
                detected_entities=[],
                evidence_spans=[],
                vulnerability_indicators={
                    "present": False,
                    "confidence": 0.0,
                    "categories": [],
                    "source": "nuance_stub",
                },
                overall_confidence=0.0,
                sensor_versions={"presidio": "unknown", "nuance_stub": "stub-0.1"},
                sensor_error=True,
            )

    def _decide(self, action, context: Context, evidence: Evidence, config: dict[str, Any]) -> Decision:
        threshold = float(config.get("high_confidence_threshold", 0.75))
        if not context.context_resolution_ok:
            return _fail_closed_decision(threshold, "Context resolution failed")
        if evidence.sensor_error:
            return _fail_closed_decision(threshold, "Semantic sensor failed")
        return opa_client.decide(action, context, evidence, config, opa_url=self.opa_url)


def _fail_closed_decision(threshold: float, reason: str) -> Decision:
    """Build the only Python-originated decision permitted by the spec."""

    return Decision(
        decision="fail_closed",
        control_id=None,
        triggered_controls=[],
        reason=reason,
        required_approval_role=None,
        framework_mappings=list(FAIL_CLOSED_FRAMEWORK_MAPPINGS),
        failure_mode="fail_closed",
        logging_requirements="enhanced",
        policy_version="pipeline-fail-closed",
        threshold_used=threshold,
    )


_default_pipeline: PolicyPipeline | None = None


def get_pipeline() -> PolicyPipeline:
    """Return the process-local pipeline used by the JSON route."""

    global _default_pipeline
    if _default_pipeline is None:
        _default_pipeline = PolicyPipeline()
    return _default_pipeline
