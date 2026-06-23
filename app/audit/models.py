"""Persistence-layer row representation for append-only audit records.

Mirrors `app.schemas.audit.EvidenceRecord` field-for-field (spec §5.5). This
module holds no policy logic; it only describes the shape of a stored row and
the genesis hash constant the store chains from.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

GENESIS_PREV_HASH = "0" * 64


@dataclass(frozen=True)
class AuditRow:
    """One stored audit row, matching `EvidenceRecord` field names exactly."""

    id: int
    correlation_id: UUID
    action: dict
    context_used: dict
    evidence: dict
    decision: dict
    enforcement_mode: str
    executed: bool
    record_type: str
    references_hash: str | None
    human_approver: str | None
    approval_reason: str | None
    created_at: datetime
    record_hash: str
    prev_hash: str
