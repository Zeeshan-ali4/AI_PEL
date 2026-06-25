"""Acceptance tests for the T22 live event feed (spec §11, §7, §8A; TASK_LEDGER T22).

Exercises the real pipeline (real OPA, real audit store) through the new SSE
endpoint and the background-event pool, per AGENTS.md's requirement that
Presidio/OPA/the hash chain stay real in any test that asserts their
behaviour.
"""

from __future__ import annotations

import json
import random

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.scenarios.background_events import (
    MAX_SAMPLE_SIZE,
    MIN_SAMPLE_SIZE,
    get_pool,
    sample_background_events,
)
from app.schemas.decision import DecisionValue

_BORING_DECISIONS = {DecisionValue.ALLOW.value, DecisionValue.ALLOW_WITH_LOGGING.value}


def _parse_sse_events(body: str) -> list[dict]:
    events = []
    for raw_block in body.split("\n\n"):
        block = raw_block.strip()
        if not block:
            continue
        for line in block.splitlines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:") :].strip()))
    return events


def _stream_scenario(client: TestClient, scenario_id: int) -> list[dict]:
    with client.stream("GET", f"/run/{scenario_id}/stream") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        body = "".join(response.iter_text())
    return _parse_sse_events(body)


# --- 1. Background pool sampling -------------------------------------------------


def test_sample_background_events_defaults_to_8_to_12():
    sample = sample_background_events(rng=random.Random(1))
    assert MIN_SAMPLE_SIZE <= len(sample) <= MAX_SAMPLE_SIZE


def test_sample_background_events_respects_explicit_count():
    sample = sample_background_events(10, rng=random.Random(2))
    assert len(sample) == 10


def test_repeated_samples_are_not_always_identical():
    samples = [
        tuple(event["scenario_id"] for event in sample_background_events(8, rng=random.Random(seed)))
        for seed in range(10)
    ]
    assert len(set(samples)) > 1


# --- 2. Background events are boring ----------------------------------------------


def test_every_background_template_resolves_to_allow_or_allow_with_logging(wired_pipeline):
    pool = get_pool()
    assert 20 <= len(pool) <= 25

    for template in pool:
        result = wired_pipeline.run_event(template, capture_trace=False)
        assert result.decision.decision.value in _BORING_DECISIONS, (
            f"{template['scenario_id']} unexpectedly resolved to {result.decision.decision.value}"
        )
        assert result.record.record_type.value == "action_evaluation"

    verification = wired_pipeline.audit_store.verify_chain()
    assert verification.intact is True
    assert verification.verified_count == len(pool)


# --- 3. SSE stream: fraud block (scenario 3) --------------------------------------


def test_stream_scenario_3_lands_on_block_with_full_trace(wired_pipeline):
    client = TestClient(app)
    events = _stream_scenario(client, 3)

    assert len(events) >= MIN_SAMPLE_SIZE + 1
    background_events = events[:-1]
    focal_event = events[-1]

    for event in background_events:
        assert event["is_focal"] is False
        assert event["decision"] in _BORING_DECISIONS
        assert not event.get("trace")

    assert focal_event["is_focal"] is True
    assert focal_event["decision"] == "block"
    assert focal_event["control_id"] == "FIN-PAY-001"

    stage_names = {stage["stage_name"] for stage in focal_event["trace"]}
    expected_stages = {
        "intercept",
        "normalise",
        "resolve_context",
        "semantic_skipped",
        "policy_decision",
        "enforce",
        "audit_write",
    }
    assert expected_stages.issubset(stage_names)


# --- 4. SSE stream: escalation with semantic evidence (scenario 4) ----------------


def test_stream_scenario_4_focal_trace_shows_real_semantic_evidence(wired_pipeline):
    client = TestClient(app)
    events = _stream_scenario(client, 4)
    focal_event = events[-1]

    assert focal_event["is_focal"] is True
    assert focal_event["decision"] == "escalate"
    assert focal_event["control_id"] == "COMM-EMAIL-001"

    semantic_stage = next(
        stage for stage in focal_event["trace"] if stage["stage_name"] == "semantic_evidence"
    )
    outputs = semantic_stage["outputs_summary"]
    assert outputs["detected_entities"], "expected real Presidio entities in the trace"
    assert outputs["vulnerability_source"] == "nuance_stub"
    assert isinstance(outputs["vulnerability_confidence"], float)


# --- 5. Trace does not break existing routes --------------------------------------


def test_json_run_endpoint_unchanged_after_trace_support(wired_pipeline):
    client = TestClient(app)
    response = client.post("/run/1")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "decision",
        "record_hash",
        "record_id",
        "correlation_id",
        "executed",
        "enforcement",
    }


def test_html_scenario_run_route_still_renders(wired_pipeline):
    client = TestClient(app)
    response = client.post("/scenarios/1/run")
    assert response.status_code == 200
    assert "Allow" in response.text or "allow" in response.text.lower()


# --- 6. Audit integrity after a full feed run -------------------------------------


def test_full_feed_run_keeps_chain_intact_and_writes_a_record_per_event(wired_pipeline):
    client = TestClient(app)
    events = _stream_scenario(client, 1)

    records = wired_pipeline.audit_store.read_records()
    assert len(records) == len(events)

    verification = wired_pipeline.audit_store.verify_chain()
    assert verification.intact is True
    assert verification.verified_count == len(records)


def test_unknown_scenario_stream_returns_404(wired_pipeline):
    client = TestClient(app)
    response = client.get("/run/999/stream")
    assert response.status_code == 404
