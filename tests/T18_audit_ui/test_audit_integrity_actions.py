"""Acceptance tests for the T18 Verify Chain / Simulate Tampering demo moment.

Exercises the real T12 `AuditStore.verify_chain()` / `simulate_tampering()`
behaviour through the real T18 web routes (spec §5.5, §8A item 6, §12).
No fake verifier is used anywhere in these tests.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _run_scenario(client: TestClient, scenario_id: int) -> dict:
    response = client.post(f"/run/{scenario_id}")
    assert response.status_code == 200
    return response.json()


def test_verify_chain_shows_green_intact_status_and_count(wired_pipeline):
    client = TestClient(app)
    _run_scenario(client, 1)
    _run_scenario(client, 2)

    records = wired_pipeline.audit_store.read_records()
    assert len(records) >= 2

    response = client.post("/audit/verify", follow_redirects=True)
    assert response.status_code == 200
    page = response.text.lower()

    assert "intact" in page
    assert str(len(records)) in response.text

    result = wired_pipeline.audit_store.verify_chain()
    assert result.intact is True
    assert result.verified_count == len(records)


def test_simulate_tampering_breaks_chain_and_names_exact_failing_record(wired_pipeline):
    client = TestClient(app)
    _run_scenario(client, 1)
    _run_scenario(client, 2)
    _run_scenario(client, 3)

    records = wired_pipeline.audit_store.read_records()
    target = records[1]

    response = client.post(
        "/audit/simulate-tampering",
        data={"record_id": target.id},
        follow_redirects=True,
    )
    assert response.status_code == 200
    page = response.text.lower()

    assert "broken" in page or "tamper" in page
    assert str(target.id) in response.text

    result = wired_pipeline.audit_store.verify_chain()
    assert result.intact is False
    assert result.broken_record_id == target.id


def test_simulate_tampering_action_is_labelled_demo_only(wired_pipeline):
    client = TestClient(app)
    _run_scenario(client, 1)

    response = client.get("/audit")
    assert response.status_code == 200
    page = response.text.lower()

    assert "demo" in page
    assert "tamper" in page


def test_no_normal_update_or_delete_audit_controls_are_exposed(wired_pipeline):
    client = TestClient(app)
    _run_scenario(client, 1)

    response = client.get("/audit")
    assert response.status_code == 200
    page = response.text.lower()

    assert "<form" in page  # the verify + tamper forms are expected
    assert "delete" not in page
    assert ">edit<" not in page
    assert "/audit/update" not in page
    assert "/audit/delete" not in page
