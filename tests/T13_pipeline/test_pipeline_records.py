from __future__ import annotations

from app.audit.store import AuditStore
from app.pipeline import PolicyPipeline
from app.settings_store import SettingsStore


def pipeline(tmp_path, opa_url):
    return PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
        opa_url=opa_url,
    )


def test_all_six_scenarios_write_expected_records_and_intact_chain(tmp_path, opa_url):
    pipe = pipeline(tmp_path, opa_url)
    expected = {
        1: ("allow", None, None),
        2: ("escalate", "FIN-PAY-002", "finance_supervisor"),
        3: ("block", "FIN-PAY-001", None),
        4: ("escalate", "COMM-EMAIL-001", "data_protection_approver"),
        5: ("escalate", "COMM-EMAIL-002", "vulnerable_customer_team"),
        6: ("allow_with_logging", "COMM-EMAIL-003", None),
    }

    for scenario_id, (decision, control_id, role) in expected.items():
        result = pipe.run_scenario(scenario_id)
        assert result.decision.decision == decision
        assert result.decision.control_id == control_id
        assert result.decision.required_approval_role == role
        assert result.record.record_hash
        assert result.record.record_type == "action_evaluation"
        assert result.decision.policy_version == "1.0.0-t10"

    records = pipe.audit_store.read_records()
    assert len(records) == 6
    assert pipe.audit_store.verify_chain().intact is True
    assert all(not record.evidence.evaluated for record in records[:3])
    assert all(record.evidence.evaluated for record in records[3:])
    assert records[3].evidence.sensor_versions["nuance_stub"] == "stub-0.1"
    assert records[3].evidence.overall_confidence == 0.88
    assert records[4].evidence.overall_confidence == 0.62


def test_escalation_queues_but_block_does_not(tmp_path, opa_url):
    pipe = pipeline(tmp_path, opa_url)
    scenario_2 = pipe.run_scenario(2)
    scenario_3 = pipe.run_scenario(3)

    assert scenario_2.record.executed is False
    assert scenario_2.enforcement_outcome.queued is True
    assert scenario_2.enforcement_outcome.queue_item.required_approval_role == "finance_supervisor"
    assert scenario_3.record.executed is False
    assert scenario_3.enforcement_outcome.queued is False
    assert len(pipe.approval_queue.list_pending()) == 1


def test_threshold_flip_for_scenario_5(tmp_path, opa_url):
    pipe = pipeline(tmp_path, opa_url)
    assert pipe.run_scenario(5).decision.decision == "escalate"
    pipe.settings_store.update_threshold(0.60)
    lowered = pipe.run_scenario(5)
    assert lowered.decision.decision == "allow_with_logging"
    assert lowered.decision.control_id == "COMM-EMAIL-003"
    assert lowered.decision.threshold_used == 0.60
