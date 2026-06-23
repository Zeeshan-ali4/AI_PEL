from __future__ import annotations

import inspect

from app.audit.store import AuditStore
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


def test_store_exposes_no_update_path_besides_simulate_tampering():
    public_methods = [
        name
        for name, _ in inspect.getmembers(AuditStore, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]

    assert "simulate_tampering" in public_methods
    assert AuditStore.simulate_tampering.__doc__
    docstring = AuditStore.simulate_tampering.__doc__.lower()
    assert "tamper" in docstring or "demo" in docstring

    mutating_candidates = [name for name in public_methods if name not in {"write_record", "simulate_tampering"}]
    for name in mutating_candidates:
        assert "update" not in name and "mutate" not in name


def test_write_record_never_mutates_existing_rows(store):
    snapshots = []
    for _ in range(5):
        _write(store)
        snapshots.append([record.model_dump() for record in store.read_records()])

    for index, snapshot in enumerate(snapshots[:-1]):
        latest = snapshots[-1]
        for row in snapshot:
            matching = next(record for record in latest if record["id"] == row["id"])
            assert matching == row
