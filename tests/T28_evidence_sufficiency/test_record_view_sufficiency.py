from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.audit import RecordType
from tests.T28_evidence_sufficiency.test_sufficiency import _write_record


def test_record_view_renders_checklist_and_illustrative_non_certification_label(wired_pipeline):
    client = TestClient(app)
    record = _write_record(wired_pipeline.audit_store)
    response = client.get(f"/records/{record.record_hash}")
    assert response.status_code == 200
    page = response.text
    assert "Evidence sufficiency checklist" in page
    assert "Illustrative sufficiency check, not a compliance certification." in page
    assert page.count("data-sufficiency-key=") >= 5
    assert "If a regulator asked" in page


def test_record_view_updates_human_oversight_after_approval(wired_pipeline):
    client = TestClient(app)
    original = _write_record(wired_pipeline.audit_store, decision="escalate", control_id="FIN-PAY-002", mappings=["Internal Delegated-Authority Policy"], required_role="finance_supervisor", executed=False)
    before = client.get(f"/records/{original.record_hash}").text
    assert 'data-sufficiency-key="human_oversight" data-sufficiency-status="pending"' in before

    approval = _write_record(wired_pipeline.audit_store, decision="escalate", control_id="FIN-PAY-002", mappings=["Internal Delegated-Authority Policy"], required_role="finance_supervisor", executed=True, record_type=RecordType.APPROVAL_DECISION, references_hash=original.record_hash, human_approver="finance@example.internal", approval_reason="Finance supervisor approved", correlation_id=original.correlation_id)
    after = client.get(f"/records/{original.record_hash}").text
    assert approval.references_hash == original.record_hash
    assert 'data-sufficiency-key="human_oversight" data-sufficiency-status="met"' in after
    refreshed_original = next(r for r in wired_pipeline.audit_store.read_records() if r.record_type == RecordType.ACTION_EVALUATION)
    assert refreshed_original.record_hash == original.record_hash
    assert refreshed_original.human_approver is None
