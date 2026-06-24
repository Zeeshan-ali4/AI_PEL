"""Demo context fixtures standing in for enterprise systems.

T05 intentionally does not call real IAM, CRM, fraud, sanctions,
payment-history, approval, or disclosure-basis systems.  The dictionaries in
this module are labelled demo fixtures so the assurance UI and tests can make
clear that context is fixture-backed for the demo build.
"""

from __future__ import annotations

from datetime import date
from typing import Any

DEMO_FIXTURE_NOTICE = (
    "DEMO FIXTURES ONLY: stand-ins for IAM, CRM, fraud, sanctions, "
    "payment-history, approval, and disclosure-basis enterprise systems."
)

FIXTURE_SYSTEM_LABELS: dict[str, str] = {
    "iam": "DEMO FIXTURE stand-in for IAM / agent identity context",
    "crm": "DEMO FIXTURE stand-in for CRM customer profile context",
    "fraud": "DEMO FIXTURE stand-in for fraud-monitoring flags",
    "sanctions": "DEMO FIXTURE stand-in for sanctions-screening results",
    "payment_history": "DEMO FIXTURE stand-in for payment-history records",
    "approval": "DEMO FIXTURE stand-in for delegated-authority approvals",
    "disclosure_basis": "DEMO FIXTURE stand-in for disclosure-basis records",
}

DEMO_BUSINESS_HOURS = True

CUSTOMER_FIXTURES: dict[str, dict[str, Any]] = {
    "CUST-100": {
        "id": "CUST-100",
        "status": "normal",
        "vulnerability_flag": False,
        "fraud_flag": False,
        "sanctions_match": False,
        "account_age_days": 1420,
    },
    "CUST-200": {
        "id": "CUST-200",
        "status": "normal",
        "vulnerability_flag": True,
        "fraud_flag": False,
        "sanctions_match": False,
        "account_age_days": 690,
    },
    "CUST-250": {
        "id": "CUST-250",
        "status": "normal",
        "vulnerability_flag": False,
        "fraud_flag": False,
        "sanctions_match": False,
        "account_age_days": 365,
    },
    "CUST-300": {
        "id": "CUST-300",
        "status": "flagged",
        "vulnerability_flag": False,
        "fraud_flag": True,
        "sanctions_match": False,
        "account_age_days": 110,
    },
}

PAYMENT_HISTORY_FIXTURES: dict[str, dict[str, Any]] = {
    "CUST-100": {"count_30d": 1, "total_30d_gbp": 80.0, "last_payment_date": date(2026, 6, 10)},
    "CUST-200": {"count_30d": 0, "total_30d_gbp": 0.0, "last_payment_date": None},
    "CUST-250": {"count_30d": 0, "total_30d_gbp": 0.0, "last_payment_date": None},
    "CUST-300": {"count_30d": 1, "total_30d_gbp": 200.0, "last_payment_date": date(2026, 6, 12)},
}

APPROVAL_FIXTURES: dict[str, dict[str, Any]] = {
    "CUST-100": {"has_approval": False, "approver": None, "approval_id": None},
    "CUST-200": {"has_approval": False, "approver": None, "approval_id": None},
    "CUST-250": {"has_approval": False, "approver": None, "approval_id": None},
    "CUST-300": {"has_approval": False, "approver": None, "approval_id": None},
}

DISCLOSURE_BASIS_BY_DOMAIN: dict[str, bool] = {
    "gmail.com": False,
    "example.org": True,
    "trusted-partner.example": True,
}

INTERNAL_EMAIL_DOMAINS = {"internal.co.uk", "internal.example"}
