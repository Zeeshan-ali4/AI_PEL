"""T10 acceptance tests for the six policy scenarios using real OPA evaluation."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.schemas.decision import Decision

REPO_ROOT = Path(__file__).resolve().parents[2]
OPA = shutil.which("opa")

pytestmark = pytest.mark.skipif(OPA is None, reason="OPA CLI is not installed")


def evaluate(input_doc: dict) -> Decision:
    process = subprocess.run(
        [
            OPA,
            "eval",
            "--format",
            "json",
            "--data",
            str(REPO_ROOT / "opa" / "policies"),
            "--data",
            str(REPO_ROOT / "opa" / "data" / "controls.json"),
            "--stdin-input",
            "data.policy.gate.decision",
        ],
        input=json.dumps(input_doc),
        text=True,
        capture_output=True,
        check=True,
    )
    value = json.loads(process.stdout)["result"][0]["expressions"][0]["value"]
    return Decision(**value)


def base_action(action_type: str, *, amount: int | None = None) -> dict:
    parameters = {"amount_gbp": amount} if amount is not None else {}
    return {
        "action_type": action_type,
        "parameters": parameters,
        "recipient": "external@example.org" if action_type == "communication.email.send" else None,
    }


def base_context(*, external: bool = False, disclosure_basis: bool = False) -> dict:
    return {
        "customer": {
            "id": "CUST-100",
            "status": "normal",
            "vulnerability_flag": False,
            "fraud_flag": False,
            "sanctions_match": False,
            "account_age_days": 365,
        },
        "payment_history": {"count_30d": 1, "total_30d_gbp": 80, "last_payment_date": None},
        "approval_state": {"has_approval": False, "approver": None, "approval_id": None},
        "recipient": {
            "is_external": external,
            "domain": "example.org" if external else None,
            "approved_disclosure_basis": disclosure_basis,
        },
        "affects_individual_financial_standing": True,
        "business_hours": True,
        "context_resolution_ok": True,
    }


def evidence(
    *,
    evaluated: bool,
    personal: bool = False,
    special: bool = False,
    vulnerability: bool = False,
    confidence: float = 0.0,
    sensor_error: bool = False,
) -> dict:
    return {
        "evaluated": evaluated,
        "contains_personal_data": personal,
        "contains_special_category_data": special,
        "sensitivity_level": "high" if special else "medium" if personal or vulnerability else "low",
        "detected_entities": [{"type": "PERSON", "score": 0.85, "source": "presidio"}] if personal else [],
        "evidence_spans": [{"start": 0, "end": 5, "label": "PERSON"}] if personal else [],
        "vulnerability_indicators": {
            "present": vulnerability,
            "confidence": confidence if vulnerability else 0.0,
            "categories": ["financial_vulnerability"] if vulnerability else [],
            "source": "nuance_stub",
        },
        "overall_confidence": confidence,
        "sensor_versions": {"presidio": "test", "nuance_stub": "stub-0.1"},
        "sensor_error": sensor_error,
    }


def payload(action: dict, context: dict, ev: dict, threshold: float = 0.75) -> dict:
    return {
        "action": action,
        "context": context,
        "evidence": ev,
        "config": {"high_confidence_threshold": threshold, "control_modes": {}},
    }


def test_scenario_1_clean_payment_allows():
    result = evaluate(payload(base_action("financial.payment.issue", amount=80), base_context(), evidence(evaluated=False)))
    assert result.decision == "allow"
    assert result.control_id is None
    assert result.triggered_controls == []
    assert result.required_approval_role is None
    assert result.logging_requirements == "standard"
    assert result.threshold_used == 0.75


def test_scenario_2_large_payment_without_approval_escalates_to_finance_supervisor():
    result = evaluate(payload(base_action("financial.payment.issue", amount=850), base_context(), evidence(evaluated=False)))
    assert result.decision == "escalate"
    assert result.control_id == "FIN-PAY-002"
    assert "FIN-PAY-002" in result.triggered_controls
    assert result.required_approval_role == "finance_supervisor"
    assert result.framework_mappings
    assert result.failure_mode == "fail_closed"


def test_scenario_3_fraud_flagged_payment_blocks():
    context = base_context()
    context["customer"]["fraud_flag"] = True
    result = evaluate(payload(base_action("financial.payment.issue", amount=200), context, evidence(evaluated=False)))
    assert result.decision == "block"
    assert result.control_id == "FIN-PAY-001"
    assert "FIN-PAY-001" in result.triggered_controls
    assert result.required_approval_role is None
    assert result.framework_mappings


def test_scenario_4_external_special_category_email_escalates_to_data_protection():
    result = evaluate(
        payload(
            base_action("communication.email.send"),
            base_context(external=True, disclosure_basis=False),
            evidence(evaluated=True, personal=True, special=True, vulnerability=True, confidence=0.88),
        )
    )
    assert result.decision == "escalate"
    assert result.control_id == "COMM-EMAIL-001"
    assert "COMM-EMAIL-001" in result.triggered_controls
    assert result.required_approval_role == "data_protection_approver"
    assert result.framework_mappings


def test_scenario_5_uncertain_vulnerability_email_escalates_at_default_threshold():
    result = evaluate(
        payload(
            base_action("communication.email.send"),
            base_context(external=True, disclosure_basis=True),
            evidence(evaluated=True, personal=True, vulnerability=True, confidence=0.62),
            threshold=0.75,
        )
    )
    assert result.decision == "escalate"
    assert result.control_id == "COMM-EMAIL-002"
    assert "COMM-EMAIL-002" in result.triggered_controls
    assert result.required_approval_role == "vulnerable_customer_team"
    assert result.threshold_used == 0.75


def test_scenario_5_threshold_060_flips_to_allow_with_logging():
    result = evaluate(
        payload(
            base_action("communication.email.send"),
            base_context(external=True, disclosure_basis=True),
            evidence(evaluated=True, personal=True, vulnerability=True, confidence=0.62),
            threshold=0.60,
        )
    )
    assert result.decision == "allow_with_logging"
    assert result.control_id == "COMM-EMAIL-003"
    assert "COMM-EMAIL-002" not in result.triggered_controls
    assert result.logging_requirements == "enhanced"
    assert result.threshold_used == 0.60


def test_scenario_6_partner_email_with_personal_data_allows_with_logging():
    result = evaluate(
        payload(
            base_action("communication.email.send"),
            base_context(external=True, disclosure_basis=True),
            evidence(evaluated=True, personal=True, special=False, vulnerability=False, confidence=0.85),
        )
    )
    assert result.decision == "allow_with_logging"
    assert result.control_id == "COMM-EMAIL-003"
    assert result.triggered_controls == ["COMM-EMAIL-003"]
    assert result.required_approval_role is None
    assert result.logging_requirements == "enhanced"
    assert result.framework_mappings
