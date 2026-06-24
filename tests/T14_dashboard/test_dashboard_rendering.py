"""Acceptance tests for the rendered T14 landing dashboard page."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

CONTROLS_PATH = Path(__file__).resolve().parents[2] / "opa" / "data" / "controls.json"

ENABLED_CONTROL_IDS = {
    "FIN-PAY-001",
    "FIN-PAY-002",
    "FIN-PAY-003",
    "FIN-PAY-004",
    "COMM-EMAIL-001",
    "COMM-EMAIL-002",
    "COMM-EMAIL-003",
}


def test_landing_page_renders_shared_dashboard_layout(wired_pipeline):
    response = TestClient(app).get("/")

    assert response.status_code == 200
    html = response.text
    assert "Control dashboard" in html
    assert "AI PEL Assurance Gate" in html  # shared base.html header
    assert "Controls" in html
    assert "Enforcement mode" in html
    assert "Auditable surface" in html


def test_dashboard_lists_every_enabled_control_from_controls_json(wired_pipeline):
    controls = json.loads(CONTROLS_PATH.read_text())["controls"]
    enabled_ids = {control_id for control_id, control in controls.items() if control.get("enabled")}
    assert enabled_ids == ENABLED_CONTROL_IDS

    html = TestClient(app).get("/").text

    for control_id in enabled_ids:
        assert control_id in html
        assert controls[control_id]["description"] in html


def test_dashboard_renders_tiers_as_plain_english_board_labels(wired_pipeline):
    html = TestClient(app).get("/").text

    assert "Prohibited" in html
    assert "Escalate" in html
    assert "Log" in html
    # Raw internal tier slugs should not be the only thing shown.
    assert "allow_with_logging" not in html


def test_dashboard_framework_chips_match_control_metadata(wired_pipeline):
    html = TestClient(app).get("/").text

    assert "Internal Fraud &amp; Financial Crime Policy" in html or "Internal Fraud & Financial Crime Policy" in html
    assert "Internal Delegated-Authority Policy" in html
    assert "UK GDPR Art.9 / DPA 2018" in html
    assert "UK GDPR Art.5(2) accountability" in html
    assert "Record-keeping control RK-03" in html
