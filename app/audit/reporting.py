"""Period-level reporting aggregations for the T30 Reporting dashboard.

Aggregates existing EvidenceRecord rows into KPI summaries a Head of Risk
can present to a board or regulator. No new schema fields; read-only over
the append-only audit store.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from app.audit.store import AuditStore, ChainVerificationResult
from app.schemas.audit import RecordType

VALID_PERIODS = frozenset({"today", "7d", "30d", "all"})
DEFAULT_PERIOD = "30d"


def _period_cutoff(period: str) -> datetime | None:
    """Return the inclusive start timestamp for the requested period, UTC.

    Returns None for 'all' (no cutoff). Defaults to 30d for unrecognised values.
    """
    now = datetime.now(timezone.utc)
    if period == "today":
        return datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    if period == "7d":
        return now - timedelta(days=7)
    if period == "30d":
        return now - timedelta(days=30)
    return None  # "all"


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _action_summary(record: Any) -> str:
    """One-line plain-English description of the action on the record."""
    action = record.action
    action_type = str(action.action_type)
    if action_type == "financial.payment.issue":
        amount = action.parameters.get("amount_gbp", "?")
        customer = action.resource.get("id", "?") if isinstance(action.resource, dict) else "?"
        return f"£{amount} payment — {customer}"
    if action_type == "communication.email.send":
        recipient = action.recipient or "unknown"
        return f"Email to {recipient}"
    return action_type


def get_report(
    store: AuditStore,
    period: str,
    controls_data: dict,
    chain_status: ChainVerificationResult | None = None,
) -> dict:
    """Aggregate audit records into a period-level summary dict.

    Args:
        store: The live audit store; records are read fresh on every call.
        period: One of 'today', '7d', '30d', 'all'. Falls back to DEFAULT_PERIOD.
        controls_data: Parsed contents of controls.json (used for name/tier lookup).
        chain_status: Optional result of a recent verify_chain() call; passed
            through to the template without re-running verification on every load.

    Returns a plain dict with keys: summary, decision_breakdown, control_activity,
    escalation_summary, chain_status, period.
    """
    if period not in VALID_PERIODS:
        period = DEFAULT_PERIOD

    all_records = store.read_records()
    cutoff = _period_cutoff(period)

    if cutoff is not None:
        records = [r for r in all_records if _ensure_utc(r.created_at) >= cutoff]
    else:
        records = all_records

    action_evals = [r for r in records if r.record_type == RecordType.ACTION_EVALUATION]

    # approval_decision records in the full (unfiltered) store determine resolution
    # status — an approval written today resolves an escalation from last week.
    all_approval_corr_ids = {
        str(r.correlation_id)
        for r in all_records
        if r.record_type == RecordType.APPROVAL_DECISION
    }

    # ── 1. Summary cards ────────────────────────────────────────────────────
    total_evaluated = len(action_evals)
    total_allowed = sum(
        1 for r in action_evals if str(r.decision.decision) in ("allow", "allow_with_logging")
    )
    total_escalated = sum(
        1 for r in action_evals if str(r.decision.decision) == "escalate"
    )
    total_blocked = sum(
        1 for r in action_evals if str(r.decision.decision) in ("block", "fail_closed")
    )

    summary = {
        "total_evaluated": total_evaluated,
        "total_allowed": total_allowed,
        "total_escalated": total_escalated,
        "total_blocked": total_blocked,
    }

    # ── 2. Decision breakdown (zero-count rows omitted) ─────────────────────
    decision_counts: dict[str, int] = defaultdict(int)
    for r in action_evals:
        decision_counts[str(r.decision.decision)] += 1

    decision_breakdown = [
        {
            "decision": dv,
            "count": count,
            "percentage": round(count / total_evaluated * 100, 1) if total_evaluated > 0 else 0.0,
        }
        for dv, count in sorted(decision_counts.items())
    ]

    # ── 3. Control activity ──────────────────────────────────────────────────
    control_counts: dict[str, int] = defaultdict(int)
    control_most_recent: dict[str, datetime] = {}

    for r in action_evals:
        for ctrl_id in r.decision.triggered_controls:
            control_counts[ctrl_id] += 1
            ts = _ensure_utc(r.created_at)
            if ctrl_id not in control_most_recent or ts > control_most_recent[ctrl_id]:
                control_most_recent[ctrl_id] = ts

    controls_catalog: dict = controls_data.get("controls", {})
    control_activity = [
        {
            "control_id": ctrl_id,
            "name": controls_catalog.get(ctrl_id, {}).get("description", ctrl_id),
            "tier": controls_catalog.get(ctrl_id, {}).get("tier", ""),
            "count": count,
            "most_recent": control_most_recent.get(ctrl_id),
        }
        for ctrl_id, count in sorted(control_counts.items(), key=lambda kv: -kv[1])
    ]

    # ── 4. Escalation resolution ─────────────────────────────────────────────
    escalate_records = [r for r in action_evals if str(r.decision.decision) == "escalate"]
    resolved = sum(1 for r in escalate_records if str(r.correlation_id) in all_approval_corr_ids)
    pending_records = [r for r in escalate_records if str(r.correlation_id) not in all_approval_corr_ids]

    escalation_summary = {
        "resolved": resolved,
        "pending": len(pending_records),
        "pending_items": [
            {
                "correlation_id": str(r.correlation_id),
                "action_summary": _action_summary(r),
                "required_approval_role": r.decision.required_approval_role,
            }
            for r in pending_records
        ],
    }

    return {
        "summary": summary,
        "decision_breakdown": decision_breakdown,
        "control_activity": control_activity,
        "escalation_summary": escalation_summary,
        "chain_status": chain_status,
        "period": period,
    }
