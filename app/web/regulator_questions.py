"""Field-backed regulator-question rows for evidence records.

T26 deliberately adds no schema fields and makes no policy decisions.  This
module only maps existing persisted audit-record fields to the questions a
regulator or internal auditor would ask about one AI-agent action.
"""

from __future__ import annotations

from typing import Any

from app.schemas.audit import EvidenceRecord, RecordType
from app.schemas.decision import DecisionValue

RegulatorQuestionRow = dict[str, Any]


QUESTIONS = {
    "interception": "Was the action intercepted before execution?",
    "policy": "What policy/control was applied, and what does it map to?",
    "evidence": "What evidence and context informed the decision?",
    "judge": "Who or what made the decision — model or policy engine?",
    "human": "Was a human involved where judgement was required, and is that decision itself evidenced?",
    "integrity": "Can this record be shown to have not been altered after the fact?",
}


def build_regulator_question_rows(record: EvidenceRecord) -> list[RegulatorQuestionRow]:
    """Return ordered, display-ready rows backed only by fields on ``record``."""

    return [
        _interception_row(record),
        _policy_row(record),
        _evidence_context_row(record),
        _judge_row(record),
        _human_oversight_row(record),
        _integrity_row(record),
    ]


def _row(question_key: str, answer_field_label: str, answer_value: str) -> RegulatorQuestionRow:
    return {
        "question": QUESTIONS[question_key],
        "answer_field_label": answer_field_label,
        "answer_value": answer_value,
    }


def _interception_row(record: EvidenceRecord) -> RegulatorQuestionRow:
    action_type = record.action.action_type.value
    mode = record.enforcement_mode.value
    executed = record.executed
    if mode == "shadow":
        outcome = "executed because enforcement_mode is shadow, while the policy outcome was still captured before execution."
    elif executed:
        outcome = "executed only after the gate recorded the binding policy evaluation."
    else:
        outcome = "did not execute under the recorded enforcement outcome."
    return _row(
        "interception",
        "action.action_type; enforcement_mode; executed; decision.decision",
        f"Action type {action_type} was evaluated with decision.decision={record.decision.decision.value}; enforcement_mode={mode}; executed={executed} — {outcome}",
    )


def _policy_row(record: EvidenceRecord) -> RegulatorQuestionRow:
    decision = record.decision
    control = decision.control_id or "None (decision.control_id is null)"
    triggered = ", ".join(decision.triggered_controls) if decision.triggered_controls else "None (triggered_controls is empty)"
    mappings = _join_or_none(decision.framework_mappings, "framework_mappings is empty")
    logging = decision.logging_requirements.value
    return _row(
        "policy",
        "decision.control_id; decision.triggered_controls; decision.framework_mappings; decision.logging_requirements",
        f"Primary control: {control}. Triggered controls: {triggered}. Decision: {decision.decision.value}; logging_requirements={logging}. Illustrative mappings: {mappings}.",
    )


def _evidence_context_row(record: EvidenceRecord) -> RegulatorQuestionRow:
    context = record.context_used
    evidence = record.evidence
    customer_bits = (
        f"customer.status={context.customer.status.value}, fraud_flag={context.customer.fraud_flag}, "
        f"sanctions_match={context.customer.sanctions_match}, context_resolution_ok={context.context_resolution_ok}"
    )
    if not evidence.evaluated:
        semantic = (
            f"evidence.evaluated=False: semantic layer not invoked/not needed for action.action_type={record.action.action_type.value}; "
            "no semantic entities or model confidence are being invented for this payment path."
        )
    else:
        entity_summary = _entities_summary(record)
        categories = [category.value for category in evidence.vulnerability_indicators.categories]
        semantic = (
            f"evidence.evaluated=True with detected_entities={entity_summary}; "
            f"vulnerability_indicators.present={evidence.vulnerability_indicators.present}, "
            f"confidence={evidence.vulnerability_indicators.confidence:.2f}, categories={categories}, "
            f"overall_confidence={evidence.overall_confidence:.2f}, sensor_versions={evidence.sensor_versions}. "
            "Presidio is the real deterministic sensor; nuance_stub is a labelled model stand-in."
        )
    recipient = (
        f"recipient.is_external={context.recipient.is_external}, "
        f"recipient.domain={context.recipient.domain}, "
        f"approved_disclosure_basis={context.recipient.approved_disclosure_basis}"
    )
    return _row(
        "evidence",
        "context_used.customer.*; context_used.recipient.*; context_used.context_resolution_ok; evidence.evaluated; evidence.detected_entities; evidence.vulnerability_indicators; evidence.overall_confidence; evidence.sensor_versions",
        f"Context: {customer_bits}; {recipient}. Evidence: {semantic}",
    )


