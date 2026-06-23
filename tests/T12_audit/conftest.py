"""Shared fixtures for T12 audit store tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.audit.store import AuditStore
from app.schemas.action import Action
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence


def sample_action(correlation_id: uuid.UUID | None = None) -> Action:
    return Action(
        action_id=uuid.uuid4(),
        correlation_id=correlation_id or uuid.uuid4(),
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


def sample_context() -> Context:
    return Context(
        customer={
            "id": "CUST-100",
            "status": "normal",
            "vulnerability_flag": False,
            "fraud_flag": False,
            "sanctions_match": False,
            "account_age_days": 365,
        },
        payment_history={"count_30d": 1, "total_30d_gbp": 80, "last_payment_date": None},
        approval_state={"has_approval": False, "approver": None, "approval_id": None},
        recipient={"is_external": False, "domain": None, "approved_disclosure_basis": False},
        affects_individual_financial_standing=True,
        business_hours=True,
        context_resolution_ok=True,
    )


def sample_evidence() -> Evidence:
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


def sample_decision(decision: str = "allow", control_id: str | None = None) -> Decision:
    return Decision(
        decision=decision,
        control_id=control_id,
        triggered_controls=[control_id] if control_id else [],
        reason="sample reason",
        required_approval_role=None,
        framework_mappings=[],
        failure_mode="fail_closed",
        logging_requirements="standard",
        policy_version="v1",
        threshold_used=0.75,
    )


@pytest.fixture
def store(tmp_path):
    return AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
