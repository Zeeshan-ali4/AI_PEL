from __future__ import annotations

from typing import Any

from app.semantic.presidio_sensor import NHS_NUMBER_ENTITY, PresidioSensor

FORBIDDEN_KEYS = {
    "decision",
    "allow",
    "block",
    "escalate",
    "approval",
    "approved",
    "required_approval_role",
    "executed",
    "control_id",
    "triggered_controls",
    "failure_mode",
    "threshold_used",
    "contains_special_category_data",
    "sensitivity_level",
    "overall_confidence",
    "vulnerability_indicators",
    "sensor_error",
    "fail_closed",
}


def _walk_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys |= _walk_keys(child)
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys |= _walk_keys(child)
        return keys
    return set()


def test_custom_nhs_number_recognizer_is_registered_with_presidio():
    body = "Please record NHS number 485 777 3456 for this customer."
    result = PresidioSensor().analyze(body)

    nhs_entities = [entity for entity in result["entities"] if entity["type"] == NHS_NUMBER_ENTITY]
    assert len(nhs_entities) == 1
    entity = nhs_entities[0]
    assert body[entity["start"] : entity["end"]] == "485 777 3456"
    assert entity["source"] == "presidio"
    assert 0.0 <= entity["score"] <= 1.0


def test_output_contract_contains_raw_evidence_only():
    body = (
        "Customer Alex Green emailed alex.green@example.org with NHS number "
        "485 777 3456 and a cancer diagnosis."
    )
    result = PresidioSensor().analyze(body)

    assert _walk_keys(result).isdisjoint(FORBIDDEN_KEYS)
    assert set(result) == {"entities", "detected_entities", "evidence_spans", "sensor_versions"}
    for entity in result["entities"]:
        assert set(entity) == {"type", "label", "score", "source", "start", "end"}
        assert entity["source"] == "presidio"
        assert body[entity["start"] : entity["end"]]
    for detected_entity in result["detected_entities"]:
        assert set(detected_entity) == {"type", "score", "source"}
        assert detected_entity["source"] == "presidio"
    for span in result["evidence_spans"]:
        assert set(span) == {"start", "end", "label"}
        assert body[span["start"] : span["end"]]


def test_sensor_handles_empty_or_whitespace_body_without_policy_decision():
    sensor = PresidioSensor()
    for body in ("", "   \n\t  ", None):
        result = sensor.analyze(body)
        assert result["entities"] == []
        assert result["detected_entities"] == []
        assert result["evidence_spans"] == []
        assert _walk_keys(result).isdisjoint(FORBIDDEN_KEYS)
