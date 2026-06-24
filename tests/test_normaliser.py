"""T20 regression tests for canonical action normalisation."""

from __future__ import annotations

from app.normaliser.normaliser import normalise
from scenarios.scenarios import get_raw_tool_call, get_scenarios


def _action_for(number: int):
    return normalise(get_raw_tool_call(number))


def test_normaliser_maps_all_scenarios_to_canonical_actions():
    expected_types = {
        1: "financial.payment.issue",
        2: "financial.payment.issue",
        3: "financial.payment.issue",
        4: "communication.email.send",
        5: "communication.email.send",
        6: "communication.email.send",
    }

    for scenario in get_scenarios():
        action = normalise(scenario["raw_tool_call"])

        assert str(action.action_id)
        assert str(action.correlation_id)
        assert action.timestamp.tzinfo is not None
        assert action.action_type == expected_types[scenario["number"]]
        assert action.actor.agent_id == "contact-centre-agent"
        assert action.actor.agent_owner == "Contact Centre"
        assert action.actor.role == "customer_service_agent"
        assert action.tool == scenario["raw_tool_call"]["tool_name"]
        assert action.target_system == scenario["raw_tool_call"]["target_system"]
        assert action.resource.id == scenario["raw_tool_call"]["customer_id"]
        assert action.environment == "demo"
        assert action.enforcement_mode == scenario["raw_tool_call"]["enforcement_mode"]


def test_normaliser_preserves_payment_fields_and_skips_email_fields_for_payments():
    expected_amounts = {1: 80, 2: 850, 3: 200}

    for scenario_number, amount in expected_amounts.items():
        raw = get_raw_tool_call(scenario_number)
        action = normalise(raw)

        assert action.action_type == "financial.payment.issue"
        assert action.parameters["amount_gbp"] == amount
        assert action.parameters["currency"] == "GBP"
        assert action.parameters["payment_reason"] == raw["parameters"]["payment_reason"]
        assert action.resource.type == "customer"
        assert action.resource.id == raw["customer_id"]
        assert action.content is None
        assert action.recipient is None


def test_normaliser_preserves_email_content_and_recipients():
    expected_phrases = {
        4: ["NHS number 485 777 3456", "cancer diagnosis", "can't afford repayments"],
        5: ["struggling a bit since losing my job"],
        6: ["Customer name: Jamie Taylor."],
    }

    for scenario_number, phrases in expected_phrases.items():
        raw = get_raw_tool_call(scenario_number)
        action = normalise(raw)

        assert action.action_type == "communication.email.send"
        assert action.recipient == raw["recipient"]
        assert action.content == raw["parameters"]["body"]
        assert action.parameters["subject"] == raw["parameters"]["subject"]
        for phrase in phrases:
            assert phrase in (action.content or "")