def _judge_row(record: EvidenceRecord) -> RegulatorQuestionRow:
    decision = record.decision
    fail_context = ""
    if decision.decision == DecisionValue.FAIL_CLOSED:
        fail_context = (
            f" Required operation failed or was unavailable: failure_mode={decision.failure_mode.value}, "
            f"context_resolution_ok={record.context_used.context_resolution_ok}, sensor_error={record.evidence.sensor_error}. "
            "The gate stopped by fail-closed policy rather than silently allowing."
        )
    return _row(
        "judge",
        "decision.decision; decision.reason; decision.policy_version; decision.failure_mode; evidence.sensor_versions; evidence.sensor_error; context_used.context_resolution_ok",
        f"OPA/the deterministic policy engine made the binding decision={decision.decision.value} under policy_version={decision.policy_version}. Reason: {decision.reason}. Evidence sensors only informed the policy; they did not decide. sensor_versions={record.evidence.sensor_versions}.{fail_context}",
    )


def _human_oversight_row(record: EvidenceRecord) -> RegulatorQuestionRow:
    decision = record.decision
    if record.record_type == RecordType.APPROVAL_DECISION:
        return _row(
            "human",
            "record_type; human_approver; approval_reason; references_hash; executed; decision.required_approval_role",
            f"record_type=approval_decision: appended human decision by human_approver={record.human_approver}; approval_reason={record.approval_reason}; references_hash={record.references_hash}; resulting executed={record.executed}. This evidences a new appended record, not a mutation of the original evaluation.",
        )
    if decision.required_approval_role:
        return _row(
            "human",
            "decision.required_approval_role; record_type; references_hash; human_approver; approval_reason; executed",
            f"decision.required_approval_role={decision.required_approval_role}; record_type={record.record_type.value}; this evaluation records the need for human judgement. human_approver={record.human_approver}, approval_reason={record.approval_reason}, references_hash={record.references_hash}; executed={record.executed} until an approval_decision record is appended.",
        )
    return _row(
        "human",
        "decision.required_approval_role; decision.decision; human_approver; approval_reason",
        f"No human approval was required by the binding decision: decision.required_approval_role={decision.required_approval_role}, decision.decision={decision.decision.value}. human_approver={record.human_approver}; approval_reason={record.approval_reason}.",
    )


def _integrity_row(record: EvidenceRecord) -> RegulatorQuestionRow:
    reference = f" references_hash={record.references_hash}." if record.references_hash else " references_hash=None."
    return _row(
        "integrity",
        "record_hash; prev_hash; references_hash",
        f"record_hash={record.record_hash}; prev_hash={record.prev_hash};{reference} These fields place this row in the append-only SHA-256 hash chain.",
    )


def _join_or_none(values: list[str], empty_label: str) -> str:
    return ", ".join(values) if values else f"None ({empty_label})"


def _entities_summary(record: EvidenceRecord) -> str:
    entities = record.evidence.detected_entities
    if not entities:
        return "[]"
    return ", ".join(f"{entity.type}:{entity.score:.2f}:{entity.source.value}" for entity in entities)
