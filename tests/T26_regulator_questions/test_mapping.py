"""Acceptance tests for T26 regulator-question mapping."""

from __future__ import annotations

from app.schemas.audit import RecordType
from app.web.regulator_questions import QUESTIONS, build_regulator_question_rows


def _run_record(pipeline, scenario_id: int):
    result = pipeline.run_scenario(scenario_id)
    return result.record


def _text(rows):
    return "\n".join(f"{r['question']} {r['answer_field_label']} {r['answer_value']}" for r in rows)


def test_mapping_returns_ordered_minimum_question_rows_with_field_labels(wired_pipeline):
    rows = build_regulator_question_rows(_run_record(wired_pipeline, 1))

    assert len(rows) >= 6
    assert [row["question"] for row in rows] == list(QUESTIONS.values())
    for row in rows:
        assert row["question"]
        assert row["answer_field_label"]
        assert row["answer_value"]
        assert any(token in row["answer_field_label"] for token in ("decision.", "evidence.", "context_used.", "record_hash", "executed", "enforcement_mode"))


def test_mapping_covers_interception_policy_evidence_judge_human_and_integrity_questions(wired_pipeline):
    rows = build_regulator_question_rows(_run_record(wired_pipeline, 4))
    body = _text(rows).lower()

    assert "intercepted before execution" in body
    assert "policy/control" in body
    assert "evidence and context" in body
    assert "opa/the deterministic policy engine made the binding decision" in body
    assert "evidence sensors only informed" in body
    assert "human involved" in body
    assert "not been altered" in body
    assert "record_hash" in body and "prev_hash" in body


def test_mapping_reflects_allow_block_escalate_and_allow_with_logging_outcomes(wired_pipeline):
    expectations = {
        1: ("allow", "decision.control_id is null"),
        2: ("escalate", "finance_supervisor"),
        3: ("block", "FIN-PAY-001"),
        4: ("escalate", "data_protection_approver"),
        5: ("escalate", "vulnerable_customer_team"),
        6: ("allow_with_logging", "logging_requirements=enhanced"),
    }

    for scenario_id, (decision, expected_fragment) in expectations.items():
        rows = build_regulator_question_rows(_run_record(wired_pipeline, scenario_id))
        body = _text(rows)
        assert f"decision={decision}" in body or f"Decision: {decision}" in body or f"decision.decision={decision}" in body
        assert expected_fragment in body


def test_payment_records_explain_semantic_layer_not_invoked_from_evidence_evaluated_false(wired_pipeline):
    record = _run_record(wired_pipeline, 1)
    assert record.evidence.evaluated is False

    body = _text(build_regulator_question_rows(record))

    assert "evidence.evaluated=False" in body
    assert "semantic layer not invoked/not needed" in body
    assert "financial.payment.issue" in body
    assert "no semantic entities or model confidence are being invented" in body


def test_email_records_show_existing_semantic_evidence_and_stub_label_context(wired_pipeline):
    record = _run_record(wired_pipeline, 4)
    assert record.evidence.evaluated is True

    body = _text(build_regulator_question_rows(record))

    assert "detected_entities=" in body
    assert "vulnerability_indicators.present=" in body
    assert "overall_confidence=" in body
    assert "sensor_versions=" in body
    assert "recipient.is_external=" in body
    assert "Presidio is the real deterministic sensor" in body
    assert "nuance_stub is a labelled model stand-in" in body
    assert "model made the binding decision" not in body.lower()


def test_fail_closed_record_renders_policy_engine_unreachable_or_required_context_failure_answer(wired_pipeline):
    wired_pipeline.settings_store.arm_opa_failure_simulation()
    record = _run_record(wired_pipeline, 1)
    assert record.decision.decision.value == "fail_closed"

    body = _text(build_regulator_question_rows(record))

    assert "decision=fail_closed" in body
    assert "failure_mode=fail_closed" in body
    assert "The gate stopped by fail-closed policy" in body
    assert "context_resolution_ok=" in body
    assert "sensor_error=" in body


def test_approval_decision_record_shows_human_approver_reason_and_referenced_original_hash(wired_pipeline):
    result = wired_pipeline.run_scenario(2)
    original = result.record
    item_id = wired_pipeline.approval_queue.list_pending()[0].item_id
    wired_pipeline.approval_queue.record_approval_decision(
        item_id=item_id,
        approved=True,
        human_approver="j.smith@internal.example",
        reason="Customer remediation approved by finance supervisor",
    )
    approval = wired_pipeline.audit_store.write_record(
        action=original.action,
        context_used=original.context_used,
        evidence=original.evidence,
        decision=original.decision,
        enforcement_mode=original.enforcement_mode,
        executed=True,
        record_type=RecordType.APPROVAL_DECISION,
        references_hash=original.record_hash,
        human_approver="j.smith@internal.example",
        approval_reason="Customer remediation approved by finance supervisor",
        correlation_id=original.correlation_id,
    )

    body = _text(build_regulator_question_rows(approval))

    assert "record_type=approval_decision" in body
    assert "j.smith@internal.example" in body
    assert "Customer remediation approved by finance supervisor" in body
    assert original.record_hash in body
    assert "new appended record, not a mutation" in body
    assert approval.record_hash in body and approval.prev_hash in body


def test_non_escalation_records_state_no_human_approval_required_from_decision_field(wired_pipeline):
    for scenario_id in (1, 3, 6):
        record = _run_record(wired_pipeline, scenario_id)
        assert record.decision.required_approval_role is None
        body = _text(build_regulator_question_rows(record))
        assert "No human approval was required by the binding decision" in body
        assert "decision.required_approval_role=None" in body
        assert "human_approver=None" in body
