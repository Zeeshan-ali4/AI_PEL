from fastapi.testclient import TestClient

import app.pipeline as pipeline_module
from app.audit.store import AuditStore
from app.main import app
from app.settings_store import SettingsStore


client = TestClient(app)


def test_root_endpoint_returns_control_dashboard(tmp_path, monkeypatch):
    pipe = pipeline_module.PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
    )
    monkeypatch.setattr(pipeline_module, "_default_pipeline", pipe)

    response = client.get("/")

    assert response.status_code == 200
    assert "Control dashboard" in response.text


def test_health_endpoint_returns_ok_when_dependencies_are_ok(monkeypatch):
    monkeypatch.setattr("app.main._check_opa", lambda: "ok")
    monkeypatch.setattr("app.main._check_db", lambda: "ok")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "app": "ok",
        "opa": "ok",
        "db": "ok",
    }


def test_health_endpoint_returns_503_when_dependency_fails(monkeypatch):
    monkeypatch.setattr("app.main._check_opa", lambda: "ok")
    monkeypatch.setattr("app.main._check_db", lambda: "fail")

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "app": "ok",
        "opa": "ok",
        "db": "fail",
    }