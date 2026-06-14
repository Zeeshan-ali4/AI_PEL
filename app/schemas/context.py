"""Canonical Context schema resolved from enterprise-system fixtures."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class CustomerStatus(StrEnum):
    """Closed set of customer account states relevant to policy."""

    NORMAL = "normal"
    FLAGGED = "flagged"
    BLOCKED = "blocked"


class CustomerContext(BaseModel):
    """Customer risk and vulnerability context used by policy."""

    id: str = Field(..., description="Customer identifier from the source system.")
    status: CustomerStatus = Field(..., description="Current customer account status.")
    vulnerability_flag: bool = Field(..., description="Whether known vulnerability support is flagged.")
    fraud_flag: bool = Field(..., description="Whether fraud monitoring has flagged the customer.")
    sanctions_match: bool = Field(..., description="Whether sanctions screening matched the customer.")
    account_age_days: int = Field(..., description="Age of the customer account in days.")


class PaymentHistory(BaseModel):
    """Recent payment activity for payment-risk controls."""

    count_30d: int = Field(..., description="Number of payments in the last 30 days.")
    total_30d_gbp: float = Field(..., description="Total payment amount in GBP over the last 30 days.")
    last_payment_date: date | None = Field(..., description="Most recent payment date, if one exists.")


class ApprovalState(BaseModel):
    """Existing human approval state available before policy evaluation."""

    has_approval: bool = Field(..., description="Whether a valid prior approval exists.")
    approver: str | None = Field(..., description="Name or role of the approver, if approved.")
    approval_id: str | None = Field(..., description="Identifier of the prior approval, if approved.")


class RecipientContext(BaseModel):
    """Recipient metadata used for communication controls."""

    is_external: bool = Field(..., description="Whether the recipient is outside the organisation.")
    domain: str | None = Field(..., description="Recipient email domain, when known.")
    approved_disclosure_basis: bool = Field(..., description="Whether an approved disclosure basis exists.")


class Context(BaseModel):
    """Policy context resolved for a proposed action."""

    customer: CustomerContext = Field(..., description="Customer risk and account context.")
    payment_history: PaymentHistory = Field(..., description="Recent payment history.")
    approval_state: ApprovalState = Field(..., description="Available human approval state.")
    recipient: RecipientContext = Field(..., description="Recipient disclosure context.")
    affects_individual_financial_standing: bool = Field(..., description="Whether the action affects financial standing.")
    business_hours: bool = Field(..., description="Whether the action is proposed during business hours.")
    context_resolution_ok: bool = Field(..., description="False when required context could not be resolved.")
