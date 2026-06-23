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


def test_verify_chain_reports_intact_with_correct_count(store):
    for _ in range(3):
        _write(store)

    result = store.verify_chain()

    assert result.intact is True
    assert result.verified_count == 3
    assert result.broken_record_id is None


def test_verify_chain_reports_intact_on_empty_store(store):
    result = store.verify_chain()

    assert result.intact is True
    assert result.verified_count == 0
    assert result.broken_record_id is None
