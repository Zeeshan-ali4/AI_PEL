"""Fixture-backed Context resolver for normalised Actions.

The resolver composes clearly labelled demo fixtures into the canonical Context
schema.  It does not call real enterprise systems and does not make policy
decisions; OPA remains the judge in later tasks.

Use ``resolve(action, force_failure=True)`` to exercise the explicit,
deterministic fail-closed context path required by the demo.
"""

from __future__ import annotations

from copy import deepcopy

from app.context.fixtures import (
    APPROVAL_FIXTURES,
    CUSTOMER_FIXTURES,
    DEMO_BUSINESS_HOURS,
    DISCLOSURE_BASIS_BY_DOMAIN,
    INTERNAL_EMAIL_DOMAINS,
    PAYMENT_HISTORY_FIXTURES,
)
from app.schemas.action import Action
from app.schemas.context import Context

_PLACEHOLDER_PAYMENT_HISTORY = {"count_30d": 0, "total_30d_gbp": 0.0, "last_payment_date": None}
_PLACEHOLDER_APPROVAL = {"has_approval": False, "approver": None, "approval_id": None}
_PLACEHOLDER_RECIPIENT = {"is_external": False, "domain": None, "approved_disclosure_basis": False}


def _customer_id_from_action(action: Action) -> str:
    return action.resource.id


def _safe_failed_context(action: Action, customer_id: str | None = None) -> Context:
    requested_customer_id = customer_id or _customer_id_from_action(action) or "UNKNOWN"
    return Context(
        customer={
            "id": requested_customer_id,
            "status": "flagged",
            "vulnerability_flag": False,
            "fraud_flag": False,
            "sanctions_match": False,
            "account_age_days": 0,
        },
        payment_history=deepcopy(_PLACEHOLDER_PAYMENT_HISTORY),
        approval_state=deepcopy(_PLACEHOLDER_APPROVAL),
        recipient=deepcopy(_PLACEHOLDER_RECIPIENT),
        affects_individual_financial_standing=action.action_type == "financial.payment.issue",
        business_hours=DEMO_BUSINESS_HOURS,
        context_resolution_ok=False,
    )


def _domain_from_recipient(recipient: str | None) -> str | None:
    if not recipient or "@" not in recipient:
        return None
    return recipient.rsplit("@", 1)[1].lower() or None


def _recipient_context(action: Action) -> dict[str, object]:
    domain = _domain_from_recipient(action.recipient)
    if action.action_type != "communication.email.send":
        return deepcopy(_PLACEHOLDER_RECIPIENT)

    is_external = domain not in INTERNAL_EMAIL_DOMAINS if domain else True
    return {
        "is_external": is_external,
        "domain": domain,
        "approved_disclosure_basis": DISCLOSURE_BASIS_BY_DOMAIN.get(domain or "", False),
    }


def resolve(action: Action, *, force_failure: bool = False) -> Context:
    """Resolve fixture-backed policy Context for a normalised Action.

    Unknown required fixture records and explicit forced failures return a valid
    Context with ``context_resolution_ok=False`` so later policy evaluation can
    fail closed without the resolver fabricating clean enterprise facts.
    """
    customer_id = _customer_id_from_action(action)
    if force_failure:
        return _safe_failed_context(action, customer_id)

    customer = CUSTOMER_FIXTURES.get(customer_id)
    payment_history = PAYMENT_HISTORY_FIXTURES.get(customer_id)
    approval_state = APPROVAL_FIXTURES.get(customer_id)
    if customer is None or payment_history is None or approval_state is None:
        return _safe_failed_context(action, customer_id)

    return Context(
        customer=deepcopy(customer),
        payment_history=deepcopy(payment_history),
        approval_state=deepcopy(approval_state),
        recipient=_recipient_context(action),
        affects_individual_financial_standing=action.action_type == "financial.payment.issue",
        business_hours=DEMO_BUSINESS_HOURS,
        context_resolution_ok=True,
    )
