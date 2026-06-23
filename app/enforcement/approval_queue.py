"""In-memory, append-only approval queue.

This is a placeholder contract for the human approval queue. A real,
persistent, hash-chained backing arrives in T12/T13 (the audit store).
Here, queued items and their approval/rejection records are plain in-process
data: nothing is ever mutated in place, only appended.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.schemas.decision import Decision


class QueueItem(BaseModel):
    """A pending (or actioned) escalation awaiting a human decision."""

    item_id: str = Field(..., description="Stable identifier for this queued item.")
    correlation_id: str | None = Field(None, description="Workflow correlation id this item belongs to.")
    control_id: str | None = Field(None, description="Triggered control that caused the escalation.")
    required_approval_role: str | None = Field(None, description="Named role required to action this item.")
    reason: str = Field(..., description="Policy reason carried over for human review.")
    decision: Decision = Field(..., description="Full underlying Decision, for rendering in the approvals UI.")
    created_at: datetime = Field(..., description="When this item was enqueued.")


class ApprovalDecisionRecord(BaseModel):
    """An appended, linked human approval/rejection record.

    Maps cleanly onto the future EvidenceRecord with
    `record_type="approval_decision"`. `references_hash` is intentionally
    None here — real hash chaining is T12's responsibility.
    """

    item_id: str = Field(..., description="Identifier of the queued item this record actions.")
    approved: bool = Field(..., description="Whether the human approved (True) or rejected (False).")
    human_approver: str = Field(..., description="Identity of the human who made the decision.")
    approval_reason: str = Field(..., description="Required human-supplied reason for the decision.")
    executed: bool = Field(..., description="Resulting execution state: True if approved, False if rejected.")
    references_hash: str | None = Field(None, description="Placeholder; real value assigned by the audit store in T12.")
    created_at: datetime = Field(..., description="When this approval decision was recorded.")


class ApprovalQueue:
    """Append-only, in-memory queue of escalations awaiting human decision."""

    def __init__(self) -> None:
        self._items: dict[str, QueueItem] = {}
        self._approval_records: dict[str, list[ApprovalDecisionRecord]] = {}

    def enqueue(
        self,
        *,
        correlation_id: str | None,
        control_id: str | None,
        required_approval_role: str | None,
        reason: str,
        decision: Decision,
    ) -> QueueItem:
        """Add a new pending escalation. Queued items are never mutated in place."""
        item = QueueItem(
            item_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            control_id=control_id,
            required_approval_role=required_approval_role,
            reason=reason,
            decision=decision,
            created_at=datetime.now(timezone.utc),
        )
        self._items[item.item_id] = item
        return item

    def get(self, item_id: str) -> QueueItem | None:
        """Look up a queued item by id, regardless of whether it has been actioned."""
        return self._items.get(item_id)

    def list_pending(self) -> list[QueueItem]:
        """List queued items that have no linked approval/rejection record yet."""
        return [item for item_id, item in self._items.items() if item_id not in self._approval_records]

    def list_approval_records(self, item_id: str) -> list[ApprovalDecisionRecord]:
        """List all appended approval/rejection records linked to a queued item."""
        return list(self._approval_records.get(item_id, []))

    def record_approval_decision(
        self,
        item_id: str,
        approved: bool,
        human_approver: str,
        reason: str,
    ) -> ApprovalDecisionRecord:
        """Append a new linked approval/rejection record. Never mutates the original item."""
        record = ApprovalDecisionRecord(
            item_id=item_id,
            approved=approved,
            human_approver=human_approver,
            approval_reason=reason,
            executed=approved,
            references_hash=None,
            created_at=datetime.now(timezone.utc),
        )
        self._approval_records.setdefault(item_id, []).append(record)
        return record
