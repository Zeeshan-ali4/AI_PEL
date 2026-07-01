"""TC-01 to TC-09: aggregation logic tests for the T30 reporting dashboard.

All tests run against a real SQLite store; no OPA or HTTP layer required.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


from app.audit.reporting import get_report
from app.audit.store import AuditStore, ChainVerificationResult
from app.schemas.audit import RecordType
from tests.T12_audit.conftest import (
    sample_action,
    sample_context,
    sample_decision,
    sample_evidence,
)

CONTROLS_PATH = Path(__file__).resolve().parents[2] / "opa" / "data" / "controls.json"


def _controls_data() -> dict:
    return json.loads(CONTROLS_PATH.read_text())


def _backdate(store: AuditStore, record_id: int, created_at: datetime) -> None:
    """Back-date a row's created_at via a direct DB connection (test-only helper)."""
    assert store._uses_sqlite, "only SQLite stores are used in data tests"
    db_path = store.database_url.removeprefix("sqlite:///")
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE audit_records SET created_at = ? WHERE id = ?",
        (created_at.isoformat(), record_id),
    )
    conn.commit()
    conn.close()


def _write(
    store: AuditStore,
    *,
    decision: str = "allow",
    control_id: str | None = None,
    triggered_controls: list[str] | None = None,
    correlation_id: uuid.UUID | None = None,
    created_at: datetime | None = None,
    record_type: RecordType = RecordType.ACTION_EVALUATION,
    references_hash: str | None = None,
    human_approver: str | None = None,
    approval_reason: str | None = None,
):
    cid = correlation_id or uuid.uuid4()
    action = sample_action(correlation_id=cid)
    dec = sample_decision(decision=decision, control_id=control_id)
    dec.triggered_controls = (
        triggered_controls if triggered_controls is not None else ([control_id] if control_id else [])
    )
    record = store.write_record(
        action=action,
        context_used=sample_context(),
        evidence=sample_evidence(),
        decision=dec,
        enforcement_mode="full",
        executed=True,
        record_type=record_type,
        correlation_id=cid,
        references_hash=references_hash,
        human_approver=human_approver,
        approval_reason=approval_reason,
    )
    if created_at is not None:
        _backdate(store, record.id, created_at)
    return record


# ── TC-01: Summary cards — correct KPI counts ────────────────────────────────

