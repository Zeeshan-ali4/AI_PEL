from __future__ import annotations

from app.schemas.audit import EvidenceRecord
from tests.T12_audit.conftest import sample_action, sample_context, sample_decision, sample_evidence


def test_write_record_round_trips_action_evaluation(store):
    action = sample_action()
    row = store.write_record(
        action=action,
        context_used=sample_context(),
        evidence=sample_evidence(),
        decision=sample_decision(decision="escalate", control_id="FIN-PAY-002"),
        enforcement_mode="full",
        executed=False,
        record_type="action_evaluation",
    )

    assert row.record_type == "action_evaluation"
    assert row.references_hash is None
    assert row.human_approver is None
    assert row.approval_reason is None
    assert EvidenceRecord.model_validate(row.model_dump())


def test_write_record_round_trips_approval_decision_with_references_hash(store):
    action = sample_action()
    original = store.write_record(
        action=action,
        context_used=sample_context(),
        evidence=sample_evidence(),
        decision=sample_decision(decision="escalate", control_id="FIN-PAY-002"),
        enforcement_mode="full",
        executed=False,
        record_type="action_evaluation",
    )

    approval = store.write_record(
        action=action,
        context_used=sample_context(),
        evidence=sample_evidence(),
        decision=sample_decision(decision="allow_with_logging"),
        enforcement_mode="full",
        executed=True,
        record_type="approval_decision",
        references_hash=original.record_hash,
        human_approver="finance_supervisor",
        approval_reason="approved per policy exception",
        correlation_id=action.correlation_id,
    )

    assert approval.id != original.id
    assert approval.prev_hash == original.record_hash
    assert approval.references_hash == original.record_hash
    assert approval.correlation_id == original.correlation_id

    reread_original = next(record for record in store.read_records() if record.id == original.id)
    assert reread_original.record_hash == original.record_hash
    assert reread_original.executed == original.executed
    assert reread_original.record_type == original.record_type
