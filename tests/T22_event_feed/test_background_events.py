from __future__ import annotations

import random

from app.scenarios.background_events import MAX_SAMPLE_SIZE, MIN_SAMPLE_SIZE, get_pool, sample_background_events
from app.schemas.decision import DecisionValue

_BORING_DECISIONS = {DecisionValue.ALLOW.value, DecisionValue.ALLOW_WITH_LOGGING.value}
_SUPPORTED_ACTION_TYPES = {"financial.payment.issue", "communication.email.send"}


def test_background_pool_contains_20_to_25_routine_templates():
    pool = get_pool()
    assert 20 <= len(pool) <= 25
    for template in pool:
        assert template["action_kind"] in _SUPPORTED_ACTION_TYPES
        assert template["tool_name"] in {"issue_payment", "send_email"}
        assert template["resource"]["id"]
        assert template["parameters"]


def test_background_sampler_returns_8_to_12_events():
    sample = sample_background_events(rng=random.Random(1))
    assert MIN_SAMPLE_SIZE <= len(sample) <= MAX_SAMPLE_SIZE
    assert all(event is not original for event, original in zip(sample, get_pool(), strict=False))
    sample[0]["parameters"]["mutated"] = True
    assert "mutated" not in sample_background_events(1, rng=random.Random(1))[0]["parameters"]


def test_background_sampler_can_produce_different_mixes():
    samples = [
        tuple(event["scenario_id"] for event in sample_background_events(8, rng=random.Random(seed)))
        for seed in range(10)
    ]
    assert len(set(samples)) > 1


def test_all_background_events_resolve_to_allow_or_allow_with_logging_with_real_pipeline(wired_pipeline):
    before = len(wired_pipeline.audit_store.read_records())
    for template in get_pool():
        result = wired_pipeline.run_event(template, capture_trace=False)
        assert result.decision.decision.value in _BORING_DECISIONS, (
            f"{template['scenario_id']} unexpectedly resolved to {result.decision.decision.value}"
        )
        assert result.record.record_type.value == "action_evaluation"

    records = wired_pipeline.audit_store.read_records()
    assert len(records) - before == len(get_pool())
    verification = wired_pipeline.audit_store.verify_chain()
    assert verification.intact is True
