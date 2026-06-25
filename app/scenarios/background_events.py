"""Pool of routine ("boring") background action templates for T22's live feed.

These are not new canonical scenarios — they reuse the same raw-tool-call shape
as `scenarios/scenarios.py` and only existing, clean fixture data (spec §5.2,
§7) so that every template resolves to `allow` or `allow_with_logging` and
never triggers an escalation, block, or fail-closed path. They exist purely to
give the T22 live event feed realistic background traffic; they are not part
of the six narrative scenarios and do not change any scenario outcome.
"""

from __future__ import annotations

import random
from copy import deepcopy
from typing import Any

_COMMON_ACTOR = {
    "agent_id": "contact-centre-agent",
    "agent_owner": "Contact Centre",
    "role": "customer_service_agent",
}

MIN_SAMPLE_SIZE = 8
MAX_SAMPLE_SIZE = 12

# Every customer here is clean in app/context/fixtures.py: no fraud_flag, no
# sanctions_match, status != blocked, and payment_history.count_30d stays
# below the FIN-PAY-003 threshold of 3.
_SAFE_CUSTOMER_IDS = ("CUST-100", "CUST-200", "CUST-250")

# Kept comfortably under the FIN-PAY-002 £500 escalation threshold.
_SAFE_PAYMENT_AMOUNTS = (15, 22, 35, 48, 60, 75, 90, 110, 130, 150, 180, 210, 250, 320, 410, 480)

# trusted-partner.example and internal.example both carry an approved
# disclosure basis / are treated as internal in app/context/fixtures.py, so
# these recipients never trigger COMM-EMAIL-001/002.
_SAFE_EMAIL_RECIPIENTS = (
    ("colleague@internal.example", "internal"),
    ("ops.team@internal.example", "internal"),
    ("case.handler@trusted-partner.example", "external_known_partner"),
    ("liaison@trusted-partner.example", "external_known_partner"),
)

_SAFE_EMAIL_BODIES = (
    "Case reference CR-{n} has been updated and is ready for review.",
    "Please confirm receipt of the attached account summary for case CR-{n}.",
    "The scheduled callback for case CR-{n} has been completed.",
    "No further action is required on case CR-{n} at this time.",
    "Case CR-{n} has been reassigned within the team for routine handling.",
)

_PAYMENT_REASONS = ("goodwill_adjustment", "service_credit", "billing_correction", "loyalty_reward")


def _payment_template(index: int, customer_id: str, amount: int, reason: str) -> dict[str, Any]:
    return {
        "scenario_id": f"background-payment-{index}",
        "action_kind": "financial.payment.issue",
        "tool_name": "issue_payment",
        "target_system": "payments_core",
        "actor": deepcopy(_COMMON_ACTOR),
        "resource": {"type": "customer", "id": customer_id},
        "customer_id": customer_id,
        "parameters": {
            "amount_gbp": amount,
            "currency": "GBP",
            "approval_present": True,
            "payment_reason": reason,
        },
        "enforcement_mode": "full",
    }


def _email_template(index: int, customer_id: str, recipient: str, recipient_type: str, body: str) -> dict[str, Any]:
    return {
        "scenario_id": f"background-email-{index}",
        "action_kind": "communication.email.send",
        "tool_name": "send_email",
        "target_system": "customer_email_gateway",
        "actor": deepcopy(_COMMON_ACTOR),
        "resource": {"type": "customer", "id": customer_id},
        "customer_id": customer_id,
        "recipient": recipient,
        "recipient_type": recipient_type,
        "approved_disclosure_basis": True,
        "parameters": {
            "subject": "Routine case update",
            "body": body.format(n=1000 + index),
        },
        "enforcement_mode": "full",
    }


def _add_payment_templates(templates: list[dict[str, Any]], target_size: int) -> None:
    index = 0
    for customer_id in _SAFE_CUSTOMER_IDS:
        for amount in _SAFE_PAYMENT_AMOUNTS:
            reason = _PAYMENT_REASONS[index % len(_PAYMENT_REASONS)]
            templates.append(_payment_template(index, customer_id, amount, reason))
            index += 1
            if len(templates) >= target_size:
                return


def _add_email_templates(templates: list[dict[str, Any]], target_size: int) -> None:
    email_index = 0
    for customer_id in _SAFE_CUSTOMER_IDS:
        for recipient, recipient_type in _SAFE_EMAIL_RECIPIENTS:
            body = _SAFE_EMAIL_BODIES[email_index % len(_SAFE_EMAIL_BODIES)]
            templates.append(_email_template(email_index, customer_id, recipient, recipient_type, body))
            email_index += 1
            if len(templates) >= target_size:
                return


def _build_pool() -> tuple[dict[str, Any], ...]:
    """Build a deterministic pool of 20–25 boring background templates."""

    templates: list[dict[str, Any]] = []
    _add_payment_templates(templates, target_size=14)
    _add_email_templates(templates, target_size=24)

    return tuple(templates)


BACKGROUND_EVENT_POOL: tuple[dict[str, Any], ...] = _build_pool()


def get_pool() -> tuple[dict[str, Any], ...]:
    """Return defensive copies of every template in the background event pool."""

    return tuple(deepcopy(template) for template in BACKGROUND_EVENT_POOL)


def sample_background_events(
    count: int | None = None,
    *,
    rng: random.Random | None = None,
) -> list[dict[str, Any]]:
    """Randomly sample 8–12 (or `count`) background templates from the pool.

    Returns defensive copies so callers (and the pipeline they feed) can mutate
    `scenario_id`/etc. freely without corrupting the shared pool.
    """

    chooser = rng or random
    pool = get_pool()
    sample_size = count if count is not None else chooser.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
    sample_size = max(1, min(sample_size, len(pool)))
    chosen = chooser.sample(pool, sample_size)
    return [deepcopy(template) for template in chosen]
