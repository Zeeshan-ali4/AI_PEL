from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.scenarios.background_events import MAX_SAMPLE_SIZE, MIN_SAMPLE_SIZE
from tests.T22_event_feed.utils import stream_scenario

_BORING_DECISIONS = {"allow", "allow_with_logging"}


def test_stream_endpoint_returns_sse_content_type(wired_pipeline):
    client = TestClient(app)
    with client.stream("GET", "/run/3/stream") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert "data:" in "".join(response.iter_text())


def test_stream_runs_background_events_then_focal_scenario_3_block(wired_pipeline):
    events = stream_scenario(3)
    assert MIN_SAMPLE_SIZE + 1 <= len(events) <= MAX_SAMPLE_SIZE + 1
    for event in events[:-1]:
        assert event["is_focal"] is False
        assert event["decision"] in _BORING_DECISIONS
        assert event.get("trace") in (None, [])
    focal = events[-1]
    assert focal["is_focal"] is True
    assert focal["decision"] == "block"
    assert focal["control_id"] == "FIN-PAY-001"
    assert focal["trace"]


def test_stream_payload_shape_matches_contract(wired_pipeline):
    events = stream_scenario(1)
    total = len(events)
    for expected_index, event in enumerate(events, start=1):
        assert {"event_index", "total_events", "is_focal", "action_summary", "decision", "control_id"}.issubset(event)
        assert event["event_index"] == expected_index
        assert event["total_events"] == total
        if event["is_focal"]:
            assert event.get("trace")
        else:
            assert "trace" not in event or event["trace"] in (None, [])


def test_stream_writes_audit_record_for_every_event_and_chain_remains_valid(wired_pipeline):
    before = len(wired_pipeline.audit_store.read_records())
    events = stream_scenario(1)
    after_records = wired_pipeline.audit_store.read_records()
    assert len(after_records) - before == len(events)
    assert wired_pipeline.audit_store.verify_chain().intact is True


def test_stream_handles_each_canonical_focal_scenario_with_correct_final_decision(wired_pipeline):
    expected = {
        1: ("allow", None),
        2: ("escalate", "FIN-PAY-002"),
        3: ("block", "FIN-PAY-001"),
        4: ("escalate", "COMM-EMAIL-001"),
        5: ("escalate", "COMM-EMAIL-002"),
        6: ("allow_with_logging", "COMM-EMAIL-003"),
    }
    for scenario_id, (decision, control_id) in expected.items():
        focal = stream_scenario(scenario_id)[-1]
        assert focal["is_focal"] is True
        assert (focal["decision"], focal["control_id"]) == (decision, control_id)


def test_unknown_scenario_stream_returns_404(wired_pipeline):
    response = TestClient(app).get("/run/999/stream")
    assert response.status_code == 404
