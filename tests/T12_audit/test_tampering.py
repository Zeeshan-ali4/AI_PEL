from __future__ import annotations

from tests.T12_audit.conftest import sample_action, sample_context, sample_decision, sample_evidence


def _write(store):
    return store.write_record(
        action=sample_action(),
        context_used=sample_context(),
        evidence=sample_evidence(),
        decision=sample_decision(),
        enforcement_mode="full",
        executed=True,
        record_type="action_evaluation",
    )


def test_simulate_tampering_breaks_chain_at_exact_row(store):
    row1 = _write(store)
    row2 = _write(store)
    row3 = _write(store)

    store.simulate_tampering(row2.id, executed=not row2.executed)

    result = store.verify_chain()

    assert result.intact is False
    assert result.broken_record_id == row2.id
    assert result.broken_record_id not in (row1.id, row3.id)


def test_tampering_does_not_affect_earlier_rows(store):
    row1 = _write(store)
    row2 = _write(store)

    store.simulate_tampering(row2.id, executed=not row2.executed)

    records = store.read_records()
    reread_row1 = next(record for record in records if record.id == row1.id)

    assert reread_row1.record_hash == row1.record_hash
    assert reread_row1.prev_hash == row1.prev_hash
    assert reread_row1.executed == row1.executed


def test_verify_chain_stops_at_first_broken_row(store):
    row1 = _write(store)
    row2 = _write(store)
    _write(store)
    _write(store)

    store.simulate_tampering(row2.id, executed=not row2.executed)

    result = store.verify_chain()

    assert result.broken_record_id == row2.id
    assert result.verified_count == 1
    assert row1.id != row2.id
