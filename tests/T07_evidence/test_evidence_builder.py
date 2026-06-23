from collections.abc import Mapping

import pytest

from app.normaliser.normaliser import normalise
from app.schemas.evidence import Evidence
from app.semantic.evidence_builder import build_evidence
from scenarios.scenarios import get_raw_tool_call

FORBIDDEN_DECISION_KEYS = {
    "decision",
    "allow",
    "block",
    "escalate",
    "approval",
    "approved",
    "enforcement",
    "executed",
    "required_approval_role",
    "control_id",
}


def _action(number: int):
    return normalise(get_raw_tool_call(number))


def _assert_no_decision_fields(value):
    if isinstance(value, Mapping):
        assert not (set(value) & FORBIDDEN_DECISION_KEYS)
        for nested in value.values():
            _assert_no_decision_fields(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_decision_fields(nested)


def test_build_evidence_payments_skip_presidio_and_nuance_for_scenarios_1_to_3(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("semantic sensor should not be called for payment actions")

    monkeypatch.setattr("app.semantic.presidio_sensor.analyze_text", fail)
    monkeypatch.setattr("app.semantic.nuance_stub.classify_vulnerability", fail)

    for number in (1, 2, 3):
        evidence = build_evidence(_action(number))
        assert isinstance(evidence, Evidence)
        assert evidence.evaluated is False
        assert evidence.contains_personal_data is False
        assert evidence.contains_special_category_data is False
        assert evidence.sensitivity_level == "low"
        assert evidence.detected_entities == []
        assert evidence.evidence_spans == []
        assert evidence.vulnerability_indicators.present is False
        assert evidence.vulnerability_indicators.categories == []
        assert evidence.sensor_versions["nuance_stub"] == "stub-0.1"
        assert evidence.sensor_error is False


def test_build_evidence_scenario_4_email_combines_real_presidio_with_labelled_stub():
    evidence = build_evidence(_action(4))

    assert evidence.evaluated is True
    assert evidence.contains_personal_data is True
    assert evidence.contains_special_category_data is True
    assert evidence.sensitivity_level == "high"
    assert evidence.detected_entities or evidence.evidence_spans
    assert {entity.source for entity in evidence.detected_entities} == {"presidio"}
    assert any(span.label in {"UK_NHS_NUMBER", "HEALTH_INFORMATION"} for span in evidence.evidence_spans)
    assert evidence.vulnerability_indicators.present is True
    assert evidence.vulnerability_indicators.confidence == 0.88
    assert evidence.vulnerability_indicators.source == "nuance_stub"
    assert set(evidence.vulnerability_indicators.categories) == {"financial_vulnerability", "health"}
    assert evidence.overall_confidence == 0.88
    assert evidence.sensor_versions["nuance_stub"] == "stub-0.1"
    assert evidence.sensor_error is False


def test_build_evidence_scenario_5_email_preserves_uncertain_vulnerability_confidence():
    evidence = build_evidence(_action(5))

    assert evidence.evaluated is True
    assert evidence.contains_special_category_data is False
    assert evidence.vulnerability_indicators.present is True
    assert evidence.vulnerability_indicators.confidence == 0.62
    assert "financial_vulnerability" in evidence.vulnerability_indicators.categories
    assert evidence.vulnerability_indicators.source == "nuance_stub"
    assert evidence.overall_confidence == 0.62
    assert evidence.sensor_versions["nuance_stub"] == "stub-0.1"
    assert evidence.sensor_error is False


def test_build_evidence_scenario_6_email_personal_data_only_allows_logging_evidence_shape():
    evidence = build_evidence(_action(6))

    assert evidence.evaluated is True
    assert evidence.contains_personal_data is True
    assert evidence.contains_special_category_data is False
    assert evidence.sensitivity_level == "medium"
    assert evidence.detected_entities or evidence.evidence_spans
    assert evidence.vulnerability_indicators.present is False
    assert evidence.vulnerability_indicators.confidence < 0.75
    assert evidence.vulnerability_indicators.categories == []
    assert evidence.sensor_error is False


@pytest.mark.parametrize("number", [1, 4])
def test_build_evidence_output_has_no_policy_decision_fields(number):
    evidence_dict = build_evidence(_action(number)).model_dump(mode="json")
    _assert_no_decision_fields(evidence_dict)
