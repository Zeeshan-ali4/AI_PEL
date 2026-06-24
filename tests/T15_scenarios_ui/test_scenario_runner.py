"""Acceptance tests for the T15 scenario runner page (spec §8A item 2)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

EXPECTED_TITLES = {
    1: "Payment £80 for clean customer",
    2: "Payment £850 without pre-existing approval",
    3: "Payment £200 for customer with active fraud flag",
    4: "External email with special-category and vulnerability content",
    5: "External email with uncertain vulnerability indicator",
    6: "External email to known partner with customer name only",
}


def test_scenario_runner_renders_six_canonical_cards():
    response = TestClient(app).get("/scenarios")

    assert response.status_code == 200
    html = response.text
    for number, title in EXPECTED_TITLES.items():
        assert title in html
        assert f"/scenarios/{number}/run" in html
        assert f"Run scenario {number}" in html


def test_scenario_runner_uses_calm_assurance_copy_not_debug_copy():
    html = TestClient(app).get("/scenarios").text

    assert "Scenario runner" in html
    assert "intercepts a" in html or "evaluates it through real context" in html
    # No raw Python object reprs or unformatted JSON dumps as primary content.
    assert "object at 0x" not in html
    assert '{"id"' not in html
