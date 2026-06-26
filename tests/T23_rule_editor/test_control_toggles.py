"""Acceptance tests for T23 per-control enable/disable behaviour.

Every test runs the real pipeline -> normaliser -> context resolver ->
(semantic layer if email) -> real OPA/Rego decision path. Nothing here
hand-rolls a decision or filters OPA's result in Python; disabling a
control must make Rego itself skip it via ``control_enabled()``.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _run_scenario_2(client: TestClient) -> dict:
    response = client.post("/run/2")
    assert response.status_code == 200
    return response.json()


def test_fin_pay_002_disabled_allows_scenario_2(wired_pipeline):
    client = TestClient(app)
    wired_pipeline.settings_store.update_control_enabled("FIN-PAY-002", False)

    payload = _run_scenario_2(client)

    assert payload["decision"]["decision"] == "allow"
    assert "FIN-PAY-002" not in payload["decision"]["triggered_controls"]
    assert payload["decision"]["required_approval_role"] is None


def test_fin_pay_002_reenabled_restores_scenario_2_escalation(wired_pipeline):
    client = TestClient(app)
    wired_pipeline.settings_store.update_control_enabled("FIN-PAY-002", False)
    disabled_payload = _run_scenario_2(client)
    assert disabled_payload["decision"]["decision"] == "allow"

    wired_pipeline.settings_store.update_control_enabled("FIN-PAY-002", True)
    payload = _run_scenario_2(client)

    assert payload["decision"]["decision"] == "escalate"
    assert payload["decision"]["control_id"] == "FIN-PAY-002"
    assert "FIN-PAY-002" in payload["decision"]["triggered_controls"]
    assert payload["decision"]["required_approval_role"] == "finance_supervisor"
    assert payload["decision"]["threshold_used"] == wired_pipeline.settings_store.read_settings().high_confidence_threshold


def test_disabled_email_control_is_skipped_by_opa(wired_pipeline):
    client = TestClient(app)
    wired_pipeline.settings_store.update_control_enabled("COMM-EMAIL-002", False)

    response = client.post("/run/5")
    assert response.status_code == 200
    payload = response.json()

    assert "COMM-EMAIL-002" not in payload["decision"]["triggered_controls"]
    assert payload["decision"]["decision"] != "escalate"


def test_settings_control_enabled_route_persists_and_takes_effect(wired_pipeline):
    client = TestClient(app)

    response = client.post(
        "/settings/control-enabled",
        data={"control_id": "FIN-PAY-002", "enabled": "false"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    settings = wired_pipeline.settings_store.read_settings()
    assert settings.control_enabled["FIN-PAY-002"] is False

    payload = _run_scenario_2(client)
    assert payload["decision"]["decision"] == "allow"
