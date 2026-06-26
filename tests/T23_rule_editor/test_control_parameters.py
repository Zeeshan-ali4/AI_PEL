"""Acceptance tests for T23's single runtime-editable control parameter:
FIN-PAY-002's payment amount threshold. Also guards the T19 confidence
threshold regression so the rule editor does not break the existing demo.

All decisions flow through the real pipeline + real OPA/Rego.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.settings_store import FIN_PAY_002_DEFAULT_AMOUNT_THRESHOLD


def _run_scenario_2(client: TestClient) -> dict:
    response = client.post("/run/2")
    assert response.status_code == 200
    return response.json()


def test_default_seed_config_preserves_existing_policy_behaviour(wired_pipeline):
    settings = wired_pipeline.settings_store.read_settings()

    assert settings.control_enabled["FIN-PAY-002"] is True
    assert settings.parameters["FIN-PAY-002"]["amount_threshold"] == FIN_PAY_002_DEFAULT_AMOUNT_THRESHOLD == 500
    assert settings.high_confidence_threshold == 0.75

    client = TestClient(app)
    payload = _run_scenario_2(client)
    assert payload["decision"]["decision"] == "escalate"
    assert payload["decision"]["required_approval_role"] == "finance_supervisor"


def test_fin_pay_002_threshold_1000_allows_scenario_2(wired_pipeline):
    client = TestClient(app)
    wired_pipeline.settings_store.update_control_parameter("FIN-PAY-002", "amount_threshold", 1000)

    payload = _run_scenario_2(client)

    assert payload["decision"]["decision"] == "allow"
    assert "FIN-PAY-002" not in payload["decision"]["triggered_controls"]


def test_fin_pay_002_threshold_500_restores_escalation(wired_pipeline):
    client = TestClient(app)
    wired_pipeline.settings_store.update_control_parameter("FIN-PAY-002", "amount_threshold", 1000)
    raised_payload = _run_scenario_2(client)
    assert raised_payload["decision"]["decision"] == "allow"

    wired_pipeline.settings_store.update_control_parameter("FIN-PAY-002", "amount_threshold", 500)
    payload = _run_scenario_2(client)

    assert payload["decision"]["decision"] == "escalate"
    assert payload["decision"]["control_id"] == "FIN-PAY-002"
    assert "FIN-PAY-002" in payload["decision"]["triggered_controls"]
    assert payload["decision"]["required_approval_role"] == "finance_supervisor"


def test_settings_control_parameter_route_persists_and_takes_effect(wired_pipeline):
    client = TestClient(app)

    response = client.post(
        "/settings/control-parameter",
        data={"control_id": "FIN-PAY-002", "amount_threshold": "1000"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    settings = wired_pipeline.settings_store.read_settings()
    assert settings.parameters["FIN-PAY-002"]["amount_threshold"] == 1000.0

    payload = _run_scenario_2(client)
    assert payload["decision"]["decision"] == "allow"


def test_t19_confidence_threshold_behaviour_still_works(wired_pipeline):
    client = TestClient(app)
    settings = wired_pipeline.settings_store.read_settings()
    assert settings.high_confidence_threshold == 0.75

    response = client.post("/run/5")
    payload = response.json()
    assert payload["decision"]["decision"] == "escalate"
    assert payload["decision"]["control_id"] == "COMM-EMAIL-002"
    assert payload["decision"]["required_approval_role"] == "vulnerable_customer_team"
    assert payload["decision"]["threshold_used"] == 0.75

    wired_pipeline.settings_store.update_threshold(0.60)
    response = client.post("/run/5")
    payload = response.json()
    assert payload["decision"]["decision"] == "allow_with_logging"
    assert payload["decision"]["threshold_used"] == 0.60
