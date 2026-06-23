from scenarios.scenarios import get_scenarios

VALID_MODES = {"shadow", "soft", "full"}
FORBIDDEN_DECISION_FIELDS = {
    "decision",
    "allow",
    "block",
    "approval_decision",
    "executed",
    "control_id",
    "triggered_controls",
}


def raw_call(number: int):
    return get_scenarios()[number - 1]["raw_tool_call"]


def test_catalog_contains_exactly_six_canonical_scenarios():
    scenarios = get_scenarios()
    assert len(scenarios) == 6
    assert [scenario["number"] for scenario in scenarios] == [1, 2, 3, 4, 5, 6]
    assert [scenario["id"] for scenario in scenarios] == [f"scenario-{i}" for i in range(1, 7)]


def test_payment_scenarios_preserve_fixture_customer_ids_and_amounts():
    expected = [(1, "CUST-100", 80), (2, "CUST-100", 850), (3, "CUST-300", 200)]
    for number, customer_id, amount in expected:
        call = raw_call(number)
        assert call["action_kind"] == "financial.payment.issue"
        assert call["resource"]["id"] == customer_id
        assert call["customer_id"] == customer_id
        assert call["parameters"]["amount_gbp"] == amount
        assert call["parameters"]["currency"] == "GBP"
        assert call["enforcement_mode"] in VALID_MODES
    assert raw_call(2)["parameters"]["approval_present"] is False


def test_payment_scenarios_do_not_include_email_semantic_content():
    for number in (1, 2, 3):
        call = raw_call(number)
        assert call["tool_name"] == "issue_payment"
        assert call["action_kind"] == "financial.payment.issue"
        assert "recipient" not in call
        assert "body" not in call
        assert "content" not in call
        assert "body" not in call["parameters"]


def test_email_scenarios_include_required_recipients_and_planted_content():
    scenario_4 = raw_call(4)
    body_4 = scenario_4["parameters"]["body"]
    assert scenario_4["recipient"].endswith("@gmail.com")
    assert scenario_4["approved_disclosure_basis"] is False
    assert "NHS number" in body_4
    assert "cancer" in body_4
    assert "can't afford repayments" in body_4

    scenario_5 = raw_call(5)
    assert scenario_5["recipient_type"] == "external"
    assert "struggling a bit since losing my job" in scenario_5["parameters"]["body"]

    scenario_6 = raw_call(6)
    body_6 = scenario_6["parameters"]["body"]
    assert scenario_6["recipient_type"] == "external_known_partner"
    assert "trusted-partner" in scenario_6["recipient"]
    assert "Customer name:" in body_6
    assert "NHS number" not in body_6
    assert "cancer" not in body_6
    assert "can't afford repayments" not in body_6
    assert "struggling a bit since losing my job" not in body_6

    for number in (4, 5, 6):
        assert raw_call(number)["enforcement_mode"] in VALID_MODES


def test_expected_outcomes_are_metadata_not_executable_policy():
    scenarios = get_scenarios()
    assert all("expected_decision" in scenario for scenario in scenarios)
    assert all("expected_control_id" in scenario for scenario in scenarios)
    for scenario in scenarios:
        assert FORBIDDEN_DECISION_FIELDS.isdisjoint(scenario["raw_tool_call"].keys())
        assert FORBIDDEN_DECISION_FIELDS.isdisjoint(scenario["raw_tool_call"]["parameters"].keys())
