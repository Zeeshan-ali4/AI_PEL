"""Tests for opa/data/controls.json structure and content."""

import json
from pathlib import Path

import pytest

CONTROLS_PATH = Path(__file__).resolve().parents[2] / "opa" / "data" / "controls.json"

EXPECTED_IDS = {
    "FIN-PAY-001", "FIN-PAY-002", "FIN-PAY-003", "FIN-PAY-004",
    "COMM-EMAIL-001", "COMM-EMAIL-002", "COMM-EMAIL-003",
}

REQUIRED_FIELDS = {"id", "tier", "decision", "description", "framework_mappings", "required_approval_role", "enabled"}


@pytest.fixture(scope="module")
def controls() -> dict:
    return json.loads(CONTROLS_PATH.read_text())["controls"]


def test_controls_json_structure(controls):
    assert set(controls.keys()) == EXPECTED_IDS
    for cid, ctrl in controls.items():
        assert REQUIRED_FIELDS <= set(ctrl.keys()), f"{cid} missing fields"
        assert isinstance(ctrl["framework_mappings"], list)
        assert len(ctrl["framework_mappings"]) > 0


def test_controls_json_framework_mappings(controls):
    assert "Internal Fraud & Financial Crime Policy" in controls["FIN-PAY-001"]["framework_mappings"]
    assert "UK GDPR Art.9 / DPA 2018" in controls["COMM-EMAIL-001"]["framework_mappings"]
    assert "UK GDPR Art.5(2) accountability" in controls["COMM-EMAIL-003"]["framework_mappings"]


def test_controls_json_fin_pay_004_proposed(controls):
    assert controls["FIN-PAY-004"].get("proposed") is True
    for cid, ctrl in controls.items():
        if cid != "FIN-PAY-004":
            assert ctrl.get("proposed") is not True, f"{cid} should not be proposed"
