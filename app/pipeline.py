"""End-to-end policy gate pipeline for the T13 integration milestone.

This module is orchestration glue only. It does not encode allow/block/escalate
business rules: the binding decision comes from OPA, except for the explicit
fail-closed cases permitted by the spec when required context/sensors/OPA fail.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, Iterator

from app.audit.store import AuditStore, get_audit_store
from app.context import resolver as context_resolver
from app.enforcement.approval_queue import ApprovalQueue
from app.enforcement.handler import enforce
from app.normaliser.normaliser import normalise
from app.pep.sdk_wrapper import SDKWrapper
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
class TraceStage:
    """One stage's real, observed inputs/outputs for the T22 pipeline trace.

    Captured by `_StageRecorder` as each pipeline step actually runs; summaries
    are derived from the real objects produced by that step, never hardcoded.
    """

    stage_name: str
    timestamp: str
    duration_ms: float
    inputs_summary: dict[str, Any]
    outputs_summary: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "timestamp": self.timestamp,
            "duration_ms": round(self.duration_ms, 3),
            "inputs_summary": self.inputs_summary,
            "outputs_summary": self.outputs_summary,
        }


@dataclass
class PipelineTrace:
    """An ordered, stage-by-stage record of one pipeline run (T22)."""

    stages: list[TraceStage] = field(default_factory=list)

    def to_json(self) -> list[dict[str, Any]]:
        return [stage.to_json() for stage in self.stages]


class _StageRecorder:
    """Records stage timing/inputs/outputs into an optional `PipelineTrace`.

    When `trace` is `None` this degrades to a no-op context manager so existing
    callers (T13's JSON/HTML routes) pay no cost and see no behaviour change.
    """

    def __init__(self, trace: PipelineTrace | None) -> None:
        self.trace = trace

    @contextmanager
    def stage(self, stage_name: str, inputs_summary: dict[str, Any]) -> Iterator[dict[str, Any]]:
        outputs_summary: dict[str, Any] = {}
        if self.trace is None:
            yield outputs_summary
            return
        started_at = perf_counter()
        timestamp = datetime.now(UTC).isoformat()
        try:
            yield outputs_summary
        finally:
            duration_ms = (perf_counter() - started_at) * 1000
            self.trace.stages.append(
                TraceStage(
                    stage_name=stage_name,
                    timestamp=timestamp,
                    duration_ms=duration_ms,
                    inputs_summary=inputs_summary,
                    outputs_summary=dict(outputs_summary),
                )
            )


@dataclass(frozen=True)
class PipelineResult:
    """Structured result returned by one full pipeline run."""

    record: EvidenceRecord
    enforcement_outcome: Any
    trace: PipelineTrace | None = None

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
    sdk_wrapper: SDKWrapper = field(default_factory=SDKWrapper)
    opa_url: str | None = None
    # T24 trace linkage: every run's full stage-by-stage trace is kept here,
    # keyed by `correlation_id`, so a human reviewing an escalation can open
    # the *exact* evaluation that produced it rather than a fresh re-run of
    # the same scenario number (spec: traceability from decision to the
    # specific pipeline evaluation, not just the scenario it matches).
    trace_store: dict[str, PipelineTrace] = field(default_factory=dict)

    def get_trace(self, correlation_id: str) -> PipelineTrace | None:
        """Look up the stored trace for one specific evaluation by correlation_id."""

        return self.trace_store.get(correlation_id)

    def run_scenario(self, scenario_id: int, *, capture_trace: bool = False) -> PipelineResult:
        """Run one canonical scenario number through the full policy gate."""

        try:
            raw_tool_call = get_raw_tool_call(scenario_id)
        except ValueError as exc:
            raise UnknownScenarioError(str(exc)) from exc
        return self.run_event(raw_tool_call, capture_trace=capture_trace)

    def run_event(self, raw_tool_call: dict[str, Any], *, capture_trace: bool = False) -> PipelineResult:
        """Intercept a raw tool call (scenario or background event) and run it
        through the full pipeline, optionally exposing the resulting `PipelineTrace`
        on the returned `PipelineResult` (it is always persisted in `trace_store`)."""

        trace = PipelineTrace()
        recorder = _StageRecorder(trace)
        with recorder.stage(
            "intercept",
            {"tool_name": raw_tool_call.get("tool_name"), "scenario_id": raw_tool_call.get("scenario_id")},
        ) as outputs:
            intercepted_call = self.sdk_wrapper.call_tool(raw_tool_call)
            outputs["intercepted"] = True
        return self.run_raw_tool_call(
            intercepted_call, capture_trace=capture_trace, _recorder=recorder, _trace=trace
        )

    def run_raw_tool_call(
        self,
        raw_tool_call: dict[str, Any],
        *,
        capture_trace: bool | PipelineTrace | None = False,
        _recorder: "_StageRecorder | None" = None,
        _trace: "PipelineTrace | None" = None,
    ) -> PipelineResult:
        """Run one already-intercepted raw tool call through the pipeline.

        The full trace is always recorded and persisted into `trace_store`
        keyed by the action's `correlation_id` so it can be looked up later by
        that ID alone. `capture_trace` only controls whether the trace is also
        attached to the returned `PipelineResult` (a bare `bool`, back-compat
        default `False`); `_trace`/`_recorder` are used internally by
        `run_event`, which has already recorded the `intercept` stage.
        """

        trace = _trace if _trace is not None else (
            capture_trace if isinstance(capture_trace, PipelineTrace) else PipelineTrace()
        )
        recorder = _recorder if _recorder is not None else _StageRecorder(trace)

        with recorder.stage("normalise", {"tool_name": raw_tool_call.get("tool_name")}) as outputs:
            action = normalise(raw_tool_call)
            outputs["action_type"] = action.action_type.value
            outputs["correlation_id"] = str(action.correlation_id)

        with recorder.stage("resolve_context", {"resource_id": action.resource.id}) as outputs:
            context = context_resolver.resolve(
                action,
                force_failure=bool(raw_tool_call.get("force_context_failure", False)),
            )
            outputs["context_resolution_ok"] = context.context_resolution_ok
            outputs["customer_status"] = context.customer.status.value

        evidence = self._build_evidence_traced(action, recorder)

        settings = self.settings_store.read_settings()
        config = settings.to_policy_config()

        with recorder.stage(
            "policy_decision", {"threshold": config.get("high_confidence_threshold")}
        ) as outputs:
            decision = self._decide(action, context, evidence, config)
            outputs["decision"] = decision.decision.value
            outputs["control_id"] = decision.control_id
            outputs["triggered_controls"] = list(decision.triggered_controls)
            outputs["reason"] = decision.reason
            outputs["required_approval_role"] = decision.required_approval_role
            outputs["framework_mappings"] = list(decision.framework_mappings)
            outputs["failure_mode"] = decision.failure_mode.value
            outputs["logging_requirements"] = decision.logging_requirements.value
            outputs["policy_version"] = decision.policy_version
            outputs["threshold_used"] = decision.threshold_used

        with recorder.stage("enforce", {"enforcement_mode": action.enforcement_mode.value}) as outputs:
            outcome = enforce(
                decision,
                action.enforcement_mode,
                approval_queue=self.approval_queue,
                control_modes={key: EnforcementMode(value) for key, value in settings.control_modes.items()},
                correlation_id=str(action.correlation_id),
            )
            outputs["executed"] = outcome.executed
            outputs["queued"] = outcome.queued

        with recorder.stage("audit_write", {"record_type": RecordType.ACTION_EVALUATION.value}) as outputs:
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
            outputs["record_hash"] = record.record_hash
            outputs["record_id"] = record.id

        self.trace_store[str(action.correlation_id)] = trace

        return PipelineResult(record=record, enforcement_outcome=outcome, trace=trace)

    def _build_evidence_traced(self, action, recorder: "_StageRecorder") -> Evidence:
        """Build evidence inside a `semantic_evidence`/`semantic_skipped` trace stage."""

        if action.action_type != ActionType.COMMUNICATION_EMAIL_SEND:
            with recorder.stage(
                "semantic_skipped",
                {"action_type": action.action_type.value},
            ) as outputs:
                evidence = self._build_evidence(action)
                outputs["evaluated"] = evidence.evaluated
                outputs["note"] = "Semantic layer not invoked - structured action."
            return evidence

        with recorder.stage("semantic_evidence", {"action_type": action.action_type.value}) as outputs:
            evidence = self._build_evidence(action)
            outputs["evaluated"] = evidence.evaluated
            outputs["contains_special_category_data"] = evidence.contains_special_category_data
            outputs["detected_entities"] = [
                {"type": entity.type, "score": entity.score, "source": entity.source.value}
                for entity in evidence.detected_entities
            ]
            outputs["vulnerability_present"] = evidence.vulnerability_indicators.present
            outputs["vulnerability_confidence"] = evidence.vulnerability_indicators.confidence
            outputs["vulnerability_source"] = evidence.vulnerability_indicators.source.value
            outputs["overall_confidence"] = evidence.overall_confidence
        return evidence

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
        if self.settings_store.consume_opa_failure_simulation():
            return _fail_closed_decision(threshold, "Policy engine unreachable (one-shot demo simulation)")
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
