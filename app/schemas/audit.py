"""Canonical EvidenceRecord schema for append-only audit records."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.action import Action, EnforcementMode
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence

Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class RecordType(StrEnum):
    """Append-only audit record type."""

    ACTION_EVALUATION = "action_evaluation"
    APPROVAL_DECISION = "approval_decision"


class EvidenceRecord(BaseModel):
    """Hash-chained audit record for an evaluation or human approval decision."""

    id: int = Field(..., description="Database row identifier for the audit record.")
    correlation_id: UUID = Field(..., description="Identifier linking workflow records.")
    action: Action = Field(..., description="Canonical action evaluated by policy.")
    context_used: Context = Field(..., description="Context supplied to policy evaluation.")
    evidence: Evidence = Field(..., description="Sensor evidence supplied to policy evaluation.")
    decision: Decision = Field(..., description="Binding PDP decision for the record.")
    enforcement_mode: EnforcementMode = Field(..., description="Enforcement mode active for the action.")
    executed: bool = Field(..., description="Whether the proposed action executed under enforcement.")
    record_type: RecordType = Field(..., description="Kind of append-only audit record.")
    references_hash: Sha256Hex | None = Field(..., description="Original record hash referenced by approvals.")
    human_approver: str | None = Field(..., description="Human approver for approval-decision rows.")
    approval_reason: str | None = Field(..., description="Human approval or rejection rationale.")
    created_at: datetime = Field(..., description="Timestamp at which the audit row was created.")
    record_hash: Sha256Hex = Field(..., description="SHA-256 hash of this record.")
    prev_hash: Sha256Hex = Field(..., description="SHA-256 hash of the previous record, or genesis zeroes.")
    evidence_schema_version: str = Field(..., description="Version of the EvidenceRecord schema at write time; shows that the definition of captured evidence is governed and versioned.")
