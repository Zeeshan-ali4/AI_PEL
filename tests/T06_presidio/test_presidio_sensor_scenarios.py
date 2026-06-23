from __future__ import annotations

from app.semantic.presidio_sensor import HEALTH_KEYWORD_ENTITY, NHS_NUMBER_ENTITY, PresidioSensor
from scenarios.scenarios import get_raw_tool_call


def _body(number: int) -> str:
    return get_raw_tool_call(number)["parameters"]["body"]


def _matches(result: dict, body: str) -> list[tuple[dict, str]]:
    return [(entity, body[entity["start"] : entity["end"]]) for entity in result["entities"]]


def _assert_valid_spans(result: dict, body: str) -> None:
    for entity in result["entities"]:
        assert isinstance(entity["start"], int)
        assert isinstance(entity["end"], int)
        assert 0 <= entity["start"] < entity["end"] <= len(body)
        assert body[entity["start"] : entity["end"]]
        assert entity["label"] == entity["type"]
        assert entity["source"] == "presidio"
        assert isinstance(entity["score"], float)
        assert 0.0 <= entity["score"] <= 1.0

    for span in result["evidence_spans"]:
        assert isinstance(span["start"], int)
        assert isinstance(span["end"], int)
        assert 0 <= span["start"] < span["end"] <= len(body)
        assert body[span["start"] : span["end"]]


def test_scenario_4_detects_nhs_number_and_health_entities_with_spans():
    body = _body(4)
    result = PresidioSensor().analyze(body)

    assert (NHS_NUMBER_ENTITY, "485 777 3456") in [
        (entity["type"], text) for entity, text in _matches(result, body)
    ]
    assert any(entity["type"] == HEALTH_KEYWORD_ENTITY for entity in result["entities"])
    assert not any(key in result for key in {"decision", "allow", "block", "escalate"})
    _assert_valid_spans(result, body)


def test_scenario_5_returns_raw_presidio_findings_without_policy_judgement():
    body = _body(5)
    result = PresidioSensor().analyze(body)

    assert isinstance(result["entities"], list)
    assert not any(
        key in result
        for key in {"decision", "enforcement", "approval", "escalate", "allow", "block"}
    )
    _assert_valid_spans(result, body)


def test_scenario_6_detects_customer_name_only_no_health_or_nhs_entity():
    body = _body(6)
    result = PresidioSensor().analyze(body)

    matched_texts = [text for _, text in _matches(result, body)]
    assert "Jamie Taylor" in matched_texts
    entity_types = {entity["type"] for entity in result["entities"]}
    assert NHS_NUMBER_ENTITY not in entity_types
    assert HEALTH_KEYWORD_ENTITY not in entity_types
    assert not any(key in result for key in {"vulnerability_indicators", "decision", "escalate"})
    _assert_valid_spans(result, body)


def test_all_returned_spans_are_valid_for_original_text():
    sensor = PresidioSensor()
    for scenario_number in (4, 5, 6):
        body = _body(scenario_number)
        _assert_valid_spans(sensor.analyze(body), body)
