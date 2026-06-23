"""Acceptance tests for app.enforcement.approval_queue.ApprovalQueue."""

from app.enforcement.approval_queue import ApprovalQueue
from app.schemas.decision import Decision, DecisionValue, FailureMode, LoggingRequirements


def _decision(decision: DecisionValue = DecisionValue.ESCALATE, control_id: str | None = "FIN-PAY-002") -> Decision:
    return Decision(
        decision=decision,
        control_id=control_id,
        triggered_controls=[control_id] if control_id else [],
        reason="needs human review",
        required_approval_role="finance_supervisor",
        framework_mappings=[],
        failure_mode=FailureMode.FAIL_CLOSED,
        logging_requirements=LoggingRequirements.STANDARD,
        policy_version="test-1",
        threshold_used=0.75,
    )


def test_enqueue_creates_pending_item_with_required_fields():
    queue = ApprovalQueue()
    decision = _decision()

    item = queue.enqueue(
        correlation_id="corr-1",
        control_id="FIN-PAY-002",
        required_approval_role="finance_supervisor",
        reason="needs human review",
        decision=decision,
    )

    assert item.item_id
    assert item.correlation_id == "corr-1"
    assert item.control_id == "FIN-PAY-002"
    assert item.required_approval_role == "finance_supervisor"
    assert item.reason == "needs human review"
    assert item in queue.list_pending()


def test_pending_lookup_excludes_actioned_items():
    queue = ApprovalQueue()
    item_a = queue.enqueue(
        correlation_id="corr-a",
        control_id="FIN-PAY-002",
        required_approval_role="finance_supervisor",
        reason="reason a",
        decision=_decision(),
    )
    item_b = queue.enqueue(
        correlation_id="corr-b",
        control_id="COMM-EMAIL-001",
        required_approval_role="data_protection_approver",
        reason="reason b",
        decision=_decision(control_id="COMM-EMAIL-001"),
    )

    queue.record_approval_decision(item_a.item_id, approved=True, human_approver="alice", reason="ok")

    pending_ids = {item.item_id for item in queue.list_pending()}
    assert pending_ids == {item_b.item_id}
    assert queue.get(item_a.item_id) is not None


def test_approve_appends_linked_record_without_mutating_original():
    queue = ApprovalQueue()
    item = queue.enqueue(
        correlation_id="corr-1",
        control_id="FIN-PAY-002",
        required_approval_role="finance_supervisor",
        reason="needs human review",
        decision=_decision(),
    )
    snapshot = item.model_copy(deep=True)

    record = queue.record_approval_decision(
        item.item_id, approved=True, human_approver="alice", reason="verified with customer"
    )

    assert record.human_approver == "alice"
    assert record.approval_reason == "verified with customer"
    assert record.executed is True

    refetched = queue.get(item.item_id)
    assert refetched == snapshot


def test_reject_appends_linked_record_with_executed_false():
    queue = ApprovalQueue()
    item = queue.enqueue(
        correlation_id="corr-1",
        control_id="FIN-PAY-002",
        required_approval_role="finance_supervisor",
        reason="needs human review",
        decision=_decision(),
    )

    record = queue.record_approval_decision(
        item.item_id, approved=False, human_approver="bob", reason="insufficient justification"
    )

    assert record.human_approver == "bob"
    assert record.approval_reason == "insufficient justification"
    assert record.executed is False


def test_approval_record_carries_no_real_hash_placeholder():
    queue = ApprovalQueue()
    item = queue.enqueue(
        correlation_id="corr-1",
        control_id="FIN-PAY-002",
        required_approval_role="finance_supervisor",
        reason="needs human review",
        decision=_decision(),
    )

    record = queue.record_approval_decision(item.item_id, approved=True, human_approver="alice", reason="ok")

    assert record.references_hash is None
