from copy import deepcopy

from app.context.resolver import resolve
from app.normaliser.normaliser import normalise
from app.schemas.context import Context
from scenarios.scenarios import get_raw_tool_call


def test_forced_resolution_failure_returns_valid_fail_closed_context():
    action = normalise(get_raw_tool_call(1))

    context = resolve(action, force_failure=True)

    assert isinstance(context, Context)
    assert context.context_resolution_ok is False
    assert context.customer.id == "CUST-100"
    assert context.payment_history.count_30d == 0
    assert context.approval_state.has_approval is False
    assert context.recipient.domain is None


def test_unknown_customer_or_missing_required_fixture_returns_failed_context():
    raw_call = deepcopy(get_raw_tool_call(1))
    raw_call["resource"]["id"] = "CUST-DOES-NOT-EXIST"
    raw_call["customer_id"] = "CUST-DOES-NOT-EXIST"
    action = normalise(raw_call)

    context = resolve(action)

    assert isinstance(context, Context)
    assert context.context_resolution_ok is False
    assert context.customer.id == "CUST-DOES-NOT-EXIST"
    assert context.payment_history.total_30d_gbp == 0.0
    assert context.recipient.approved_disclosure_basis is False


def test_no_policy_decision_fields_or_decision_logic_in_context_output():
    forbidden = {
        "decision",
        "allow",
        "block",
        "escalate",
        "control_id",
        "approval_role",
        "required_approval_role",
    }

    for scenario_number in (1, 4):
        action = normalise(get_raw_tool_call(scenario_number))
        context = resolve(action)
        dumped = context.model_dump()
        assert forbidden.isdisjoint(dumped)
        assert isinstance(context, Context)
