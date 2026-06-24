"""Acceptance tests for the T17 single evidence-record view.

Exercises the real route -> pipeline -> real OPA path and the real
append-only audit store (spec §5.5, §8A item 5). Nothing here mocks the
audit store or hand-writes record bodies.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.audit import RecordType


def _run_scenario_2(client: TestClient) -> dict:
    response = client.post("/run/2")
    assert response.status_code == 200
    body = response.json()
    assert body["decision"]["decision"] == "escalate"
    assert body["decision"]["control_id"] == "FIN-PAY-002"
    return body


def _action_evaluation_records(audit_store):
    return [record for record in audit_store.read_records() if record.record_type == RecordType.ACTION_EVALUATION]


def test_action_evaluation_record_page_opens_with_required_assurance_fields(wired_pipeline):
    client = TestClient(app)
    _run_scenario_2(client)

    original = _action_evaluation_records(wired_pipeline.audit_store)[0]

    response = client.get(f"/records/{original.record_hash}")
    assert response.status_code == 200
    page = response.text

    assert original.record_hash in page
    assert original.prev_hash in page
    assert str(original.correlation_id) in page
    assert "escalate" in page.lower() or "escalate to a human" in page.lower()
    assert "FIN-PAY-002" in page
    assert original.enforcement_mode.value in page
    assert "Executed" in page
    assert "Hash chain" in page
    assert "Action" in page
    assert "Context used" in page
    assert "Evidence" in page
    assert "Binding decision" in page
    assert "Execution status" in page


def test_approval_decision_record_page_shows_approver_reason_execution_and_reference_hash(wired_pipeline):
    client = TestClient(app)
    _run_scenario_2(client)

    item_id = wired_pipeline.approval_queue.list_pending()[0].item_id
    response = client.post(
        f"/approvals/{item_id}/decide",
        data={
            "decision": "approve",
            "reason": "Customer remediation approved by finance supervisor",
            "human_approver": "j.smith@postoffice.example",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    records = wired_pipeline.audit_store.read_records()
    approval = next(r for r in records if r.record_type == RecordType.APPROVAL_DECISION)
    original = next(r for r in records if r.record_type == RecordType.ACTION_EVALUATION)

    page = client.get(f"/records/{approval.record_hash}")
    assert page.status_code == 200
    body = page.text

    assert approval.record_hash in body
    assert approval.prev_hash in body
    assert original.record_hash in body  # references_hash to the original
    assert "j.smith@postoffice.example" in body
    assert "Customer remediation approved by finance supervisor" in body
    assert "appended" in body.lower()

    # Reject path: approval reason and execution=false wording.
    page2 = client.get(f"/records/{original.record_hash}")
    assert page2.status_code == 200
    assert "Executed" in page2.text


def test_unknown_record_identifier_returns_clear_404(wired_pipeline):
    client = TestClient(app)
    unknown_hash = "a" * 64

    response = client.get(f"/records/{unknown_hash}")
    assert response.status_code == 404
    assert "not found" in response.text.lower() or "no audit record" in response.text.lower()
