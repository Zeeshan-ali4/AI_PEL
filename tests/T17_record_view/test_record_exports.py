"""Acceptance tests for T17 evidence-record export (JSON + human-readable).

Exercises the real route -> pipeline -> real OPA path and the real
append-only audit store (spec §5.5, §8A item 5, §12).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.audit import RecordType


def _run_scenario_1(client: TestClient) -> dict:
    response = client.post("/run/1")
    assert response.status_code == 200
    body = response.json()
    assert body["decision"]["decision"] == "allow"
    return body


def _action_evaluation_records(audit_store):
    return [record for record in audit_store.read_records() if record.record_type == RecordType.ACTION_EVALUATION]


def test_json_export_is_downloadable_valid_json_and_faithful_to_persisted_record(wired_pipeline):
    client = TestClient(app)
    _run_scenario_1(client)
    original = _action_evaluation_records(wired_pipeline.audit_store)[0]

    response = client.get(f"/records/{original.record_hash}/export.json")
    assert response.status_code == 200
    assert "json" in response.headers["content-type"]
    assert "attachment" in response.headers.get("content-disposition", "")

    payload = response.json()
    assert payload["record_hash"] == original.record_hash
    assert payload["prev_hash"] == original.prev_hash
    assert payload["correlation_id"] == str(original.correlation_id)
    assert payload["record_type"] == original.record_type.value
    assert payload["executed"] == original.executed
    assert payload["enforcement_mode"] == original.enforcement_mode.value
    assert payload["created_at"] is not None

    assert payload["action"]["action_type"] == original.action.action_type.value
    assert payload["context_used"]["customer"]["status"] == original.context_used.customer.status.value
    assert payload["decision"]["decision"] == original.decision.decision.value

    evidence = payload["evidence"]
    for forbidden in ("decision", "allow", "block", "approval", "enforcement"):
        assert forbidden not in evidence


def test_human_readable_export_is_printable_and_non_technical(wired_pipeline):
    client = TestClient(app)
    _run_scenario_1(client)
    original = _action_evaluation_records(wired_pipeline.audit_store)[0]

    response = client.get(f"/records/{original.record_hash}/export.html")
    assert response.status_code == 200
    assert "html" in response.headers["content-type"]
    assert "attachment" in response.headers.get("content-disposition", "")

    body = response.text
    for label in (
        "Evidence record",
        "Action",
        "Context used",
        "Evidence",
        "Binding decision",
        "Execution status",
        "Hash chain",
    ):
        assert label in body

    assert original.record_hash in body
    assert original.prev_hash in body
    # Not a raw JSON dump: should not contain Python-style braces wrapping the whole payload.
    assert '{"action_id"' not in body


def test_record_view_links_or_buttons_offer_both_audit_exports(wired_pipeline):
    client = TestClient(app)
    _run_scenario_1(client)
    original = _action_evaluation_records(wired_pipeline.audit_store)[0]

    response = client.get(f"/records/{original.record_hash}")
    assert response.status_code == 200
    body = response.text

    assert f"/records/{original.record_hash}/export.json" in body
    assert f"/records/{original.record_hash}/export.html" in body


def test_exports_for_unknown_record_return_404(wired_pipeline):
    client = TestClient(app)
    unknown_hash = "b" * 64

    json_response = client.get(f"/records/{unknown_hash}/export.json")
    assert json_response.status_code == 404

    html_response = client.get(f"/records/{unknown_hash}/export.html")
    assert html_response.status_code == 404
