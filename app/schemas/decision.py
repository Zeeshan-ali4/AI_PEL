"""Canonical Decision schema returned by the policy decision point."""

from enum import StrEnum

from pydantic import BaseModel, Field


class DecisionValue(StrEnum):
    """Binding PDP decision values in the policy contract."""

    ALLOW = "allow"
    BLOCK = "block"
    ESCALATE = "escalate"
    MODIFY = "modify"
    ALLOW_WITH_LOGGING = "allow_with_logging"
    REQUIRE_EVIDENCE = "require_evidence"
    FAIL_CLOSED = "fail_closed"


class FailureMode(StrEnum):
    """Failure posture reported by the PDP."""

    FAIL_CLOSED = "fail_closed"
    FAIL_OPEN = "fail_open"


class LoggingRequirements(StrEnum):
    """Audit logging level required for the decision."""

    STANDARD = "standard"
    ENHANCED = "enhanced"


class Decision(BaseModel):
    """Binding policy decision made by OPA/PDP, not by evidence sensors."""

    decision: DecisionValue = Field(..., description="Binding policy decision.")
    control_id: str | None = Field(..., description="Primary triggered control, if any.")
    triggered_controls: list[str] = Field(..., description="All controls triggered during evaluation.")
    reason: str = Field(..., description="Human-readable explanation from policy.")
    required_approval_role: str | None = Field(..., description="Named approval role required for escalation.")
    framework_mappings: list[str] = Field(..., description="Framework or assurance mappings for triggered controls.")
    failure_mode: FailureMode = Field(..., description="Failure posture represented by the decision.")
    logging_requirements: LoggingRequirements = Field(..., description="Required audit logging level.")
    policy_version: str = Field(..., description="Policy bundle or version identifier.")
    threshold_used: float = Field(..., ge=0, le=1, description="Configurable high-confidence threshold used by policy.")
