from app.semantic.nuance_stub import STUB_SOURCE, assert_no_decision_fields, classify_vulnerability
from scenarios.scenarios import get_raw_tool_call


def _body(number: int) -> str:
    return get_raw_tool_call(number)["parameters"]["body"]


def test_nuance_stub_scenario_4_health_affordability_phrase_returns_fixed_high_confidence():
    result = classify_vulnerability(_body(4)).as_dict()

    assert result["present"] is True
    assert result["confidence"] == 0.88
    assert result["source"] == STUB_SOURCE
    assert set(result["categories"]) == {"financial_vulnerability", "health"}
    assert_no_decision_fields(result)


def test_nuance_stub_scenario_5_job_loss_phrase_returns_fixed_uncertain_confidence():
    result = classify_vulnerability(_body(5)).as_dict()

    assert result["present"] is True
    assert result["confidence"] == 0.62
    assert result["source"] == STUB_SOURCE
    assert result["categories"] == ["financial_vulnerability"]
    assert_no_decision_fields(result)


def test_nuance_stub_scenario_6_name_only_returns_no_vulnerability():
    result = classify_vulnerability(_body(6)).as_dict()

    assert result["present"] is False
    assert result["confidence"] < 0.75
    assert result["source"] == STUB_SOURCE
    assert result["categories"] == []
    assert_no_decision_fields(result)
