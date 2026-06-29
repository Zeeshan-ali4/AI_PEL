"""Route/template integration tests for T26 regulator-question panel."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.audit import RecordType
from app.web.regulator_questions import QUESTIONS


def test_decision_page_renders_regulator_panel_with_rows_after_scenario_run(wired_pipeline):
    client = TestClient(app)
    response = client.post('/scenarios/4/run')

    assert response.status_code == 200
    page = response.text
    assert "If a regulator asked..." in page
    for question in QUESTIONS.values():
        assert question in page
    assert "Fields:" in page
    assert "Binding decision" in page
    assert "Evidence" in page


def test_record_page_renders_same_regulator_panel_for_persisted_record(wired_pipeline):
    client = TestClient(app)
    result = wired_pipeline.run_scenario(2)

    response = client.get(f"/records/{result.record.record_hash}")

    assert response.status_code == 200
    page = response.text
    assert "If a regulator asked..." in page
    assert "finance_supervisor" in page
    for question in QUESTIONS.values():
        assert question in page
    assert result.record.record_hash in page


def test_record_page_renders_regulator_panel_for_approval_decision(wired_pipeline):
    client = TestClient(app)
    wired_pipeline.run_scenario(2)
    item_id = wired_pipeline.approval_queue.list_pending()[0].item_id
    response = client.post(
        f"/approvals/{item_id}/decide",
        data={"decision": "approve", "reason": "Approved for customer remediation", "human_approver": "j.smith@internal.example"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    approval = next(r for r in wired_pipeline.audit_store.read_records() if r.record_type == RecordType.APPROVAL_DECISION)

    page = client.get(f"/records/{approval.record_hash}").text

    assert "If a regulator asked..." in page
    assert "record_type=approval_decision" in page
    assert "j.smith@internal.example" in page
    assert "Approved for customer remediation" in page
    assert approval.references_hash in page


def test_templates_do_not_define_duplicate_question_text():
    partial = Path("app/web/templates/_regulator_questions.html").read_text()
    decision = Path("app/web/templates/decision.html").read_text()
    record = Path("app/web/templates/record.html").read_text()
    module = Path("app/web/regulator_questions.py").read_text()

    assert "regulator_question_rows" in partial
    assert '{% include "_regulator_questions.html" %}' in decision
    assert '{% include "_regulator_questions.html" %}' in record
    for question in QUESTIONS.values():
        assert question in module
        assert question not in partial
        assert question not in decision
        assert question not in record


def test_panel_answers_are_conservative_when_optional_fields_are_missing(wired_pipeline):
    record = wired_pipeline.run_scenario(1).record
    page = TestClient(app).get(f"/records/{record.record_hash}").text

    assert "None (decision.control_id is null)" in page
    assert "None (triggered_controls is empty)" in page
    assert "No human approval was required by the binding decision" in page
    assert "human_approver=None" in page
    assert "references_hash=None" in page
