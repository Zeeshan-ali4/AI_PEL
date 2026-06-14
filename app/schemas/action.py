"""Canonical Action schema produced by the action normaliser."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ActionType(StrEnum):
    """Tool-independent action types governed by the policy gate."""

    FINANCIAL_PAYMENT_ISSUE = "financial.payment.issue"
    COMMUNICATION_EMAIL_SEND = "communication.email.send"


class Environment(StrEnum):
    """Runtime environment in which the proposed action was raised."""

    DEMO = "demo"
    SANDBOX = "sandbox"
    PROD = "prod"


class EnforcementMode(StrEnum):
    """How strongly the gate should enforce the policy decision."""

    SHADOW = "shadow"
    SOFT = "soft"
    FULL = "full"


class Actor(BaseModel):
    """Agent identity and owning business role for an action."""

    agent_id: str = Field(..., description="Unique identifier for the proposing agent.")
    agent_owner: str = Field(..., description="Person or team accountable for the agent.")
    role: str = Field(..., description="Business role under which the agent is acting.")


class Resource(BaseModel):
    """Target business object the proposed action would affect."""

    type: str = Field(..., description="Resource type, such as customer or account.")
    id: str = Field(..., description="Identifier of the target resource.")


class Action(BaseModel):
    """Canonical proposed action intercepted before execution."""

    action_id: UUID = Field(..., description="Unique identifier for this proposed action.")
    correlation_id: UUID = Field(..., description="Identifier linking all records for one workflow.")
    timestamp: datetime = Field(..., description="ISO-8601 time at which the action was proposed.")
    action_type: ActionType = Field(..., description="Canonical action type governed by policy.")
    actor: Actor = Field(..., description="Agent identity and accountable owner.")
    tool: str = Field(..., description="Original tool or integration requested by the agent.")
    target_system: str = Field(..., description="Business system the tool would call.")
    resource: Resource = Field(..., description="Business resource targeted by the action.")
    parameters: dict[str, Any] = Field(..., description="Action-specific parameters supplied to the tool.")
    content: str | None = Field(..., description="Unstructured message content, when applicable.")
    recipient: str | None = Field(..., description="Message recipient, when applicable.")
    environment: Environment = Field(..., description="Environment where the action would run.")
    enforcement_mode: EnforcementMode = Field(..., description="Configured enforcement mode for this action.")
