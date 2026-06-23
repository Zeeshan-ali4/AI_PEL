"""Acceptance tests for app.enforcement.handler.enforce across shadow/soft/full modes."""

import pytest

from app.enforcement.approval_queue import ApprovalQueue
from app.enforcement.handler import enforce
from app.schemas.action import EnforcementMode
from app.schemas.decision import Decision, DecisionValue, FailureMode, LoggingRequirements


def _decision(
    decision: DecisionValue,
    control_id: str | None = None,
    required_approval_role: str | None = None,
    threshold_used: float = 0.75,
) -> Decision:
    return Decision(
        decision=decision,
        control_id=control_id,
        triggered_controls=[control_id] if control_id else [],
        reason=f"test reason for {decision.value}",
        required_approval_role=required_approval_role,
        framework_mappings=[],
        failure_mode=FailureMode.FAIL_CLOSED,
        logging_requirements=LoggingRequirements.STANDARD,
        policy_version="test-1",
        threshold_used=threshold_used,
    )


def test_block_full_not_executed_not_queued():
    queue = ApprovalQueue()
    decision = _decision(DecisionValue.BLOCK, control_id="FIN-PAY-001")

    outcome = enforce(decision, EnforcementMode.FULL, approval_queue=queue)

    assert outcome.executed is False
    assert outcome.queued is False
    assert queue.list_pending() == []


def test_escalate_full_not_executed_and_queued_with_role():
    queue = ApprovalQueue()
    decision = _decision(
        DecisionValue.ESCALATE, control_id="FIN-PAY-002", required_approval_role="finance_supervisor"
    )

    outcome = enforce(decision, EnforcementMode.FULL, approval_queue=queue)

    assert outcome.executed is False
    assert outcome.queued is True
    assert outcome.queue_item is not None
    assert outcome.queue_item.required_approval_role == "finance_supervisor"
    assert outcome.queue_item.control_id == "FIN-PAY-002"
    assert outcome.queue_item.reason == decision.reason
    assert len(queue.list_pending()) == 1


def test_block_shadow_executes_with_would_have_blocked_annotation():
    queue = ApprovalQueue()
    decision = _decision(DecisionValue.BLOCK, control_id="FIN-PAY-001")

    outcome = enforce(decision, EnforcementMode.SHADOW, approval_queue=queue)

    assert outcome.executed is True
    assert outcome.queued is False
    assert outcome.would_have is not None
    assert "block" in outcome.would_have
    assert queue.list_pending() == []


def test_escalate_shadow_executes_with_would_have_escalated_annotation_not_queued():
    queue = ApprovalQueue()
    decision = _decision(
        DecisionValue.ESCALATE, control_id="COMM-EMAIL-001", required_approval_role="data_protection_approver"
    )

    outcome = enforce(decision, EnforcementMode.SHADOW, approval_queue=queue)

    assert outcome.executed is True
    assert outcome.queued is False
    assert outcome.would_have is not None
    assert "escalate" in outcome.would_have
    assert queue.list_pending() == []


def test_allow_full_executed_not_queued():
    decision = _decision(DecisionValue.ALLOW)

    outcome = enforce(decision, EnforcementMode.FULL)

    assert outcome.executed is True
    assert outcome.queued is False
    assert outcome.would_have is None


def test_allow_with_logging_full_executed_not_queued():
    decision = _decision(DecisionValue.ALLOW_WITH_LOGGING, control_id="COMM-EMAIL-003")

    outcome = enforce(decision, EnforcementMode.FULL)

    assert outcome.executed is True
    assert outcome.queued is False


def test_fail_closed_full_not_executed_not_queued():
    decision = _decision(DecisionValue.FAIL_CLOSED)

    outcome = enforce(decision, EnforcementMode.FULL)

    assert outcome.executed is False
    assert outcome.queued is False


def test_fail_closed_shadow_executes_with_would_have_failed_closed_annotation():
    decision = _decision(DecisionValue.FAIL_CLOSED)

    outcome = enforce(decision, EnforcementMode.SHADOW)

    assert outcome.executed is True
    assert outcome.queued is False
    assert outcome.would_have is not None
    assert "fail_closed" in outcome.would_have


def test_soft_mode_enforced_control_applies_full_semantics():
    queue = ApprovalQueue()
    decision = _decision(
        DecisionValue.ESCALATE, control_id="FIN-PAY-002", required_approval_role="finance_supervisor"
    )
    control_modes = {"FIN-PAY-002": EnforcementMode.FULL}

    outcome = enforce(decision, EnforcementMode.SOFT, approval_queue=queue, control_modes=control_modes)

    assert outcome.executed is False
    assert outcome.queued is True
    assert len(queue.list_pending()) == 1


def test_soft_mode_unenforced_control_falls_back_to_shadow_behaviour():
    queue = ApprovalQueue()
    decision = _decision(DecisionValue.BLOCK, control_id="FIN-PAY-001")
    control_modes: dict[str, EnforcementMode] = {}

    outcome = enforce(decision, EnforcementMode.SOFT, approval_queue=queue, control_modes=control_modes)

    assert outcome.executed is True
    assert outcome.queued is False
    assert outcome.would_have is not None
    assert "block" in outcome.would_have
    assert queue.list_pending() == []


@pytest.mark.parametrize("decision_value", [DecisionValue.REQUIRE_EVIDENCE, DecisionValue.MODIFY])
def test_require_evidence_and_modify_full_default_to_not_executed_not_queued(decision_value):
    decision = _decision(decision_value)

    outcome = enforce(decision, EnforcementMode.FULL)

    assert outcome.executed is False
    assert outcome.queued is False
