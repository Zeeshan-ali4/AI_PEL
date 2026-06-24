"""Acceptance tests for the T19 Settings page.

Exercises the real settings store + pipeline + real OPA path (spec §6, §8,
§8A item 7, §12). No decision logic is hand-rolled in these tests; the
live impact panel and Scenario 5 flip are verified through the real routes.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_settings_page_renders_current_threshold_and_control_modes(wired_pipeline):
    client = TestClient(app)
    settings = wired_pipeline.settings_store.read_settings()

    response = client.get("/settings")
    assert response.status_code == 200
    page = response.text

    assert str(settings.high_confidence_threshold) in page
    for control_id, mode in settings.control_modes.items():
        assert control_id in page
    assert "shadow" in page.lower()
    assert "full" in page.lower()


def test_update_threshold_persists_and_takes_effect_without_restart(wired_pipeline):
    client = TestClient(app)

    response = client.post("/settings/threshold", data={"threshold": "0.60"}, follow_redirects=True)
    assert response.status_code == 200

    settings = wired_pipeline.settings_store.read_settings()
    assert settings.high_confidence_threshold == 0.60

    run_response = client.post("/run/5")
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["decision"]["decision"] == "allow_with_logging"
    assert payload["decision"]["threshold_used"] == 0.60


def test_update_control_mode_persists_and_reflects_on_reload(wired_pipeline):
    client = TestClient(app)

    response = client.post(
        "/settings/control-mode",
        data={"control_id": "FIN-PAY-001", "mode": "full"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    settings = wired_pipeline.settings_store.read_settings()
    assert settings.control_modes["FIN-PAY-001"] == "full"

    page = client.get("/settings").text
    assert "FIN-PAY-001" in page


def test_impact_panel_reflects_accurate_scenario_5_outcomes_at_both_thresholds(wired_pipeline):
    client = TestClient(app)
    settings = wired_pipeline.settings_store.read_settings()
    assert settings.high_confidence_threshold == 0.75

    response = client.get("/settings", params={"preview_threshold": "0.60"})
    assert response.status_code == 200
    page = response.text.lower()

    assert "escalate" in page
    assert "allow, with logging" in page or "allow_with_logging" in page
    assert "0.6" in page


def test_invalid_threshold_is_rejected_with_no_silent_acceptance(wired_pipeline):
    client = TestClient(app)
    original = wired_pipeline.settings_store.read_settings().high_confidence_threshold

    response = client.post("/settings/threshold", data={"threshold": "1.5"}, follow_redirects=True)
    assert response.status_code == 200

    settings = wired_pipeline.settings_store.read_settings()
    assert settings.high_confidence_threshold == original
    assert "between 0 and 1" in response.text.lower() or "must be between" in response.text.lower()
