"""Happy-path and contract tests for canonical scenario normalisation."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.normaliser.normaliser import normalise
from app.schemas.action import Action
from scenarios.scenarios import get_raw_tool_call

CANONICAL_ACTION_FIELDS = {
    "action_id",
    "correlation_id",
    "timestamp",
    "action_type",
    "actor",
    "tool",
    "target_system",
    "resource",
    "parameters",
    "content",
    "recipient",
    "environment",
    "enforcement_mode",
}


def _uuid_version(value: UUID) -> int:
    return UUID(str(value)).version


def test_all_canonical_scenarios_normalise_to_valid_actions() -> None:
    for scenario_number in range(1, 7):
        raw_call = get_raw_tool_call(scenario_number)

        action = normalise(raw_call)

        assert isinstance(action, Action)
        assert action.environment == "demo"
        assert action.enforcement_mode == raw_call["enforcement_mode"] == "full"
        assert action.actor.model_dump() == raw_call["actor"]
        assert action.tool == raw_call["tool_name"]
        assert action.target_system == raw_call["target_system"]
        assert action.resource.model_dump() == raw_call["resource"]
        assert action.parameters == raw_call["parameters"]


def test_payment_tool_maps_to_financial_payment_issue() -> None:
    for scenario_number in (1, 2, 3):
        raw_call = get_raw_tool_call(scenario_number)

        action = normalise(raw_call)

        assert action.action_type == "financial.payment.issue"
        assert action.content is None
        assert action.recipient is None
        assert action.parameters["amount_gbp"] == raw_call["parameters"]["amount_gbp"]
        assert action.parameters["currency"] == "GBP"
        assert "approval_present" in action.parameters
        assert "payment_reason" in action.parameters


def test_email_tool_maps_to_communication_email_send() -> None:
    for scenario_number in (4, 5, 6):
        raw_call = get_raw_tool_call(scenario_number)

        action = normalise(raw_call)

        assert action.action_type == "communication.email.send"
        assert action.recipient == raw_call["recipient"]
        assert action.content == raw_call["parameters"]["body"]
        assert action.parameters["subject"] == raw_call["parameters"]["subject"]
        assert action.parameters["body"] == raw_call["parameters"]["body"]


def test_normaliser_generates_fresh_uuid4_action_and_correlation_ids() -> None:
    raw_call = get_raw_tool_call(1)

    first = normalise(raw_call)
    second = normalise(raw_call)

    assert _uuid_version(first.action_id) == 4
    assert _uuid_version(first.correlation_id) == 4
    assert _uuid_version(second.action_id) == 4
    assert _uuid_version(second.correlation_id) == 4
    assert second.action_id != first.action_id
    assert second.correlation_id != first.correlation_id
    assert str(first.action_id) != raw_call["scenario_id"]
    assert str(first.correlation_id) != raw_call["customer_id"]


def test_normaliser_sets_current_schema_valid_timestamp() -> None:
    raw_call = get_raw_tool_call(1)
    before = datetime.now(UTC) - timedelta(seconds=1)

    action = normalise(raw_call)

    after = datetime.now(UTC) + timedelta(seconds=1)
    assert isinstance(action.timestamp, datetime)
    assert before <= action.timestamp <= after


def test_missing_enforcement_mode_defaults_to_shadow() -> None:
    raw_call = deepcopy(get_raw_tool_call(1))
    raw_call.pop("enforcement_mode")

    action = normalise(raw_call)

    assert action.enforcement_mode == "shadow"


def test_normaliser_does_not_add_decision_evidence_context_or_audit_fields() -> None:
    action = normalise(get_raw_tool_call(4))
    output = action.model_dump(mode="json")

    assert set(output) == CANONICAL_ACTION_FIELDS
    forbidden_fields = {
        "decision",
        "control_id",
        "triggered_controls",
        "contains_personal_data",
        "customer",
        "payment_history",
        "executed",
        "record_hash",
        "prev_hash",
    }
    assert forbidden_fields.isdisjoint(output)
