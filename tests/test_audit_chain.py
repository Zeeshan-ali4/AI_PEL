"""T20 regression tests for append-only hash-chain integrity and tamper detection."""

from __future__ import annotations

from app.audit.models import GENESIS_PREV_HASH
from app.audit.store import AuditStore
from app.context.resolver import resolve
from app.normaliser.normaliser import normalise
from app.schemas.audit import RecordType
from app.schemas.decision import Decision
from app.semantic.evidence_builder import build_evidence
from scenarios.scenarios import get_raw_tool_call


def _decision(decision: str = "allow", control_id: str | None = None) -> Decision:
    return Decision(
        decision=decision,
        control_id=control_id,
        triggered_controls=[control_id] if control_id else [],
        reason="T20 audit-chain regression fixture",
        required_approval_role=None,
        framework_mappings=["Internal test mapping"] if control_id else [],
        failure_mode="fail_closed",
        logging_requirements="standard",
        policy_version="test-suite",
        threshold_used=0.75,
    )


def _append_scenario_record(store: AuditStore, scenario_number: int, *, executed: bool):
    action = normalise(get_raw_tool_call(scenario_number))
    return store.write_record(
        action=action,
        context_used=resolve(action),
        evidence=build_evidence(action),
        decision=_decision(),
        enforcement_mode=action.enforcement_mode,
        executed=executed,
        record_type=RecordType.ACTION_EVALUATION,
        correlation_id=action.correlation_id,
    )


def test_audit_chain_verifies_multiple_appended_records_intact(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    records = [_append_scenario_record(store, number, executed=True) for number in (1, 2, 3)]

    assert records[0].prev_hash == GENESIS_PREV_HASH
    assert records[1].prev_hash == records[0].record_hash
    assert records[2].prev_hash == records[1].record_hash
    assert all(record.record_hash for record in records)

    result = store.verify_chain()
    assert result.intact is True
    assert result.verified_count == 3
    assert result.broken_record_id is None


def test_audit_chain_reports_exact_tampered_record(tmp_path):
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    records = [_append_scenario_record(store, number, executed=True) for number in (1, 2, 3)]
    assert store.verify_chain().intact is True

    store.simulate_tampering(records[1].id, executed=False)
    result = store.verify_chain()

    assert result.intact is False
    assert result.verified_count == 1
    assert result.broken_record_id == records[1].id
    assert result.broken_reason == "record_hash mismatch"
