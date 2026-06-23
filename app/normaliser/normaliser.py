"""Action normaliser for intercepted raw tool calls.

This module is deliberately limited to schema translation. It does not resolve
context, build evidence, call policy, enforce decisions, or write audit records.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.schemas.action import Action

DEFAULT_ENFORCEMENT_MODE = "shadow"

_TOOL_ACTION_TYPES = {
    "issue_payment": "financial.payment.issue",
    "send_email": "communication.email.send",
}


class UnsupportedToolError(ValueError):
    """Raised when a raw tool call uses a tool the normaliser cannot map."""


def _action_type_for_tool(tool_name: str) -> str:
    """Return the canonical action type for a supported raw tool name."""
    try:
        return _TOOL_ACTION_TYPES[tool_name]
    except KeyError as exc:
        supported = ", ".join(sorted(_TOOL_ACTION_TYPES))
        raise UnsupportedToolError(
            f"Unsupported tool_name '{tool_name}'. Supported tool names: {supported}."
        ) from exc


def normalise(raw_tool_call: dict[str, Any]) -> Action:
    """Convert one intercepted raw tool call into the canonical Action schema.

    The normaliser owns fresh UUIDv4 identifiers and the current timestamp.
    When a raw call omits ``enforcement_mode``, the narrow demo-safe default is
    ``shadow``; invalid supplied modes are left for the Action schema to reject.
    """
    tool_name = raw_tool_call.get("tool_name")
    if not isinstance(tool_name, str) or not tool_name:
        raise UnsupportedToolError("Raw tool call must include a non-empty tool_name.")

    parameters = deepcopy(raw_tool_call.get("parameters", {}))
    recipient = raw_tool_call.get("recipient") if tool_name == "send_email" else None
    content = parameters.get("body") if tool_name == "send_email" else None

    return Action(
        action_id=uuid4(),
        correlation_id=uuid4(),
        timestamp=datetime.now(UTC),
        action_type=_action_type_for_tool(tool_name),
        actor=deepcopy(raw_tool_call.get("actor")),
        tool=tool_name,
        target_system=raw_tool_call.get("target_system"),
        resource=deepcopy(raw_tool_call.get("resource")),
        parameters=parameters,
        content=content,
        recipient=recipient,
        environment="demo",
        enforcement_mode=raw_tool_call.get("enforcement_mode", DEFAULT_ENFORCEMENT_MODE),
    )
