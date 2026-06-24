"""T20 regression tests proving the six scenario decisions stay aligned to spec §7."""

from __future__ import annotations

import os
import time
from copy import deepcopy

import httpx
import pytest

from app.audit.store import AuditStore
from app.pipeline import PolicyPipeline
from app.settings_store import SettingsStore
from scenarios.scenarios import get_raw_tool_call

OPA_URL = os.environ.get("OPA_URL", "http://opa:8181")


@pytest.fixture(scope="session", autouse=True)
def opa_is_ready():
    deadline = time.time() + 20
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(f"{OPA_URL}/health", timeout=1.0)
            if response.status_code == 200:
                return
        except Exception as exc:  # pragma: no cover - diagnostic only while waiting for compose service
            last_error = exc
        time.sleep(0.5)
    pytest.fail(f"OPA was not reachable at {OPA_URL}: {last_error}")


@pytest.fixture
def pipeline(tmp_path):
    return PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
        opa_url=OPA_URL,
    )


def test_policy_decisions_match_master_spec_section_7_for_all_six_scenarios(pipeline):
    expected = {
        1: ("allow", None, None),
        2: ("escalate", "FIN-PAY-002", "finance_supervisor"),
        3: ("block", "FIN-PAY-001", None),
        4: ("escalate", "COMM-EMAIL-001", "data_protection_approver"),
        5: ("escalate", "COMM-EMAIL-002", "vulnerable_customer_team"),
        6: ("allow_with_logging", "COMM-EMAIL-003", None),
    }

    for scenario_number, (decision, control_id, approval_role) in expected.items():
        result = pipeline.run_scenario(scenario_number)
        actual = result.decision

        assert actual.decision == decision
        assert actual.control_id == control_id
        assert actual.required_approval_role == approval_role
        assert actual.threshold_used == 0.75
        assert actual.failure_mode == "fail_closed"
        assert actual.policy_version
        if control_id is None:
            assert actual.triggered_controls == []
        else:
            assert control_id in actual.triggered_controls
            assert actual.framework_mappings
        if scenario_number == 6:
            assert actual.logging_requirements == "enhanced"


def test_policy_precedence_blocks_prohibited_payment_even_when_other_payment_controls_trigger(pipeline):
    raw = deepcopy(get_raw_tool_call(3))
    raw["parameters"]["amount_gbp"] = 850

    result = pipeline.run_raw_tool_call(raw)

    assert result.decision.decision == "block"
    assert result.decision.control_id == "FIN-PAY-001"
    assert "FIN-PAY-001" in result.decision.triggered_controls
    assert "FIN-PAY-002" in result.decision.triggered_controls
    assert result.decision.required_approval_role is None


def test_threshold_change_flips_scenario_5_to_allow_with_logging(pipeline):
    default_result = pipeline.run_scenario(5)
    assert default_result.decision.decision == "escalate"
    assert default_result.decision.control_id == "COMM-EMAIL-002"
    assert default_result.decision.required_approval_role == "vulnerable_customer_team"
    assert default_result.decision.threshold_used == 0.75

    pipeline.settings_store.update_threshold(0.60)
    lowered_result = pipeline.run_scenario(5)

    assert lowered_result.decision.decision == "allow_with_logging"
    assert lowered_result.decision.control_id == "COMM-EMAIL-003"
    assert "COMM-EMAIL-002" not in lowered_result.decision.triggered_controls
    assert lowered_result.decision.required_approval_role is None
    assert lowered_result.decision.logging_requirements == "enhanced"
    assert lowered_result.decision.threshold_used == 0.60


def test_payment_scenarios_do_not_invoke_semantic_layer(pipeline):
    for scenario_number in (1, 2, 3):
        result = pipeline.run_scenario(scenario_number)
        evidence = result.record.evidence

        assert evidence.evaluated is False
        assert evidence.detected_entities == []
        assert evidence.evidence_spans == []
        assert evidence.contains_personal_data is False
        assert evidence.contains_special_category_data is False
        assert evidence.vulnerability_indicators.present is False
        assert evidence.sensor_error is False
