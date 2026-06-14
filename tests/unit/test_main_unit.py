from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint_returns_placeholder_page():
    response = client.get("/")

    assert response.status_code == 200
    assert "Runtime Policy Enforcement Gate" in response.text
    assert "Check service health" in response.text


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