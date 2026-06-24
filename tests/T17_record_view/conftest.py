"""Shared fixtures for T17 evidence record view/export UI tests.

Mirrors the real-OPA pattern used by tests/T15_scenarios_ui and
tests/T16_approvals_ui: a real `opa` binary is started against the real
policy/data bundle so these acceptance tests exercise real pipeline-generated
audit records, not hand-written response bodies.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

import app.pipeline as pipeline_module
from app.audit.store import AuditStore
from app.settings_store import SettingsStore


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def opa_url() -> Iterator[str]:
    """Provide a real OPA/Rego HTTP endpoint for scenario-driven UI tests."""

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


@pytest.fixture
def wired_pipeline(tmp_path, monkeypatch, opa_url) -> pipeline_module.PolicyPipeline:
    """Point the app's process-local pipeline at fresh sqlite-backed stores plus real OPA."""

    pipe = pipeline_module.PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
        opa_url=opa_url,
    )
    monkeypatch.setattr(pipeline_module, "_default_pipeline", pipe)
    return pipe
