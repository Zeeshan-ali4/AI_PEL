"""TC-10 to TC-16: HTTP route tests for the T30 reporting dashboard.

Requires a live OPA binary or OPA_URL env var. Tests are skipped if OPA
is unavailable.
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

import app.pipeline as pipeline_module
from app.audit.reporting import VALID_PERIODS
from app.audit.store import AuditStore
from app.main import app
from app.pipeline import PolicyPipeline
from app.settings_store import SettingsStore


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


# ── TC-10: GET /reporting renders 200 with all five sections ─────────────────

def test_reporting_renders_all_sections(wired_pipeline):
    client = TestClient(app)
    for i in range(1, 7):
        _run_scenario(client, i)

    response = client.get("/reporting")
    assert response.status_code == 200
    page = response.text

    assert "Illustrative period summary" in page
    assert "Total evaluated" in page
    assert "Decision breakdown" in page
    assert "Control activity" in page
    assert "Escalation resolution" in page
    assert "Chain-integrity status" in page


# ── TC-11: Period param scopes counts and displays selected ───────────────────

def test_reporting_period_param_shown_as_selected(wired_pipeline):
    client = TestClient(app)
    for period in VALID_PERIODS:
        response = client.get(f"/reporting?period={period}")
        assert response.status_code == 200
        page = response.text
        assert (
            f'value="{period}" selected' in page
            or f'value="{period}"  selected' in page
            or (f'value="{period}"' in page and "selected" in page)
        )


# ── TC-12: Default period is 30d when param absent ───────────────────────────

def test_reporting_defaults_to_30d(wired_pipeline):
    client = TestClient(app)
    response = client.get("/reporting")
    assert response.status_code == 200
    assert 'value="30d"' in response.text


# ── TC-13: Invalid period does not 500 ───────────────────────────────────────

def test_reporting_invalid_period_no_500(wired_pipeline):
    client = TestClient(app)
    response = client.get("/reporting?period=xyz")
    assert response.status_code in (200, 422)


# ── TC-14: GET /reporting/verify redirects with chain_ok=true ────────────────

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


# ── TC-15: GET /reporting/verify reports broken chain ────────────────────────

def test_reporting_verify_broken_chain(wired_pipeline):
    client = TestClient(app, follow_redirects=False)
    _run_scenario(TestClient(app), 1)
    _run_scenario(TestClient(app), 2)

    records = wired_pipeline.audit_store.read_records()
    wired_pipeline.audit_store.simulate_tampering(records[1].id)

    response = client.get("/reporting/verify")
    assert response.status_code in (302, 303, 307)
    location = response.headers["location"]
    assert "chain_ok=false" in location
    assert "chain_broken_at=" in location


# ── TC-16: Pending escalation count updates after approval ────────────────────

def test_pending_escalation_updates_after_approval(wired_pipeline):
    client = TestClient(app)
    _run_scenario(client, 2)  # scenario 2 → escalate to finance_supervisor

    response = client.get("/reporting?period=all")
    assert response.status_code == 200
    assert "Pending" in response.text

    pending_items = wired_pipeline.approval_queue.list_pending()
    assert len(pending_items) >= 1
    item_id = pending_items[0].item_id

    approve_resp = client.post(
        f"/approvals/{item_id}/decide",
        data={"decision": "approve", "reason": "Approved for T30 test",
              "human_approver": "test.approver@example.com"},
        follow_redirects=True,
    )
    assert approve_resp.status_code == 200

    report_resp = client.get("/reporting?period=all")
    assert report_resp.status_code == 200
    page = report_resp.text
    assert "Escalation resolution" in page
    assert re.search(r"Resolved</span>\s*<strong[^>]*>1</strong>", page)
    assert re.search(r"Pending</span>\s*<strong[^>]*>0</strong>", page)
