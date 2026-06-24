"""Acceptance tests for the T16 human approval queue view.

These exercise the real route -> pipeline -> real OPA path and the real
append-only audit store (spec §5.5, §8A item 4, §12). Nothing here mocks the
approval queue or the audit store's write/verify path.
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
    assert body["decision"]["required_approval_role"] == "finance_supervisor"
    return body


def _action_evaluation_records(audit_store):
    return [record for record in audit_store.read_records() if record.record_type == RecordType.ACTION_EVALUATION]


def test_scenario_2_escalation_appears_in_approval_queue(wired_pipeline):
    client = TestClient(app)
    _run_scenario_2(client)

    response = client.get("/approvals")
    assert response.status_code == 200
    html = response.text

    assert "finance_supervisor" in html
    assert "FIN-PAY-002" in html
    assert "850" in html
    assert "CUST-100" in html
    assert "Approve" in html
    assert "Reject" in html


def test_approve_requires_non_empty_reason_and_does_not_append_when_blank(wired_pipeline):
    client = TestClient(app)
    _run_scenario_2(client)

    original = _action_evaluation_records(wired_pipeline.audit_store)[0]
    before_count = len(wired_pipeline.audit_store.read_records())

    pending = wired_pipeline.approval_queue.list_pending()
    assert len(pending) == 1
    item_id = pending[0].item_id

    response = client.post(
        f"/approvals/{item_id}/decide",
        data={"decision": "approve", "reason": "   "},
        follow_redirects=False,
    )
    assert response.status_code in (303, 400, 422)

    records = wired_pipeline.audit_store.read_records()
    assert len(records) == before_count

    refreshed_original = _action_evaluation_records(wired_pipeline.audit_store)[0]
    assert refreshed_original.record_hash == original.record_hash
    assert refreshed_original.executed == original.executed
    assert refreshed_original.record_type == original.record_type
    assert refreshed_original.decision == original.decision
    assert refreshed_original.created_at == original.created_at

    approvals_page = client.get("/approvals")
    assert "finance_supervisor" in approvals_page.text


def test_approve_with_reason_appends_linked_approval_decision_and_marks_item_actioned(wired_pipeline):
    client = TestClient(app)
    _run_scenario_2(client)

    original = _action_evaluation_records(wired_pipeline.audit_store)[0]
    item_id = wired_pipeline.approval_queue.list_pending()[0].item_id

    response = client.post(
        f"/approvals/{item_id}/decide",
        data={
            "decision": "approve",
            "reason": "Customer remediation approved by finance supervisor",
            "human_approver": "j.smith@internal.example",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    records = wired_pipeline.audit_store.read_records()
    approval_records = [r for r in records if r.record_type == RecordType.APPROVAL_DECISION]
    assert len(approval_records) == 1
    approval = approval_records[0]

    assert approval.correlation_id == original.correlation_id
    assert approval.references_hash == original.record_hash
    assert approval.human_approver == "j.smith@internal.example"
    assert approval.approval_reason == "Customer remediation approved by finance supervisor"
    assert approval.executed is True

    refreshed_original = _action_evaluation_records(wired_pipeline.audit_store)[0]
    assert refreshed_original.record_hash == original.record_hash
    assert refreshed_original.executed is False

    verification = wired_pipeline.audit_store.verify_chain()
    assert verification.intact is True

    approvals_page = client.get("/approvals")
    assert approvals_page.status_code == 200
    assert "Approved" in approvals_page.text
    assert wired_pipeline.approval_queue.list_pending() == []


def test_reject_with_reason_appends_linked_rejection_decision_without_execution(wired_pipeline):
    client = TestClient(app)
    _run_scenario_2(client)

    original = _action_evaluation_records(wired_pipeline.audit_store)[0]
    item_id = wired_pipeline.approval_queue.list_pending()[0].item_id

    response = client.post(
        f"/approvals/{item_id}/decide",
        data={"decision": "reject", "reason": "Insufficient supporting evidence for payment"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    records = wired_pipeline.audit_store.read_records()
    approval_records = [r for r in records if r.record_type == RecordType.APPROVAL_DECISION]
    assert len(approval_records) == 1
    rejection = approval_records[0]

    assert rejection.correlation_id == original.correlation_id
    assert rejection.references_hash == original.record_hash
    assert rejection.approval_reason == "Insufficient supporting evidence for payment"
    assert rejection.executed is False

    refreshed_original = _action_evaluation_records(wired_pipeline.audit_store)[0]
    assert refreshed_original.record_hash == original.record_hash
    assert refreshed_original.executed is False

    verification = wired_pipeline.audit_store.verify_chain()
    assert verification.intact is True

    assert wired_pipeline.approval_queue.list_pending() == []
    approvals_page = client.get("/approvals")
    assert "Rejected" in approvals_page.text


def test_reject_requires_non_empty_reason_and_preserves_pending_item(wired_pipeline):
    client = TestClient(app)
    _run_scenario_2(client)

    before_count = len(wired_pipeline.audit_store.read_records())
    item_id = wired_pipeline.approval_queue.list_pending()[0].item_id

    response = client.post(
        f"/approvals/{item_id}/decide",
        data={"decision": "reject", "reason": ""},
        follow_redirects=False,
    )
    assert response.status_code in (303, 400, 422)

    records = wired_pipeline.audit_store.read_records()
    assert len(records) == before_count
    assert any(r.record_type == RecordType.APPROVAL_DECISION for r in records) is False

    original = _action_evaluation_records(wired_pipeline.audit_store)[0]
    assert original.executed is False

    pending = wired_pipeline.approval_queue.list_pending()
    assert len(pending) == 1
    assert pending[0].item_id == item_id

    approvals_page = client.get("/approvals")
    assert "finance_supervisor" in approvals_page.text


def test_approval_view_does_not_invoke_or_reclassify_semantic_evidence_for_payment(wired_pipeline):
    client = TestClient(app)
    _run_scenario_2(client)

    original = _action_evaluation_records(wired_pipeline.audit_store)[0]
    assert original.evidence.evaluated is False

    client.get("/approvals")

    item_id = wired_pipeline.approval_queue.list_pending()[0].item_id
    client.post(
        f"/approvals/{item_id}/decide",
        data={"decision": "approve", "reason": "Reviewed payment history and approved."},
        follow_redirects=False,
    )

    refreshed_original = _action_evaluation_records(wired_pipeline.audit_store)[0]
    assert refreshed_original.evidence.evaluated is False
    assert refreshed_original.evidence.model_dump(mode="json") == original.evidence.model_dump(mode="json")

    records = wired_pipeline.audit_store.read_records()
    approval_record = next(r for r in records if r.record_type == RecordType.APPROVAL_DECISION)
    assert approval_record.evidence.evaluated is False
    assert not hasattr(approval_record.evidence, "decision")
    assert not hasattr(approval_record.evidence, "allow")
    assert not hasattr(approval_record.evidence, "block")
    assert not hasattr(approval_record.evidence, "approval")
