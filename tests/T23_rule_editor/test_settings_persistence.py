"""Acceptance tests for T23 settings persistence: page rendering, refresh,
and store-reinitialisation (an in-process stand-in for an app restart).
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.settings_store import SettingsStore

_CONTROLS_PATH = Path(__file__).resolve().parents[2] / "opa" / "data" / "controls.json"


def _control_ids() -> list[str]:
    payload = json.loads(_CONTROLS_PATH.read_text())
    return list(payload["controls"].keys())


def test_all_controls_have_persisted_enabled_flags_and_ui_rows(wired_pipeline):
    settings = wired_pipeline.settings_store.read_settings()
    for control_id in _control_ids():
        assert control_id in settings.control_enabled
        assert settings.control_enabled[control_id] is True

    client = TestClient(app)
    page = client.get("/settings").text
    for control_id in _control_ids():
        assert control_id in page
    assert "amount-threshold-input" in page
    assert "High-confidence threshold" in page


def test_settings_page_save_persists_control_toggle_and_parameter_after_refresh(wired_pipeline):
    client = TestClient(app)

    client.post(
        "/settings/control-enabled",
        data={"control_id": "FIN-PAY-002", "enabled": "false"},
        follow_redirects=True,
    )
    client.post(
        "/settings/control-parameter",
        data={"control_id": "FIN-PAY-002", "amount_threshold": "1000"},
        follow_redirects=True,
    )

    settings = wired_pipeline.settings_store.read_settings()
    assert settings.control_enabled["FIN-PAY-002"] is False
    assert settings.parameters["FIN-PAY-002"]["amount_threshold"] == 1000.0

    refreshed_page = client.get("/settings").text
    assert "Disabled" in refreshed_page

    response = client.post("/run/2")
    assert response.json()["decision"]["decision"] == "allow"


def test_control_settings_survive_store_reinitialisation(wired_pipeline, tmp_path):
    wired_pipeline.settings_store.update_control_enabled("FIN-PAY-002", False)
    wired_pipeline.settings_store.update_control_parameter("FIN-PAY-002", "amount_threshold", 1000)

    database_url = wired_pipeline.settings_store.database_url
    reinitialised_store = SettingsStore(database_url)

    reloaded = reinitialised_store.read_settings()
    assert reloaded.control_enabled["FIN-PAY-002"] is False
    assert reloaded.parameters["FIN-PAY-002"]["amount_threshold"] == 1000

    wired_pipeline.settings_store = reinitialised_store
    client = TestClient(app)
    response = client.post("/run/2")
    assert response.json()["decision"]["decision"] == "allow"


def test_settings_confirmation_mentions_next_evaluation(wired_pipeline):
    client = TestClient(app)

    response = client.post(
        "/settings/control-enabled",
        data={"control_id": "FIN-PAY-002", "enabled": "false"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "next evaluation" in response.text.lower()
