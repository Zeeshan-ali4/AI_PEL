"""Tests for the OPA HTTP round-trip (requires live OPA or is skipped)."""

import uuid
from datetime import datetime, timezone

import httpx
import pytest

from app.policy.opa_client import _build_input, decide
from app.schemas.action import Action
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence

OPA_URL = "http://localhost:8181"


def _opa_available() -> bool:
    try:
        r = httpx.get(f"{OPA_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


requires_opa = pytest.mark.skipif(not _opa_available(), reason="OPA not running on localhost:8181")


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
    return {"high_confidence_threshold": 0.75, "control_modes": {"FIN-PAY-001": "shadow"}}


@requires_opa
def test_roundtrip_allow_decision():
    result = decide(
        _sample_action(), _sample_context(), _sample_evidence(), _sample_config(),
        opa_url=OPA_URL,
    )
    assert isinstance(result, Decision)
    assert result.decision == "allow"


@requires_opa
def test_decision_schema_fields_complete():
    result = decide(
        _sample_action(), _sample_context(), _sample_evidence(), _sample_config(),
        opa_url=OPA_URL,
    )
    assert result.decision is not None
    assert result.triggered_controls is not None
    assert result.reason is not None
    assert result.framework_mappings is not None
    assert result.failure_mode is not None
    assert result.logging_requirements is not None
    assert result.policy_version is not None
    assert result.threshold_used is not None


def test_opa_input_contract_shape():
    action = _sample_action()
    context = _sample_context()
    evidence = _sample_evidence()
    config = _sample_config()
    payload = _build_input(action, context, evidence, config)
    assert "input" in payload
    inp = payload["input"]
    assert set(inp.keys()) == {"action", "context", "evidence", "config"}
    assert "high_confidence_threshold" in inp["config"]
