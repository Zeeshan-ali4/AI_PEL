from __future__ import annotations

from fastapi.testclient import TestClient

import app.pipeline as pipeline_module
from app.audit.store import AuditStore
from app.main import app
from app.pipeline import PolicyPipeline
from app.settings_store import SettingsStore


def test_post_run_endpoint_returns_decision_and_record_hash_for_all_scenarios(tmp_path, monkeypatch, opa_url):
    pipe = PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
        opa_url=opa_url,
    )
    monkeypatch.setattr(pipeline_module, "_default_pipeline", pipe)
    expected = {
        1: ("allow", None, None),
        2: ("escalate", "FIN-PAY-002", "finance_supervisor"),
        3: ("block", "FIN-PAY-001", None),
        4: ("escalate", "COMM-EMAIL-001", "data_protection_approver"),
        5: ("escalate", "COMM-EMAIL-002", "vulnerable_customer_team"),
        6: ("allow_with_logging", "COMM-EMAIL-003", None),
    }

    client = TestClient(app)
    response_hash_by_id = {}
    for scenario_id, (decision, control_id, role) in expected.items():
        response = client.post(f"/run/{scenario_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["decision"]["decision"] == decision
        assert body["decision"]["control_id"] == control_id
        assert body["decision"]["required_approval_role"] == role
        assert body["record_hash"]
        assert body["record_id"] == scenario_id
        assert body["correlation_id"]
        response_hash_by_id[scenario_id] = body["record_hash"]

    records = pipe.audit_store.read_records()
    assert len(records) == 6
    persisted_hash_by_id = {record.id: record.record_hash for record in records}
    assert persisted_hash_by_id == response_hash_by_id
    assert all(persisted_hash_by_id.values())
    assert pipe.audit_store.verify_chain().intact is True


def test_post_run_rejects_unknown_scenario_without_audit_record(tmp_path, monkeypatch):
    pipe = PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
    )
    monkeypatch.setattr(pipeline_module, "_default_pipeline", pipe)

    response = TestClient(app).post("/run/999")

    assert response.status_code == 404
    assert pipe.audit_store.read_records() == []
