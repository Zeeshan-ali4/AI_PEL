"""Enforcement-mode toggle persistence tests for the T14 dashboard."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_displays_current_modes_from_settings_store(wired_pipeline):
    wired_pipeline.settings_store.update_control_modes(
        {
            "FIN-PAY-001": "full",
            "FIN-PAY-002": "soft",
            "FIN-PAY-003": "shadow",
            "FIN-PAY-004": "shadow",
            "COMM-EMAIL-001": "shadow",
            "COMM-EMAIL-002": "shadow",
            "COMM-EMAIL-003": "shadow",
        }
    )

    html = TestClient(app).get("/").text

    rows = html.split("<tr>")
    fin_001_row = next(row for row in rows if "FIN-PAY-001" in row)
    fin_002_row = next(row for row in rows if "FIN-PAY-002" in row)
    email_003_row = next(row for row in rows if "COMM-EMAIL-003" in row)

    assert "full" in fin_001_row
    assert "soft" in fin_002_row
    assert "shadow" in email_003_row


def test_dashboard_enforcement_mode_toggle_persists_selected_mode(wired_pipeline):
    client = TestClient(app)

    response = client.post("/mode", data={"mode": "full"}, follow_redirects=False)

    assert response.status_code == 303
    persisted = wired_pipeline.settings_store.read_settings()
    assert set(persisted.control_modes.values()) == {"full"}

    html = client.get("/").text
    assert "full" in html


def test_dashboard_rejects_invalid_enforcement_mode_submission(wired_pipeline):
    client = TestClient(app)
    before = wired_pipeline.settings_store.read_settings()

    response = client.post("/mode", data={"mode": "observe"}, follow_redirects=False)

    assert 400 <= response.status_code < 500
    after = wired_pipeline.settings_store.read_settings()
    assert after.control_modes == before.control_modes