def test_summary_cards_correct_counts(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    _write(store, decision="allow")
    _write(store, decision="allow")
    _write(store, decision="allow_with_logging")
    _write(store, decision="escalate")
    _write(store, decision="escalate")
    _write(store, decision="block")
    _write(store, decision="fail_closed")

    report = get_report(store, "all", _controls_data())
    s = report["summary"]
    assert s["total_evaluated"] == 7
    assert s["total_allowed"] == 3
    assert s["total_escalated"] == 2
    assert s["total_blocked"] == 2


# ── TC-02: Decision breakdown — correct rows and percentages ─────────────────

def test_decision_breakdown_rows_and_percentages(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    _write(store, decision="allow")
    _write(store, decision="allow")
    _write(store, decision="allow_with_logging")
    _write(store, decision="escalate")
    _write(store, decision="escalate")
    _write(store, decision="block")
    _write(store, decision="fail_closed")

    report = get_report(store, "all", _controls_data())
    rows = {r["decision"]: r for r in report["decision_breakdown"]}

    assert rows["allow"]["count"] == 2
    assert rows["allow_with_logging"]["count"] == 1
    assert rows["escalate"]["count"] == 2
    assert rows["block"]["count"] == 1
    assert rows["fail_closed"]["count"] == 1

    total_pct = sum(r["percentage"] for r in report["decision_breakdown"])
    assert abs(total_pct - 100.0) < 1.0


# ── TC-03: Zero-count rows are omitted ───────────────────────────────────────

def test_decision_breakdown_omits_zero_count_rows(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    _write(store, decision="allow")
    _write(store, decision="escalate")

    report = get_report(store, "all", _controls_data())
    decisions_present = {r["decision"] for r in report["decision_breakdown"]}
    assert decisions_present == {"allow", "escalate"}
    assert "block" not in decisions_present
    assert "fail_closed" not in decisions_present
    assert "allow_with_logging" not in decisions_present


# ── TC-04: Control activity — firing counts and ordering ─────────────────────

def test_control_activity_counts_and_order(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    for _ in range(3):
        _write(store, decision="escalate", control_id="FIN-PAY-002",
               triggered_controls=["FIN-PAY-002"])
    _write(store, decision="escalate", control_id="COMM-EMAIL-001",
           triggered_controls=["COMM-EMAIL-001"])

    report = get_report(store, "all", _controls_data())
    rows = report["control_activity"]
    assert len(rows) == 2
    assert rows[0]["control_id"] == "FIN-PAY-002"
    assert rows[0]["count"] == 3
    assert rows[1]["control_id"] == "COMM-EMAIL-001"
    assert rows[1]["count"] == 1

    controls_data = _controls_data()["controls"]
    assert rows[0]["name"] == controls_data["FIN-PAY-002"]["description"]
    assert rows[0]["tier"] == controls_data["FIN-PAY-002"]["tier"]
    assert rows[0]["most_recent"] is not None


# ── TC-05: Escalation resolution — pending vs resolved ───────────────────────

def test_escalation_resolution_pending_vs_resolved(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    cid_approved = uuid.uuid4()
    cid_pending = uuid.uuid4()

    rec1 = _write(store, decision="escalate", correlation_id=cid_approved)
    _write(store, decision="escalate", correlation_id=cid_pending)

    _write(
        store,
        decision="allow",
        record_type=RecordType.APPROVAL_DECISION,
        correlation_id=cid_approved,
        references_hash=rec1.record_hash,
        human_approver="approver@example.com",
        approval_reason="Approved after review",
    )

    report = get_report(store, "all", _controls_data())
    es = report["escalation_summary"]
    assert es["resolved"] == 1
    assert es["pending"] == 1
    assert len(es["pending_items"]) == 1
    item = es["pending_items"][0]
    assert "correlation_id" in item
    assert str(cid_pending) == item["correlation_id"]


# ── TC-06: Period filter — today ──────────────────────────────────────────────

def test_period_filter_today(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    _write(store, decision="allow")
    eight_days_ago = datetime.now(timezone.utc) - timedelta(days=8)
    _write(store, decision="allow", created_at=eight_days_ago)

    report = get_report(store, "today", _controls_data())
    assert report["summary"]["total_evaluated"] == 1


# ── TC-07: Period filter — 7d, 30d, all ──────────────────────────────────────

def test_period_filter_7d_30d_all(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    now = datetime.now(timezone.utc)
    _write(store, decision="allow")
    _write(store, decision="allow", created_at=now - timedelta(days=6))
    _write(store, decision="allow", created_at=now - timedelta(days=8))
    _write(store, decision="allow", created_at=now - timedelta(days=29))
    _write(store, decision="allow", created_at=now - timedelta(days=31))

    r7 = get_report(store, "7d", _controls_data())
    r30 = get_report(store, "30d", _controls_data())
    rall = get_report(store, "all", _controls_data())

    assert r7["summary"]["total_evaluated"] == 2
    assert r30["summary"]["total_evaluated"] == 4
    assert rall["summary"]["total_evaluated"] == 5


# ── TC-08: Empty state — no records ──────────────────────────────────────────

def test_empty_state_returns_zero_counts_not_error(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")

    report = get_report(store, "all", _controls_data())
    assert report["summary"]["total_evaluated"] == 0
    assert report["decision_breakdown"] == []
    assert report["control_activity"] == []
    assert report["escalation_summary"]["resolved"] == 0
    assert report["escalation_summary"]["pending"] == 0


# ── TC-09: Chain integrity status passthrough shape ──────────────────────────

def test_chain_integrity_status_shape_is_returned(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    _write(store, decision="allow")
    _write(store, decision="escalate")
    _write(store, decision="block")

    verify_result = store.verify_chain()
    report = get_report(store, "all", _controls_data(), chain_status=verify_result)

    assert isinstance(report["chain_status"], ChainVerificationResult)
    assert report["chain_status"].intact is True
    assert report["chain_status"].verified_count >= 3
    assert report["chain_status"].broken_record_id is None
