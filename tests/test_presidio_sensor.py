"""T20 regression tests for real Presidio-backed semantic evidence."""

from __future__ import annotations

from app.normaliser.normaliser import normalise
from app.semantic import evidence_builder, presidio_sensor
from app.semantic.presidio_sensor import HEALTH_KEYWORD_ENTITY, NHS_NUMBER_ENTITY
from scenarios.scenarios import get_raw_tool_call


def _evidence_for_scenario(number: int):
    return evidence_builder.build_evidence(normalise(get_raw_tool_call(number)))


def test_presidio_detects_scenario_4_real_pii_and_special_category_evidence():
    raw_text = get_raw_tool_call(4)["parameters"]["body"]
    raw_result = presidio_sensor.analyze_text(raw_text)
    raw_entity_types = {entity["type"] for entity in raw_result["detected_entities"]}

    evidence = _evidence_for_scenario(4)
    evidence_types = {entity.type for entity in evidence.detected_entities}
    span_labels = {span.label for span in evidence.evidence_spans}

    assert raw_result["detected_entities"], "Presidio should return real findings for scenario #4"
    assert NHS_NUMBER_ENTITY in raw_entity_types
    assert HEALTH_KEYWORD_ENTITY in raw_entity_types
    assert evidence.evaluated is True
    assert evidence.contains_personal_data is True
    assert evidence.contains_special_category_data is True
    assert evidence.sensitivity_level == "high"
    assert NHS_NUMBER_ENTITY in evidence_types | span_labels
    assert HEALTH_KEYWORD_ENTITY in evidence_types | span_labels
    assert evidence.vulnerability_indicators.present is True
    assert evidence.vulnerability_indicators.confidence == 0.88
    assert evidence.sensor_versions["presidio"]
    assert evidence.sensor_versions["nuance_stub"] == "stub-0.1"
    assert evidence.sensor_error is False


def test_presidio_scenario_6_is_personal_data_only_not_special_category():
    evidence = _evidence_for_scenario(6)
    labels = {entity.type for entity in evidence.detected_entities} | {span.label for span in evidence.evidence_spans}

    assert evidence.evaluated is True
    assert evidence.contains_personal_data is True
    assert evidence.contains_special_category_data is False
    assert NHS_NUMBER_ENTITY not in labels
    assert HEALTH_KEYWORD_ENTITY not in labels
    assert evidence.vulnerability_indicators.present is False
    assert evidence.vulnerability_indicators.confidence == 0.0
    assert evidence.sensor_versions["presidio"]
    assert evidence.sensor_versions["nuance_stub"] == "stub-0.1"
    assert evidence.sensor_error is False
