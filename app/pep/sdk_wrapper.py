"""SDK wrapper Policy Enforcement Point for T03.

The wrapper intercepts raw agent tool calls before any business execution. The
real downstream pipeline is implemented later; this task only echoes the raw
call after making interception visible.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

INTERCEPTION_MESSAGE = "intercepted before execution"


def placeholder_policy_pipeline(raw_tool_call: dict[str, Any]) -> dict[str, Any]:
    """Temporary T03 pipeline placeholder that echoes the intercepted call.

    This function is intentionally not a policy decision point. It must not add
    decisions, approvals, audit records, execution results, or sensor evidence.
    """
    return deepcopy(raw_tool_call)


class SDKWrapper:
    """Minimal SDK wrapper proving the PEP interception point."""

    def call_tool(self, raw_tool_call: dict[str, Any]) -> dict[str, Any]:
        print(f"{INTERCEPTION_MESSAGE}: {raw_tool_call.get('scenario_id', 'unknown')}")
        return placeholder_policy_pipeline(raw_tool_call)
