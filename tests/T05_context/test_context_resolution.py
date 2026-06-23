from app.context.resolver import resolve
from app.normaliser.normaliser import normalise
from app.schemas.context import Context
from scenarios.scenarios import get_raw_tool_call


def _action(number: int):
    return normalise(get_raw_tool_call(number))


def test_resolves_clean_low_value_payment_context_for_scenario_1():
    action = _action(1)
    context = resolve(action)

    assert isinstance(context, Context)
    assert context.customer.id == "CUST-100"
    assert context.customer.status == "normal"
    assert context.customer.fraud_flag is False
    assert context.customer.sanctions_match is False
    assert context.payment_history.count_30d < 3
    assert context.approval_state.has_approval is False
    assert context.affects_individual_financial_standing is True
    assert context.business_hours is True
    assert context.context_resolution_ok is True


def test_resolves_high_value_payment_without_approval_for_scenario_2():
    action = _action(2)
    context = resolve(action)

    assert context.customer.id == "CUST-100"
    assert context.customer.fraud_flag is False
    assert context.customer.sanctions_match is False
    assert context.customer.status == "normal"
    assert context.approval_state.has_approval is False
    assert context.approval_state.approver is None
    assert context.approval_state.approval_id is None
    assert context.context_resolution_ok is True
    assert action.parameters["amount_gbp"] == 850
    assert "amount_gbp" not in context.model_dump()


def test_resolves_fraud_flag_payment_for_scenario_3():
    context = resolve(_action(3))

    assert context.customer.id == "CUST-300"
    assert context.customer.fraud_flag is True
    assert context.customer.status in {"normal", "flagged", "blocked"}
    assert context.context_resolution_ok is True
    assert context.affects_individual_financial_standing is True


def test_resolves_external_gmail_without_disclosure_basis_for_scenario_4():
    context = resolve(_action(4))

    assert context.recipient.is_external is True
    assert context.recipient.domain == "gmail.com"
    assert context.recipient.approved_disclosure_basis is False
    assert context.affects_individual_financial_standing is False
    assert context.context_resolution_ok is True
    assert context.customer.id == "CUST-200"


def test_resolves_external_adviser_disclosure_basis_for_scenario_5():
    context = resolve(_action(5))

    assert context.recipient.is_external is True
    assert context.recipient.domain == "example.org"
    assert context.recipient.approved_disclosure_basis is True
    assert context.affects_individual_financial_standing is False
    assert context.context_resolution_ok is True
    assert context.customer.id == "CUST-250"


def test_resolves_known_partner_recipient_for_scenario_6():
    context = resolve(_action(6))

    assert context.recipient.is_external is True
    assert context.recipient.domain == "trusted-partner.example"
    assert context.recipient.approved_disclosure_basis is True
    assert context.customer.id == "CUST-100"
    assert context.affects_individual_financial_standing is False
    assert context.context_resolution_ok is True


def test_all_scenarios_return_schema_valid_context_objects():
    expected_fields = {
        "customer",
        "payment_history",
        "approval_state",
        "recipient",
        "affects_individual_financial_standing",
        "business_hours",
        "context_resolution_ok",
    }

    for number in range(1, 7):
        context = resolve(_action(number))
        assert isinstance(context, Context)
        assert set(context.model_dump()) == expected_fields
