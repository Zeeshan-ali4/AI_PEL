"""OPA HTTP client for the policy decision point.

Sends an input document to OPA and parses the response into a Decision model.

OPA input contract (stable — T10+ depends on this shape):

    POST {OPA_URL}/v1/data/policy/gate/decision

    {
        "input": {
            "action": { ... Action.model_dump(mode="json") ... },
            "context": { ... Context.model_dump(mode="json") ... },
            "evidence": { ... Evidence.model_dump(mode="json") ... },
            "config": {
                "high_confidence_threshold": <float>,
                "control_modes": { "<control_id>": "<mode>", ... }
            }
        }
    }

Response (success):

    { "result": { ... Decision fields ... } }

On OPA unreachable / non-2xx → returns Decision(decision="fail_closed").
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.schemas.action import Action
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence

OPA_TIMEOUT_SECONDS = 5.0
OPA_POLICY_PATH = "/v1/data/policy/gate/decision"

FAIL_CLOSED_FRAMEWORK_MAPPINGS = [
    "Internal AI Governance Policy (safe-default)",
    "ISO/IEC 42001 (robustness)",
]


def _build_input(
    action: Action,
    context: Context,
    evidence: Evidence,
    config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "input": {
            "action": action.model_dump(mode="json"),
            "context": context.model_dump(mode="json"),
            "evidence": evidence.model_dump(mode="json"),
            "config": config,
        }
    }


def _fail_closed_decision(threshold: float, reason: str = "OPA unreachable") -> Decision:
    return Decision(
        decision="fail_closed",
        control_id=None,
        triggered_controls=[],
        reason=reason,
        required_approval_role=None,
        framework_mappings=list(FAIL_CLOSED_FRAMEWORK_MAPPINGS),
        failure_mode="fail_closed",
        logging_requirements="enhanced",
        policy_version="unknown",
        threshold_used=threshold,
    )


def decide(
    action: Action,
    context: Context,
    evidence: Evidence,
    config: dict[str, Any],
    *,
    opa_url: str | None = None,
) -> Decision:
    """Query OPA for a policy decision.

    Args:
        action: Normalised action.
        context: Resolved context.
        evidence: Assembled evidence (may be unevaluated for payments).
        config: Policy config dict from RuntimeSettings.to_policy_config().
        opa_url: Override OPA base URL (for testing). Defaults to app config.

    Returns:
        A Decision model — either from OPA or a fail_closed fallback.
    """
    if opa_url is None:
        opa_url = get_settings().opa_url

    threshold = config.get("high_confidence_threshold", 0.75)
    payload = _build_input(action, context, evidence, config)
    url = f"{opa_url}{OPA_POLICY_PATH}"

    try:
        response = httpx.post(url, json=payload, timeout=OPA_TIMEOUT_SECONDS)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError):
        return _fail_closed_decision(threshold)

    if response.status_code != 200:
        return _fail_closed_decision(threshold, reason=f"OPA returned HTTP {response.status_code}")

    try:
        result = response.json().get("result")
        if result is None:
            return _fail_closed_decision(threshold, reason="OPA returned no result")
        return Decision(**result)
    except Exception:
        return _fail_closed_decision(threshold, reason="Failed to parse OPA response")
