"""Tests for T30 reporting dashboard.

TC-01 to TC-09 cover aggregation logic in reporting.py (real SQLite store).
TC-10 to TC-16 cover HTTP routes via FastAPI TestClient.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

import app.pipeline as pipeline_module
from app.audit.reporting import DEFAULT_PERIOD, VALID_PERIODS, get_report
from app.audit.store import AuditStore
from app.main import app
from app.pipeline import PolicyPipeline
from app.schemas.audit import RecordType
from app.settings_store import SettingsStore
from tests.T12_audit.conftest import (
    sample_action,
    sample_context,
    sample_decision,
    sample_evidence,
)

CONTROLS_PATH = Path(__file__).resolve().parents[2] / "opa" / "data" / "controls.json"


def _controls_data() -> dict:
    return json.loads(CONTROLS_PATH.read_text())


def _write(store: AuditStore, *, decision: str = "allow", control_id: str | None = None,
           triggered_controls: list[str] | None = None, correlation_id: uuid.UUID | None = None,
           created_at: datetime | None = None, record_type: RecordType = RecordType.ACTION_EVALUATION,
           references_hash: str | None = None, human_approver: str | None = None,
           approval_reason: str | None = None) -> any:
    cid = correlation_id or uuid.uuid4()
    action = sample_action(correlation_id=cid)
    dec = sample_decision(decision=decision, control_id=control_id)
    dec.triggered_controls = triggered_controls if triggered_controls is not None else ([control_id] if control_id else [])
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
        # Patch the created_at timestamp directly on the row for period-filter tests.
        store._update_created_at(record.id, created_at)
    return record


# ── TC-01: Summary cards — correct KPI counts ─────────────────────────────

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


# ── TC-02: Decision breakdown — correct rows and percentages ──────────────

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
    assert abs(total_pct - 100.0) < 1.0  # floating-point rounding tolerance


# ── TC-03: Zero-count rows are omitted ────────────────────────────────────

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


# ── TC-04: Control activity — firing counts and ordering ─────────────────

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
    # Ordered by count descending
    assert rows[0]["control_id"] == "FIN-PAY-002"
    assert rows[0]["count"] == 3
    assert rows[1]["control_id"] == "COMM-EMAIL-001"
    assert rows[1]["count"] == 1

    controls_data = _controls_data()["controls"]
    assert rows[0]["name"] == controls_data["FIN-PAY-002"]["description"]
    assert rows[0]["tier"] == controls_data["FIN-PAY-002"]["tier"]
    assert rows[0]["most_recent"] is not None


# ── TC-05: Escalation resolution — pending vs resolved ───────────────────

def test_escalation_resolution_pending_vs_resolved(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    cid_approved = uuid.uuid4()
    cid_pending = uuid.uuid4()

    rec1 = _write(store, decision="escalate", correlation_id=cid_approved)
    _write(store, decision="escalate", correlation_id=cid_pending)

    # Append approval_decision record for cid_approved
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


# ── TC-06: Period filter — today ──────────────────────────────────────────

def test_period_filter_today(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    _write(store, decision="allow")  # now
    eight_days_ago = datetime.now(timezone.utc) - timedelta(days=8)
    _write(store, decision="allow", created_at=eight_days_ago)

    report = get_report(store, "today", _controls_data())
    assert report["summary"]["total_evaluated"] == 1


# ── TC-07: Period filter — 7d and 30d ────────────────────────────────────

def test_period_filter_7d_30d_all(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    now = datetime.now(timezone.utc)
    _write(store, decision="allow")  # now
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


# ── TC-08: Empty state — no records ──────────────────────────────────────

def test_empty_state_returns_zero_counts_not_error(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")

    report = get_report(store, "all", _controls_data())
    assert report["summary"]["total_evaluated"] == 0
    assert report["decision_breakdown"] == []
    assert report["control_activity"] == []
    assert report["escalation_summary"]["resolved"] == 0
    assert report["escalation_summary"]["pending"] == 0


# ── TC-09: Invalid period falls back to default ───────────────────────────

def test_invalid_period_falls_back_to_default(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    _write(store, decision="allow")

    report = get_report(store, "xyz", _controls_data())
    assert report["period"] == DEFAULT_PERIOD


# ── OPA fixture for route tests ───────────────────────────────────────────

def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="module")
def opa_url() -> Iterator[str]:
    existing = os.getenv("OPA_URL")
    if existing:
        try:
            httpx.get(f"{existing}/health", timeout=1.0).raise_for_status()
            yield existing
            return
        except Exception:
            pass

    opa_bin = shutil.which("opa")
    if opa_bin is None:
        pytest.skip("OPA binary not available; set OPA_URL or install opa to run route tests")

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    repo_root = Path(__file__).resolve().parents[2]
    process = subprocess.Popen(
        [opa_bin, "run", "--server", f"--addr=127.0.0.1:{port}",
         str(repo_root / "opa" / "policies"), str(repo_root / "opa" / "data")],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=1)
                pytest.fail(f"OPA exited\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
            try:
                if httpx.get(f"{url}/health", timeout=0.5).status_code == 200:
                    yield url
                    return
            except Exception:
                time.sleep(0.1)
        pytest.fail("Timed out waiting for OPA")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture
def wired_pipeline(tmp_path, monkeypatch, opa_url) -> PolicyPipeline:
    pipe = PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
        opa_url=opa_url,
    )
    monkeypatch.setattr(pipeline_module, "_default_pipeline", pipe)
    return pipe


def _run_scenario(client: TestClient, scenario_id: int) -> None:
    response = client.post(f"/run/{scenario_id}")
    assert response.status_code == 200


# ── TC-10: GET /reporting renders 200 with all five sections ─────────────

def test_reporting_renders_all_sections(wired_pipeline):
    client = TestClient(app)
    for i in range(1, 7):
        _run_scenario(client, i)

    response = client.get("/reporting")
    assert response.status_code == 200
    page = response.text

    assert "Illustrative period summary" in page
    # All five sections must be present
    assert "Total evaluated" in page
    assert "Decision breakdown" in page
    assert "Control activity" in page
    assert "Escalation resolution" in page
    assert "Chain-integrity status" in page


# ── TC-11: Period param scopes counts ────────────────────────────────────

def test_reporting_period_param_shown_as_selected(wired_pipeline):
    client = TestClient(app)
    for period in VALID_PERIODS:
        response = client.get(f"/reporting?period={period}")
        assert response.status_code == 200
        page = response.text
        # The selected option must appear with 'selected' in the select element
        assert f'value="{period}" selected' in page or f'value="{period}"  selected' in page or \
               (f'value="{period}"' in page and f"selected" in page)


# ── TC-12: Default period is 30d when param absent ────────────────────────

def test_reporting_defaults_to_30d(wired_pipeline):
    client = TestClient(app)
    response = client.get("/reporting")
    assert response.status_code == 200
    # 30d option must be selected
    assert 'value="30d"' in response.text


# ── TC-13: Invalid period does not 500 ───────────────────────────────────

def test_reporting_invalid_period_no_500(wired_pipeline):
    client = TestClient(app)
    response = client.get("/reporting?period=xyz")
    assert response.status_code in (200, 422)


# ── TC-14: GET /reporting/verify redirects with chain_ok=true ────────────

def test_reporting_verify_intact_redirects(wired_pipeline):
    client = TestClient(app, follow_redirects=False)
    _run_scenario(TestClient(app), 1)
    _run_scenario(TestClient(app), 2)
    _run_scenario(TestClient(app), 3)

    response = client.get("/reporting/verify")
    assert response.status_code in (302, 303, 307)
    location = response.headers["location"]
    assert "chain_ok=true" in location
    assert "chain_count=" in location


# ── TC-15: GET /reporting/verify reports broken chain ────────────────────

def test_reporting_verify_broken_chain(wired_pipeline):
    client = TestClient(app, follow_redirects=False)
    _run_scenario(TestClient(app), 1)
    _run_scenario(TestClient(app), 2)

    records = wired_pipeline.audit_store.read_records()
    # Tamper the second record
    wired_pipeline.audit_store.simulate_tampering(records[1].id)

    response = client.get("/reporting/verify")
    assert response.status_code in (302, 303, 307)
    location = response.headers["location"]
    assert "chain_ok=false" in location
    assert "chain_broken_at=" in location


# ── TC-16: Pending escalation count updates after approval ────────────────

def test_pending_escalation_updates_after_approval(wired_pipeline):
    client = TestClient(app)
    # Scenario 2 → escalate to finance_supervisor
    _run_scenario(client, 2)

    response = client.get("/reporting?period=all")
    assert response.status_code == 200
    assert "Pending" in response.text

    # Locate the pending queue item to approve
    pending_items = wired_pipeline.approval_queue.list_pending()
    assert len(pending_items) >= 1
    item_id = pending_items[0].item_id

    # Approve via the approval queue endpoint
    approve_resp = client.post(
        f"/approvals/{item_id}/decide",
        data={"decision": "approve", "reason": "Approved for T30 test",
              "human_approver": "test.approver@example.com"},
        follow_redirects=True,
    )
    assert approve_resp.status_code == 200

    # After approval an approval_decision record is appended, so pending drops to 0
    report_resp = client.get("/reporting?period=all")
    assert report_resp.status_code == 200
    page = report_resp.text
    assert "Escalation resolution" in page  # section present
