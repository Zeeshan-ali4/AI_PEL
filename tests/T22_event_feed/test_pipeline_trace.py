from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from tests.T22_event_feed.utils import stream_scenario


def _stage(trace, name):
    return next(stage for stage in trace if stage["stage_name"] == name)


def test_focal_trace_contains_required_stage_sequence_for_payment(wired_pipeline):
    trace = stream_scenario(3)[-1]["trace"]
    assert [stage["stage_name"] for stage in trace] == [
        "intercept",
        "normalise",
        "resolve_context",
        "semantic_skipped",
        "policy_decision",
        "enforce",
        "audit_write",
    ]
    for stage in trace:
        assert {"stage_name", "timestamp", "duration_ms", "inputs_summary", "outputs_summary"}.issubset(stage)
    semantic = _stage(trace, "semantic_skipped")
    assert semantic["outputs_summary"]["evaluated"] is False
    assert "not invoked" in semantic["outputs_summary"]["note"].lower()


def test_focal_trace_contains_semantic_evidence_for_email_scenario_4(wired_pipeline):
    trace = stream_scenario(4)[-1]["trace"]
    semantic = _stage(trace, "semantic_evidence")
    outputs = semantic["outputs_summary"]
    assert outputs["evaluated"] is True
    assert outputs["detected_entities"]
    assert outputs["vulnerability_source"] == "nuance_stub"
    assert isinstance(outputs["vulnerability_confidence"], float)
    assert _stage(trace, "policy_decision")["outputs_summary"]["threshold_used"] is not None


def test_focal_trace_policy_and_audit_outputs_are_real(wired_pipeline):
    trace = stream_scenario(3)[-1]["trace"]
    policy = _stage(trace, "policy_decision")["outputs_summary"]
    for key in ["decision", "triggered_controls", "reason", "framework_mappings", "policy_version", "threshold_used"]:
        assert key in policy
    audit = _stage(trace, "audit_write")["outputs_summary"]
    assert audit["record_id"] >= 1
    assert len(audit["record_hash"]) == 64
    assert wired_pipeline.audit_store.verify_chain().intact is True


def test_existing_run_routes_still_return_compatible_results(wired_pipeline):
    client = TestClient(app)
    api = client.post("/run/3")
    assert api.status_code == 200
    assert api.json()["decision"]["decision"] == "block"
    assert api.json()["decision"]["control_id"] == "FIN-PAY-001"

    html = client.post("/scenarios/1/run")
    assert html.status_code == 200
    assert 'data-decision="allow"' in html.text
    assert "No control was triggered" in html.text
