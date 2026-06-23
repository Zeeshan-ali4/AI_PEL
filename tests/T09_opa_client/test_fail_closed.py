"""Tests for fail-closed behaviour when OPA is unreachable."""

import uuid
from datetime import datetime, timezone

from app.policy.opa_client import decide
from app.schemas.action import Action
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence


def _sample_action() -> Action:
    return Action(
        action_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        action_type="financial.payment.issue",
        actor={"agent_id": "agent-1", "agent_owner": "ops", "role": "clerk"},
        tool="payment_tool",
        target_system="payment_system",
        resource={"type": "customer", "id": "CUST-100"},
        parameters={"amount_gbp": 80},
        content=None,
        recipient=None,
        environment="demo",
        enforcement_mode="shadow",
    )


def _sample_context() -> Context:
    return Context(
        customer={"id": "CUST-100", "status": "normal", "vulnerability_flag": False, "fraud_flag": False, "sanctions_match": False, "account_age_days": 365},
        payment_history={"count_30d": 1, "total_30d_gbp": 80, "last_payment_date": None},
        approval_state={"has_approval": False, "approver": None, "approval_id": None},
        recipient={"is_external": False, "domain": None, "approved_disclosure_basis": False},
        affects_individual_financial_standing=True,
        business_hours=True,
        context_resolution_ok=True,
    )


def _sample_evidence() -> Evidence:
    return Evidence(
        evaluated=False,
        contains_personal_data=False,
        contains_special_category_data=False,
        sensitivity_level="low",
        detected_entities=[],
        evidence_spans=[],
        vulnerability_indicators={"present": False, "confidence": 0.0, "categories": [], "source": "nuance_stub"},
        overall_confidence=0.0,
        sensor_versions={"presidio": "2.2.355", "nuance_stub": "stub-0.1"},
        sensor_error=False,
    )


def _sample_config() -> dict:
    return {"high_confidence_threshold": 0.75, "control_modes": {}}


DEAD_OPA_URL = "http://localhost:19999"


def test_opa_unreachable_fail_closed():
    result = decide(
        _sample_action(), _sample_context(), _sample_evidence(), _sample_config(),
        opa_url=DEAD_OPA_URL,
    )
    assert isinstance(result, Decision)
    assert result.decision == "fail_closed"
    assert result.failure_mode == "fail_closed"


def test_fail_closed_decision_fields():
    result = decide(
        _sample_action(), _sample_context(), _sample_evidence(), _sample_config(),
        opa_url=DEAD_OPA_URL,
    )
    assert "unreachable" in result.reason.lower() or "connect" in result.reason.lower()
    assert result.logging_requirements == "enhanced"
    assert "Internal AI Governance Policy (safe-default)" in result.framework_mappings
    assert "ISO/IEC 42001 (robustness)" in result.framework_mappings
    assert result.policy_version == "unknown"
    assert result.threshold_used == 0.75


def test_opa_non_2xx_fail_closed():
    """POST to OPA at a nonsense path → empty result → fail_closed."""
    import httpx
    try:
        r = httpx.get("http://localhost:8181/health", timeout=2)
        opa_up = r.status_code == 200
    except Exception:
        opa_up = False

    if not opa_up:
        result = decide(
            _sample_action(), _sample_context(), _sample_evidence(), _sample_config(),
            opa_url=DEAD_OPA_URL,
        )
    else:
        from unittest.mock import patch
        from app.policy import opa_client
        original_path = opa_client.OPA_POLICY_PATH
        opa_client.OPA_POLICY_PATH = "/v1/data/nonexistent/path"
        try:
            result = decide(
                _sample_action(), _sample_context(), _sample_evidence(), _sample_config(),
                opa_url="http://localhost:8181",
            )
        finally:
            opa_client.OPA_POLICY_PATH = original_path

    assert result.decision == "fail_closed"
