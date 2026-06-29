from __future__ import annotations

from copy import deepcopy

from app.audit.sufficiency import build_sufficiency_checklist
from app.schemas.audit import RecordType
from tests.T12_audit.conftest import sample_action, sample_context, sample_decision, sample_evidence


def _by_key(items):
    return {item.key: item for item in items}


def _write_record(store, *, decision="allow", control_id=None, mappings=None, required_role=None, executed=True, record_type=RecordType.ACTION_EVALUATION, references_hash=None, human_approver=None, approval_reason=None, correlation_id=None):
    action = sample_action(correlation_id=correlation_id)
    decision_obj = sample_decision(decision=decision, control_id=control_id)
    decision_obj.framework_mappings = mappings if mappings is not None else []
    decision_obj.required_approval_role = required_role
    return store.write_record(
        action=action,
        context_used=sample_context(),
        evidence=sample_evidence(),
        decision=decision_obj,
        enforcement_mode="full",
        executed=executed,
        record_type=record_type,
        references_hash=references_hash,
        human_approver=human_approver,
        approval_reason=approval_reason,
        correlation_id=correlation_id or action.correlation_id,
    )


def test_allow_record_marks_core_evidence_met_and_human_oversight_not_applicable(wired_pipeline):
    record = _write_record(wired_pipeline.audit_store)
    rows = _by_key(build_sufficiency_checklist(record))
    assert len(rows) >= 5
    assert rows["interception"].status == "met"
    assert rows["decision_rationale"].status == "met"
    assert rows["chain_position"].status == "met"
    assert rows["human_oversight"].status == "not-applicable"


def test_allow_with_logging_record_accepts_framework_mapping_as_evidence(wired_pipeline):
    record = _write_record(wired_pipeline.audit_store, decision="allow_with_logging", control_id="COMM-EMAIL-003", mappings=["Internal Data Disclosure Policy"])
    rows = _by_key(build_sufficiency_checklist(record))
    assert rows["control_mapping"].status == "met"
    assert rows["human_oversight"].status == "not-applicable"


def test_control_mapping_not_applicable_when_allow_has_no_triggered_control(wired_pipeline):
    record = _write_record(wired_pipeline.audit_store)
    rows = _by_key(build_sufficiency_checklist(record))
    assert record.decision.control_id is None
    assert record.decision.triggered_controls == []
    assert record.decision.framework_mappings == []
    assert rows["control_mapping"].status == "not-applicable"


def test_pending_escalation_marks_human_oversight_pending_or_missing(wired_pipeline):
    record = _write_record(wired_pipeline.audit_store, decision="escalate", control_id="FIN-PAY-002", mappings=["Internal Delegated-Authority Policy"], required_role="finance_supervisor", executed=False)
    rows = _by_key(build_sufficiency_checklist(record))
    assert rows["human_oversight"].status == "pending"
    assert "no linked approval_decision" in rows["human_oversight"].evidence
    assert rows["decision_rationale"].status == "met"
    assert rows["chain_position"].status == "met"


def test_approved_escalation_marks_human_oversight_met_when_linked_approval_supplied(wired_pipeline):
    original = _write_record(wired_pipeline.audit_store, decision="escalate", control_id="FIN-PAY-002", mappings=["Internal Delegated-Authority Policy"], required_role="finance_supervisor", executed=False)
    approval = _write_record(
        wired_pipeline.audit_store,
        decision="escalate",
        control_id="FIN-PAY-002",
        mappings=["Internal Delegated-Authority Policy"],
        required_role="finance_supervisor",
        executed=True,
        record_type=RecordType.APPROVAL_DECISION,
        references_hash=original.record_hash,
        human_approver="j.smith@internal.example",
        approval_reason="Approved after review",
        correlation_id=original.correlation_id,
    )
    rows = _by_key(build_sufficiency_checklist(original, [approval]))
    assert rows["human_oversight"].status == "met"
    assert "j.smith@internal.example" in rows["human_oversight"].evidence
    assert wired_pipeline.audit_store.read_records()[0].record_hash == original.record_hash


def test_approval_decision_record_uses_approval_specific_evidence(wired_pipeline):
    original = _write_record(wired_pipeline.audit_store, decision="escalate", control_id="FIN-PAY-002", mappings=["Internal Delegated-Authority Policy"], required_role="finance_supervisor", executed=False)
    approval = _write_record(wired_pipeline.audit_store, decision="escalate", control_id="FIN-PAY-002", mappings=["Internal Delegated-Authority Policy"], required_role="finance_supervisor", executed=False, record_type=RecordType.APPROVAL_DECISION, references_hash=original.record_hash, human_approver="dpo@example.internal", approval_reason="Rejected for missing detail", correlation_id=original.correlation_id)
    rows = _by_key(build_sufficiency_checklist(approval))
    assert rows["interception"].status == "met"
    assert rows["decision_rationale"].status == "met"
    assert rows["human_oversight"].status == "met"
    assert rows["control_mapping"].status == "not-applicable"


def test_fail_closed_record_reports_available_evidence_without_treating_failure_as_certification_failure(wired_pipeline):
    record = _write_record(wired_pipeline.audit_store, decision="fail_closed")
    rows = _by_key(build_sufficiency_checklist(record))
    assert rows["decision_rationale"].status == "met"
    assert rows["chain_position"].status == "met"
    assert rows["human_oversight"].status == "not-applicable"


def test_incomplete_record_marks_missing_fields_from_actual_absence(wired_pipeline):
    record = _write_record(wired_pipeline.audit_store).model_dump()
    record["decision"]["reason"] = ""
    record["record_hash"] = ""
    record["enforcement_mode"] = None
    rows = _by_key(build_sufficiency_checklist(record))
    assert rows["decision_rationale"].status == "missing"
    assert rows["chain_position"].status == "missing"
    assert rows["interception"].status == "missing"
    assert rows["human_oversight"].status == "not-applicable"


def test_sufficiency_function_has_no_database_or_policy_side_effects(wired_pipeline):
    record = _write_record(wired_pipeline.audit_store).model_dump()
    before = deepcopy(record)
    assert build_sufficiency_checklist(record) == build_sufficiency_checklist(record)
    assert record == before
