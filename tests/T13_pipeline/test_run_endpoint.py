from __future__ import annotations

from fastapi.testclient import TestClient

import app.pipeline as pipeline_module
from app.audit.store import AuditStore
from app.main import app
from app.pipeline import PolicyPipeline
from app.settings_store import SettingsStore


def test_post_run_endpoint_returns_decision_and_record_hash(tmp_path, monkeypatch, opa_url):
    pipe = PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
        opa_url=opa_url,
    )
    monkeypatch.setattr(pipeline_module, "_default_pipeline", pipe)

    response = TestClient(app).post("/run/1")

    assert response.status_code == 200
    body = response.json()
    assert body["decision"]["decision"] == "allow"
    assert body["record_hash"]
    assert body["record_id"] == 1
    assert body["correlation_id"]
    assert body["executed"] is True


def test_post_run_rejects_unknown_scenario_without_audit_record(tmp_path, monkeypatch):
    pipe = PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
    )
    monkeypatch.setattr(pipeline_module, "_default_pipeline", pipe)

    response = TestClient(app).post("/run/999")

    assert response.status_code == 404
    assert pipe.audit_store.read_records() == []
