"""Illustrative evidence-sufficiency checklist for audit records.

T28 adds no persistence, schema, policy, or scenario behaviour.  The functions
in this module are pure evaluators over already-loaded record objects/dicts and
linked approval records supplied by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from app.audit.models import GENESIS_PREV_HASH
from app.schemas.audit import RecordType
from app.schemas.decision import DecisionValue

CONTROL_MAPPING_LABEL = "Framework/control mapping present"
HUMAN_OVERSIGHT_LABEL = "Human oversight evidenced where required"


@dataclass(frozen=True)
class SufficiencyItem:
    """One display-ready, field-backed sufficiency criterion."""

    key: str
    label: str
    status: str
    evidence: str


def build_sufficiency_checklist(record: Any, linked_approval_records: Iterable[Any] | None = None) -> list[SufficiencyItem]:
    """Evaluate illustrative sufficiency criteria from existing record fields only.

    ``linked_approval_records`` must be supplied by the route/store caller. This
    function intentionally does not query the database, call OPA/sensors, mutate
    records, or special-case scenario numbers.
    """

    linked = list(linked_approval_records or [])
    return [
        _interception_item(record),
        _decision_rationale_item(record),
        _control_mapping_item(record),
        _chain_position_item(record),
        _human_oversight_item(record, linked),
    ]


def _interception_item(record: Any) -> SufficiencyItem:
    if _record_type(record) == "approval_decision":
        fields = _present_fields(record, "references_hash", "human_approver", "approval_reason", "executed")
        if fields:
            return _item(
                "interception",
                "Pre-execution/intervention evidence",
                "met",
                "This approval_decision is an appended human intervention record: references_hash, approver, reason, and resulting executed state are present.",
            )
        return _item("interception", "Pre-execution/intervention evidence", "missing", "Approval-decision intervention fields are incomplete.")

    if _has_value(record, "executed") and _has_value(record, "enforcement_mode"):
        return _item(
            "interception",
            "Pre-execution interception evidenced",
            "met",
            f"executed={_value(record, 'executed')} and enforcement_mode={_enum_value(_value(record, 'enforcement_mode'))} are recorded for this evaluation.",
        )
    return _item(
        "interception",
        "Pre-execution interception evidenced",
        "missing",
        "Missing executed and/or enforcement_mode, so the record cannot show how the gate handled execution.",
    )


def _decision_rationale_item(record: Any) -> SufficiencyItem:
    if _record_type(record) == "approval_decision":
        if _has_value(record, "approval_reason"):
            return _item("decision_rationale", "Human decision rationale recorded", "met", f"approval_reason={_value(record, 'approval_reason')!r}.")
        return _item("decision_rationale", "Human decision rationale recorded", "missing", "approval_reason is empty or absent.")

    reason = _value(_value(record, "decision"), "reason")
    if reason:
        return _item("decision_rationale", "Decision rationale recorded", "met", f"decision.reason={reason!r}.")
    return _item("decision_rationale", "Decision rationale recorded", "missing", "decision.reason is empty or absent.")


def _control_mapping_item(record: Any) -> SufficiencyItem:
    if _record_type(record) == "approval_decision":
        return _item(
            "control_mapping",
            CONTROL_MAPPING_LABEL,
            "not-applicable",
            "This is an approval_decision record; the original action_evaluation carries the applied control/framework mapping.",
        )

    decision = _value(record, "decision")
    control_id = _value(decision, "control_id")
    triggered = _value(decision, "triggered_controls") or []
    mappings = _value(decision, "framework_mappings") or []
    decision_value = _enum_value(_value(decision, "decision"))
    if mappings and (control_id or triggered):
        return _item("control_mapping", CONTROL_MAPPING_LABEL, "met", f"control_id={control_id}; framework_mappings={mappings}.")
    if decision_value == "allow" and not control_id and not triggered:
        return _item("control_mapping", CONTROL_MAPPING_LABEL, "not-applicable", "Clean allow with no triggered control; no framework mapping is required for this record shape.")
    return _item("control_mapping", CONTROL_MAPPING_LABEL, "missing", "A control-triggered decision should carry control_id/triggered_controls and framework_mappings.")


def _chain_position_item(record: Any) -> SufficiencyItem:
    record_hash = _value(record, "record_hash")
    prev_hash = _value(record, "prev_hash")
    if record_hash and prev_hash:
        genesis_note = " (genesis/first-record prev_hash)" if prev_hash == GENESIS_PREV_HASH else ""
        return _item("chain_position", "Tamper-evident chain position recorded", "met", f"record_hash and prev_hash are present{genesis_note}.")
    return _item("chain_position", "Tamper-evident chain position recorded", "missing", "record_hash and/or prev_hash is absent.")


def _human_oversight_item(record: Any, linked_approval_records: list[Any]) -> SufficiencyItem:
    if _record_type(record) == "approval_decision":
        if _present_fields(record, "references_hash", "human_approver", "approval_reason", "executed"):
            return _item(
                "human_oversight",
                HUMAN_OVERSIGHT_LABEL,
                "met",
                f"approval_decision records human_approver={_value(record, 'human_approver')!r}, approval_reason, references_hash={_value(record, 'references_hash')}, executed={_value(record, 'executed')}.",
            )
        return _item("human_oversight", HUMAN_OVERSIGHT_LABEL, "missing", "Approval record is missing approver, reason, reference hash, or executed state.")

    decision = _value(record, "decision")
    requires_human = _enum_value(_value(decision, "decision")) == "escalate" or bool(_value(decision, "required_approval_role"))
    if not requires_human:
        return _item("human_oversight", HUMAN_OVERSIGHT_LABEL, "not-applicable", "The binding decision did not require human approval.")

    original_hash = _value(record, "record_hash")
    correlation = str(_value(record, "correlation_id"))
    for approval in linked_approval_records:
        if (
            _record_type(approval) == "approval_decision"
            and _value(approval, "references_hash") == original_hash
            and str(_value(approval, "correlation_id")) == correlation
            and _has_value(approval, "human_approver")
            and _has_value(approval, "approval_reason")
            and _has_value(approval, "executed")
        ):
            return _item(
                "human_oversight",
                HUMAN_OVERSIGHT_LABEL,
                "met",
                f"Linked approval_decision by {_value(approval, 'human_approver')!r} references this record_hash and records a reason/result.",
            )
    role = _value(decision, "required_approval_role") or "required approval role"
    return _item("human_oversight", HUMAN_OVERSIGHT_LABEL, "pending", f"Decision requires {role}; no linked approval_decision record is present yet.")


def _item(key: str, label: str, status: str, evidence: str) -> SufficiencyItem:
    return SufficiencyItem(key=key, label=label, status=status, evidence=evidence)


def _value(obj: Any, name: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _has_value(obj: Any, name: str) -> bool:
    value = _value(obj, name)
    return value is not None and value != "" and value != []


def _present_fields(obj: Any, *names: str) -> bool:
    return all(_has_value(obj, name) for name in names)


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return getattr(value, "value", value)


def _record_type(record: Any) -> str | None:
    value = _enum_value(_value(record, "record_type"))
    if value == RecordType.ACTION_EVALUATION.value:
        return "action_evaluation"
    if value == RecordType.APPROVAL_DECISION.value:
        return "approval_decision"
    return value
