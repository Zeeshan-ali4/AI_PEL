"""Shared fixtures for T14 dashboard tests."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
import uuid
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

import app.pipeline as pipeline_module
from app.audit.store import AuditStore
from app.pipeline import PolicyPipeline
from app.schemas.action import Action
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence
from app.settings_store import SettingsStore


def sample_action(correlation_id: uuid.UUID | None = None) -> Action:
    return Action(
        action_id=uuid.uuid4(),
        correlation_id=correlation_id or uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        action_type="financial.payment.issue",
        actor={"agent_id": "agent-1", "agent_owner": "ops", "role": "clerk"},
        tool="payment_tool",
        target_system="payment_system",
        resource={"type": "customer", "id": "CUST-100"},
        parameters={"amount_gbp": 80},
        content=None,
        recipient=None,
        environment="demo",
        enforcement_mode="shadow",
    )


def sample_context() -> Context:
    return Context(
        customer={
            "id": "CUST-100",
            "status": "normal",
            "vulnerability_flag": False,
            "fraud_flag": False,
            "sanctions_match": False,
            "account_age_days": 365,
        },
        payment_history={"count_30d": 1, "total_30d_gbp": 80, "last_payment_date": None},
        approval_state={"has_approval": False, "approver": None, "approval_id": None},
        recipient={"is_external": False, "domain": None, "approved_disclosure_basis": False},
        affects_individual_financial_standing=True,
        business_hours=True,
        context_resolution_ok=True,
    )


def sample_evidence() -> Evidence:
    return Evidence(
        evaluated=False,
        contains_personal_data=False,
        contains_special_category_data=False,
        sensitivity_level="low",
        detected_entities=[],
        evidence_spans=[],
        vulnerability_indicators={"present": False, "confidence": 0.0, "categories": [], "source": "nuance_stub"},
        overall_confidence=0.0,
        sensor_versions={"presidio": "2.2.355", "nuance_stub": "stub-0.1"},
        sensor_error=False,
    )


def sample_decision(decision: str = "allow", control_id: str | None = None) -> Decision:
    return Decision(
        decision=decision,
        control_id=control_id,
        triggered_controls=[control_id] if control_id else [],
        reason="sample reason",
        required_approval_role=None,
        framework_mappings=[],
        failure_mode="fail_closed",
        logging_requirements="standard",
        policy_version="v1",
        threshold_used=0.75,
    )


def write_action_evaluation(store: AuditStore, *, decision: str, control_id: str | None) -> None:
    """Write a minimal real action_evaluation row for dashboard count assertions."""

    store.write_record(
        action=sample_action(),
        context_used=sample_context(),
        evidence=sample_evidence(),
        decision=sample_decision(decision=decision, control_id=control_id),
        enforcement_mode="shadow",
        executed=True,
        record_type="action_evaluation",
    )


@pytest.fixture
def wired_pipeline(tmp_path, monkeypatch) -> PolicyPipeline:
    """Point the app's process-local pipeline at fresh sqlite-backed stores."""

    pipe = PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
    )
    monkeypatch.setattr(pipeline_module, "_default_pipeline", pipe)
    return pipe


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def opa_url() -> Iterator[str]:
    """Provide a real OPA/Rego HTTP endpoint for scenario-driven count tests."""

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
        pytest.skip("OPA binary not available; set OPA_URL or install opa to run real Rego integration tests")

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    repo_root = Path(__file__).resolve().parents[2]
    process = subprocess.Popen(
        [
            opa_bin,
            "run",
            "--server",
            f"--addr=127.0.0.1:{port}",
            str(repo_root / "opa" / "policies"),
            str(repo_root / "opa" / "data"),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=1)
                pytest.fail(f"OPA exited before becoming healthy\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
            try:
                response = httpx.get(f"{url}/health", timeout=0.5)
                if response.status_code == 200:
                    yield url
                    return
            except Exception:
                time.sleep(0.1)
        pytest.fail("Timed out waiting for OPA test server to become healthy")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
