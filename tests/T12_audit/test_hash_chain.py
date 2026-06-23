from __future__ import annotations

import json

from app.audit.models import GENESIS_PREV_HASH
from app.audit.store import canonical_json
from tests.T12_audit.conftest import sample_action, sample_context, sample_decision, sample_evidence


def _write(store, executed=True, record_type="action_evaluation"):
    return store.write_record(
        action=sample_action(),
        context_used=sample_context(),
        evidence=sample_evidence(),
        decision=sample_decision(),
        enforcement_mode="full",
        executed=executed,
        record_type=record_type,
    )


def test_chain_builds_with_correct_linkage(store):
    row1 = _write(store, executed=True)
    row2 = _write(store, executed=False)
    row3 = _write(store, executed=True)

    assert row1.prev_hash == GENESIS_PREV_HASH
    assert row2.prev_hash == row1.record_hash
    assert row3.prev_hash == row2.record_hash

    hashes = {row1.record_hash, row2.record_hash, row3.record_hash}
    assert len(hashes) == 3
    for record_hash in hashes:
        assert len(record_hash) == 64
        int(record_hash, 16)


def test_genesis_prev_hash_is_64_zeros(store):
    row = _write(store)
    assert row.prev_hash == "0" * 64
    assert len(row.prev_hash) == 64


def test_record_hash_excludes_id_and_record_hash_fields(store):
    from hashlib import sha256

    row = _write(store)
    payload = {
        "correlation_id": row.correlation_id,
        "action": row.action,
        "context_used": row.context_used,
        "evidence": row.evidence,
        "decision": row.decision,
        "enforcement_mode": row.enforcement_mode,
        "executed": row.executed,
        "record_type": row.record_type,
        "references_hash": row.references_hash,
        "human_approver": row.human_approver,
        "approval_reason": row.approval_reason,
        "created_at": row.created_at,
        "prev_hash": row.prev_hash,
    }
    recomputed = sha256((canonical_json(payload) + row.prev_hash).encode("utf-8")).hexdigest()
    assert recomputed == row.record_hash


def test_canonical_json_is_deterministic_sorted_no_whitespace():
    first = canonical_json({"b": 1, "a": 2})
    second = canonical_json({"a": 2, "b": 1})

    assert first == second
    assert first == json.dumps({"a": 2, "b": 1}, sort_keys=True, separators=(",", ":"))
    assert " " not in first
    assert "\n" not in first
