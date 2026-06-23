from app.pep.agent_simulator import iter_scenario_tool_calls


def test_agent_simulator_emits_one_raw_tool_call_per_scenario_in_order():
    calls = list(iter_scenario_tool_calls())
    assert len(calls) == 6
    assert all(isinstance(call, dict) for call in calls)
    assert [call["scenario_id"] for call in calls] == [f"scenario-{i}" for i in range(1, 7)]


def test_agent_simulator_raw_calls_have_later_normalisation_fields():
    for call in iter_scenario_tool_calls():
        assert call["tool_name"]
        assert call["target_system"]
        assert call["actor"]["agent_id"]
        assert call["resource"]["id"]
        assert call["action_kind"]
        assert call["scenario_id"]
        assert isinstance(call["parameters"], dict)
        assert call["enforcement_mode"] in {"shadow", "soft", "full"}
        if call["action_kind"] == "financial.payment.issue":
            assert "amount_gbp" in call["parameters"]
            assert call["parameters"]["currency"] == "GBP"
        else:
            assert "recipient" in call
            assert "body" in call["parameters"]
