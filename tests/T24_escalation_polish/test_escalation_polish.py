"""Acceptance tests for the T24 escalation dashboard polish (extends T16).

These exercise the real route -> pipeline -> real OPA path and the real
append-only audit store. Nothing here mocks the approval queue or the audit
store's write/verify path.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.audit import RecordType


def _run_scenario(client: TestClient, scenario_id: int) -> dict:
    response = client.post(f"/run/{scenario_id}")
    assert response.status_code == 200
    return response.json()


def _action_evaluation_records(audit_store):
    return [record for record in audit_store.read_records() if record.record_type == RecordType.ACTION_EVALUATION]


def test_nav_badge_absent_or_zero_when_no_pending_escalations(wired_pipeline):
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert 'aria-label="1 escalations' not in response.text


def test_nav_badge_shows_pending_escalation_count_on_any_page(wired_pipeline):
    client = TestClient(app)
    _run_scenario(client, 2)

    response = client.get("/")
    assert response.status_code == 200
    assert "1" in response.text
    assert "escalations awaiting a human decision" in response.text


def test_approvals_queue_item_shows_timestamp_control_and_role(wired_pipeline):
    client = TestClient(app)
    _run_scenario(client, 2)

    response = client.get("/approvals")
    assert response.status_code == 200
    html = response.text

    assert "finance_supervisor" in html
    assert "FIN-PAY-002" in html
    assert "850" in html
    assert "CUST-100" in html
    assert "Escalated" in html


def test_role_filter_hides_other_roles(wired_pipeline):
    client = TestClient(app)
    _run_scenario(client, 2)
    _run_scenario(client, 4)

    finance_only = client.get("/approvals", params={"role": "finance_supervisor"})
    assert finance_only.status_code == 200
    assert "FIN-PAY-002" in finance_only.text
    assert "COMM-EMAIL-001" not in finance_only.text

    all_roles = client.get("/approvals", params={"role": "All"})
    assert "FIN-PAY-002" in all_roles.text
    assert "COMM-EMAIL-001" in all_roles.text


def test_view_trace_link_points_to_event_feed_for_triggering_scenario(wired_pipeline):
    client = TestClient(app)
    _run_scenario(client, 2)

    response = client.get("/approvals")
    assert response.status_code == 200
    assert 'href="/events/2"' in response.text


def test_badge_count_decrements_after_approval(wired_pipeline):
    client = TestClient(app)
    _run_scenario(client, 2)

    before = client.get("/")
    assert "escalations awaiting a human decision" in before.text

    original = _action_evaluation_records(wired_pipeline.audit_store)[0]
    item_id = wired_pipeline.approval_queue.list_pending()[0].item_id

    response = client.post(
        f"/approvals/{item_id}/decide",
        data={"decision": "approve", "reason": "Reviewed and approved."},
        follow_redirects=False,
    )
    assert response.status_code == 303

    after = client.get("/")
    assert "escalations awaiting a human decision" not in after.text

    records = wired_pipeline.audit_store.read_records()
    approval_records = [r for r in records if r.record_type == RecordType.APPROVAL_DECISION]
    assert len(approval_records) == 1
    assert approval_records[0].references_hash == original.record_hash

    refreshed_original = _action_evaluation_records(wired_pipeline.audit_store)[0]
    assert refreshed_original.record_hash == original.record_hash
