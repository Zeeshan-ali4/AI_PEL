"""Acceptance tests for the T18 audit log listing page.

Exercises the real route -> pipeline -> real OPA path and the real
append-only audit store (spec §5.5, §8A item 6). Nothing here mocks the
audit store or hand-writes record bodies.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _run_scenario(client: TestClient, scenario_id: int) -> dict:
    response = client.post(f"/run/{scenario_id}")
    assert response.status_code == 200
    return response.json()


def test_audit_log_lists_records_chronologically_with_assurance_fields(wired_pipeline):
    client = TestClient(app)
    _run_scenario(client, 1)
    _run_scenario(client, 2)
    _run_scenario(client, 3)

    records = wired_pipeline.audit_store.read_records()
    assert len(records) >= 3

    response = client.get("/audit")
    assert response.status_code == 200
    page = response.text

    # Chronological: earlier record ids should appear before later ones in the page text.
    positions = [page.index(f">{record.id}</td>") for record in records]
    assert positions == sorted(positions)

    for record in records:
        assert str(record.id) in page
        assert str(record.correlation_id) in page
        assert record.decision.decision.value in page
        assert record.record_type.value in page
        # Hashes may be shortened visually but must be present in full via title/text.
        assert record.record_hash in page
        assert record.prev_hash in page


def test_audit_log_includes_record_detail_links_when_records_exist(wired_pipeline):
    client = TestClient(app)
    _run_scenario(client, 1)

    records = wired_pipeline.audit_store.read_records()
    target = records[0]

    response = client.get("/audit")
    assert response.status_code == 200
    page = response.text

    assert f"/records/{target.record_hash}" in page

    record_response = client.get(f"/records/{target.record_hash}")
    assert record_response.status_code == 200
    assert target.record_hash in record_response.text


def test_audit_log_empty_or_minimal_state_is_board_readable(wired_pipeline):
    client = TestClient(app)

    response = client.get("/audit")
    assert response.status_code == 200
    page = response.text

    assert "no audit records" in page.lower() or "no records" in page.lower()
    assert "verify chain" in page.lower()
    # No traceback / error leakage.
    assert "Traceback" not in page


def test_reset_or_reseed_affordance_is_present_without_new_subsystem_assumption(wired_pipeline):
    client = TestClient(app)
    response = client.get("/audit")
    assert response.status_code == 200
    page = response.text.lower()

    assert "scenario" in page  # guides the user back to the demo workflow to populate/reseed
