"""Enforcement handler: applies an OPA Decision under an EnforcementMode.

This module never re-derives policy. It only reacts to `decision.decision`,
the binding value already resolved by OPA (T10), and decides whether the
action executes and/or is routed to the human approval queue (T11's
`approval_queue`). No persistence happens here — that is wired to the real
audit store in T12/T13.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.enforcement.approval_queue import ApprovalQueue, QueueItem
from app.schemas.action import EnforcementMode
from app.schemas.decision import Decision, DecisionValue

# Decisions that, if actually enforced in full mode, would not execute the action.
_NON_EXECUTING_DECISIONS = {
    DecisionValue.BLOCK,
    DecisionValue.ESCALATE,
    DecisionValue.REQUIRE_EVIDENCE,
    DecisionValue.MODIFY,
    DecisionValue.FAIL_CLOSED,
}


class EnforcementOutcome(BaseModel):
    """Result of applying a Decision under an EnforcementMode."""

    executed: bool = Field(..., description="Whether the underlying action was allowed to execute.")
    queued: bool = Field(..., description="Whether the decision was routed to the human approval queue.")
    would_have: str | None = Field(
        None,
        description=(
            "Shadow-style annotation naming what would have happened under full "
            "enforcement (e.g. 'would have blocked'); None outside shadow/soft-fallback."
        ),
    )
    decision: DecisionValue = Field(..., description="The underlying decision this outcome was derived from.")
    control_id: str | None = Field(None, description="Triggered control carried through for queueing/rendering.")
    required_approval_role: str | None = Field(None, description="Approval role carried through when queued.")
    reason: str | None = Field(None, description="Policy reason carried through for queueing/rendering.")
    queue_item: QueueItem | None = Field(None, description="The queue item created, when queued is True.")


def _would_have_annotation(decision: DecisionValue) -> str | None:
    """Build the shadow/soft-fallback annotation for a decision that did not actually enforce."""
    if decision in _NON_EXECUTING_DECISIONS:
        return f"would have {decision.value}"
    return None


def _apply_full_semantics(
    decision: Decision,
    approval_queue: ApprovalQueue | None,
    correlation_id: str | None,
) -> EnforcementOutcome:
    """Apply real enforcement semantics for a single decision (used by full mode and
    by soft mode for controls on the allow-list)."""
    value = decision.decision

    if value == DecisionValue.BLOCK:
        # Prohibited tier: a hard stop, never an escalation, never queued.
        return EnforcementOutcome(
            executed=False,
            queued=False,
            decision=value,
            control_id=decision.control_id,
            required_approval_role=decision.required_approval_role,
            reason=decision.reason,
        )

    if value == DecisionValue.ESCALATE:
        queue_item = None
        if approval_queue is not None:
            queue_item = approval_queue.enqueue(
                correlation_id=correlation_id,
                control_id=decision.control_id,
                required_approval_role=decision.required_approval_role,
                reason=decision.reason,
                decision=decision,
            )
        return EnforcementOutcome(
            executed=False,
            queued=True,
            decision=value,
            control_id=decision.control_id,
            required_approval_role=decision.required_approval_role,
            reason=decision.reason,
            queue_item=queue_item,
        )

    if value in (DecisionValue.REQUIRE_EVIDENCE, DecisionValue.MODIFY, DecisionValue.FAIL_CLOSED):
        # Conservative default per architect brief: not executed, not queued.
        # require_evidence/modify have no further handling defined for T11;
        # fail_closed is a safe default, not an escalation.
        return EnforcementOutcome(
            executed=False,
            queued=False,
            decision=value,
            control_id=decision.control_id,
            required_approval_role=decision.required_approval_role,
            reason=decision.reason,
        )

    # ALLOW / ALLOW_WITH_LOGGING
    return EnforcementOutcome(
        executed=True,
        queued=False,
        decision=value,
        control_id=decision.control_id,
        required_approval_role=decision.required_approval_role,
        reason=decision.reason,
    )


def _apply_shadow_semantics(decision: Decision) -> EnforcementOutcome:
    """Shadow mode always executes and never queues; annotate what would have happened."""
    return EnforcementOutcome(
        executed=True,
        queued=False,
        would_have=_would_have_annotation(decision.decision),
        decision=decision.decision,
        control_id=decision.control_id,
        required_approval_role=decision.required_approval_role,
        reason=decision.reason,
    )


def enforce(
    decision: Decision,
    enforcement_mode: EnforcementMode,
    approval_queue: ApprovalQueue | None = None,
    control_modes: dict[str, EnforcementMode] | None = None,
    correlation_id: str | None = None,
) -> EnforcementOutcome:
    """Apply `decision` under `enforcement_mode` and return the resulting outcome.

    Args:
        decision: The binding Decision already resolved by OPA.
        enforcement_mode: The run-level enforcement mode (shadow/soft/full).
        approval_queue: Queue to enqueue escalations into; required for any
            outcome that queues a human approval.
        control_modes: Per-control mode overrides consulted only in `soft`
            mode, keyed by control id (e.g. `decision.control_id`). A control
            present here with value `EnforcementMode.FULL` is treated as
            enforced; absence (or any other value) falls back to shadow-style
            behaviour.
        correlation_id: Workflow correlation id carried onto queued items.
    """
    if enforcement_mode == EnforcementMode.SHADOW:
        return _apply_shadow_semantics(decision)

    if enforcement_mode == EnforcementMode.SOFT:
        control_modes = control_modes or {}
        is_enforced = control_modes.get(decision.control_id) == EnforcementMode.FULL
        if is_enforced:
            return _apply_full_semantics(decision, approval_queue, correlation_id)
        return _apply_shadow_semantics(decision)

    # FULL
    return _apply_full_semantics(decision, approval_queue, correlation_id)
