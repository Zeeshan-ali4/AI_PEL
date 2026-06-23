from __future__ import annotations

from app.audit.store import AuditStore
from app.pipeline import PolicyPipeline
from app.settings_store import SettingsStore
from scenarios.scenarios import get_raw_tool_call


def test_context_resolution_failure_writes_fail_closed_record(tmp_path):
    pipe = PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
    )
    raw = get_raw_tool_call(1)
    raw["force_context_failure"] = True

    result = pipe.run_raw_tool_call(raw)

    assert result.decision.decision == "fail_closed"
    assert result.record.context_used.context_resolution_ok is False
    assert result.record.record_hash
    assert pipe.audit_store.verify_chain().intact is True


def test_sensor_error_writes_fail_closed_record_for_email(tmp_path, monkeypatch):
    def broken_evidence(_action):
        raise RuntimeError("sensor unavailable")

    monkeypatch.setattr("app.semantic.evidence_builder.build_evidence", broken_evidence)
    pipe = PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
    )

    result = pipe.run_scenario(4)

    assert result.decision.decision == "fail_closed"
    assert result.record.evidence.sensor_error is True
    assert result.record.record_hash


def test_opa_unreachable_writes_fail_closed_record(tmp_path):
    pipe = PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
        opa_url="http://127.0.0.1:9",
    )

    result = pipe.run_scenario(1)

    assert result.decision.decision == "fail_closed"
    assert result.decision.failure_mode == "fail_closed"
    assert result.record.record_hash
