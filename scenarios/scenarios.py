"""Canonical demo scenarios for T03.

These entries are raw simulator inputs only. Expected outcomes are traceability
metadata for later policy tasks; they are not executable decisions.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

VALID_ENFORCEMENT_MODES = {"shadow", "soft", "full"}

_COMMON_ACTOR = {
    "agent_id": "contact-centre-agent",
    "agent_owner": "Contact Centre",
    "role": "customer_service_agent",
}

SCENARIOS: tuple[dict[str, Any], ...] = (
    {
        "id": "scenario-1",
        "number": 1,
        "title": "Payment £80 for clean customer",
        "expected_decision": "allow",
        "expected_control_id": None,
        "expected_approval_role": None,
        "raw_tool_call": {
            "scenario_id": "scenario-1",
            "action_kind": "financial.payment.issue",
            "tool_name": "issue_payment",
            "target_system": "payments_core",
            "actor": _COMMON_ACTOR,
            "resource": {"type": "customer", "id": "CUST-100"},
            "customer_id": "CUST-100",
            "parameters": {
                "amount_gbp": 80,
                "currency": "GBP",
                "approval_present": False,
                "payment_reason": "goodwill_adjustment",
            },
            "enforcement_mode": "full",
        },
    },
    {
        "id": "scenario-2",
        "number": 2,
        "title": "Payment £850 without pre-existing approval",
        "expected_decision": "escalate",
        "expected_control_id": "FIN-PAY-002",
        "expected_approval_role": "finance_supervisor",
        "raw_tool_call": {
            "scenario_id": "scenario-2",
            "action_kind": "financial.payment.issue",
            "tool_name": "issue_payment",
            "target_system": "payments_core",
            "actor": _COMMON_ACTOR,
            "resource": {"type": "customer", "id": "CUST-100"},
            "customer_id": "CUST-100",
            "parameters": {
                "amount_gbp": 850,
                "currency": "GBP",
                "approval_present": False,
                "payment_reason": "complaint_redress",
            },
            "enforcement_mode": "full",
        },
    },
    {
        "id": "scenario-3",
        "number": 3,
        "title": "Payment £200 for customer with active fraud flag",
        "expected_decision": "block",
        "expected_control_id": "FIN-PAY-001",
        "expected_approval_role": None,
        "raw_tool_call": {
            "scenario_id": "scenario-3",
            "action_kind": "financial.payment.issue",
            "tool_name": "issue_payment",
            "target_system": "payments_core",
            "actor": _COMMON_ACTOR,
            "resource": {"type": "customer", "id": "CUST-300"},
            "customer_id": "CUST-300",
            "parameters": {
                "amount_gbp": 200,
                "currency": "GBP",
                "approval_present": False,
                "payment_reason": "refund",
            },
            "enforcement_mode": "full",
        },
    },
    {
        "id": "scenario-4",
        "number": 4,
        "title": "External email with special-category and vulnerability content",
        "expected_decision": "escalate",
        "expected_control_id": "COMM-EMAIL-001",
        "expected_approval_role": "data_protection_approver",
        "raw_tool_call": {
            "scenario_id": "scenario-4",
            "action_kind": "communication.email.send",
            "tool_name": "send_email",
            "target_system": "customer_email_gateway",
            "actor": _COMMON_ACTOR,
            "resource": {"type": "customer", "id": "CUST-200"},
            "customer_id": "CUST-200",
            "recipient": "external.caseworker@gmail.com",
            "recipient_type": "external",
            "approved_disclosure_basis": False,
            "parameters": {
                "subject": "Customer support information",
                "body": "Customer Alex Green has NHS number 485 777 3456 and has discussed a cancer diagnosis. They said they can't afford repayments.",
            },
            "enforcement_mode": "full",
        },
    },
    {
        "id": "scenario-5",
        "number": 5,
        "title": "External email with uncertain vulnerability indicator",
        "expected_decision": "escalate",
        "expected_control_id": "COMM-EMAIL-002",
        "expected_approval_role": "vulnerable_customer_team",
        "raw_tool_call": {
            "scenario_id": "scenario-5",
            "action_kind": "communication.email.send",
            "tool_name": "send_email",
            "target_system": "customer_email_gateway",
            "actor": _COMMON_ACTOR,
            "resource": {"type": "customer", "id": "CUST-250"},
            "customer_id": "CUST-250",
            "recipient": "external.adviser@example.org",
            "recipient_type": "external",
            "approved_disclosure_basis": True,
            "parameters": {
                "subject": "Customer update",
                "body": "Pat Morgan told us they are struggling a bit since losing my job and asked for options on the account.",
            },
            "enforcement_mode": "full",
        },
    },
    {
        "id": "scenario-6",
        "number": 6,
        "title": "External email to known partner with customer name only",
        "expected_decision": "allow_with_logging",
        "expected_control_id": "COMM-EMAIL-003",
        "expected_approval_role": None,
        "raw_tool_call": {
            "scenario_id": "scenario-6",
            "action_kind": "communication.email.send",
            "tool_name": "send_email",
            "target_system": "customer_email_gateway",
            "actor": _COMMON_ACTOR,
            "resource": {"type": "customer", "id": "CUST-100"},
            "customer_id": "CUST-100",
            "recipient": "case.handler@trusted-partner.example",
            "recipient_type": "external_known_partner",
            "approved_disclosure_basis": True,
            "parameters": {
                "subject": "Customer reference",
                "body": "Customer name: Jamie Taylor.",
            },
            "enforcement_mode": "full",
        },
    },
)


def get_scenarios() -> tuple[dict[str, Any], ...]:
    """Return defensive copies of the canonical scenario catalog."""
    return tuple(deepcopy(scenario) for scenario in SCENARIOS)


def get_raw_tool_call(scenario_number: int) -> dict[str, Any]:
    """Return a defensive copy of one scenario's raw tool-call dictionary."""
    for scenario in SCENARIOS:
        if scenario["number"] == scenario_number:
            return deepcopy(scenario["raw_tool_call"])
    raise ValueError(f"Unknown scenario number: {scenario_number}")
