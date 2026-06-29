from __future__ import annotations

import pytest

import app.pipeline as pipeline_module
from app.audit.store import AuditStore
from app.pipeline import PolicyPipeline
from app.settings_store import SettingsStore
from tests.T12_audit.conftest import sample_action, sample_context, sample_decision, sample_evidence  # noqa: F401


@pytest.fixture
def wired_pipeline(tmp_path, monkeypatch) -> PolicyPipeline:
    pipe = PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
        opa_url="http://127.0.0.1:1",
    )
    monkeypatch.setattr(pipeline_module, "_default_pipeline", pipe)
    return pipe
