from __future__ import annotations

from app.audit.store import AuditStore
from app.pipeline import PolicyPipeline
from app.schemas.decision import Decision
from app.settings_store import SettingsStore


def fake_decide(action, context, evidence, config, *, opa_url=None):
    threshold = config["high_confidence_threshold"]
    if context.customer.fraud_flag or context.customer.sanctions_match or context.customer.status == "blocked":
        return Decision(decision="block", control_id="FIN-PAY-001", triggered_controls=["FIN-PAY-001"], reason="Prohibited payment risk", required_approval_role=None, framework_mappings=["fraud"], failure_mode="fail_closed", logging_requirements="enhanced", policy_version="test", threshold_used=threshold)
    if action.action_type == "financial.payment.issue" and action.parameters.get("amount_gbp", 0) > 500 and not context.approval_state.has_approval:
        return Decision(decision="escalate", control_id="FIN-PAY-002", triggered_controls=["FIN-PAY-002"], reason="Large payment needs approval", required_approval_role="finance_supervisor", framework_mappings=["approval"], failure_mode="fail_closed", logging_requirements="enhanced", policy_version="test", threshold_used=threshold)
    if action.action_type == "communication.email.send":
        if context.recipient.is_external and evidence.contains_special_category_data and not context.recipient.approved_disclosure_basis:
            return Decision(decision="escalate", control_id="COMM-EMAIL-001", triggered_controls=["COMM-EMAIL-001"], reason="Special category disclosure", required_approval_role="data_protection_approver", framework_mappings=["gdpr"], failure_mode="fail_closed", logging_requirements="enhanced", policy_version="test", threshold_used=threshold)
        if context.recipient.is_external and evidence.vulnerability_indicators.present and evidence.overall_confidence < threshold:
            return Decision(decision="escalate", control_id="COMM-EMAIL-002", triggered_controls=["COMM-EMAIL-002"], reason="Uncertain vulnerability", required_approval_role="vulnerable_customer_team", framework_mappings=["vulnerability"], failure_mode="fail_closed", logging_requirements="enhanced", policy_version="test", threshold_used=threshold)
        if context.recipient.is_external and evidence.contains_personal_data:
            return Decision(decision="allow_with_logging", control_id="COMM-EMAIL-003", triggered_controls=["COMM-EMAIL-003"], reason="Personal data logged", required_approval_role=None, framework_mappings=["accountability"], failure_mode="fail_closed", logging_requirements="enhanced", policy_version="test", threshold_used=threshold)
    return Decision(decision="allow", control_id=None, triggered_controls=[], reason="No controls triggered", required_approval_role=None, framework_mappings=[], failure_mode="fail_closed", logging_requirements="standard", policy_version="test", threshold_used=threshold)


def pipeline(tmp_path, monkeypatch):
    monkeypatch.setattr("app.policy.opa_client.decide", fake_decide)
    return PolicyPipeline(
        settings_store=SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}"),
        audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"),
    )


def test_all_six_scenarios_write_expected_records_and_intact_chain(tmp_path, monkeypatch):
    pipe = pipeline(tmp_path, monkeypatch)
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

    records = pipe.audit_store.read_records()
    assert len(records) == 6
    assert pipe.audit_store.verify_chain().intact is True
    assert all(not record.evidence.evaluated for record in records[:3])
    assert all(record.evidence.evaluated for record in records[3:])
    assert records[3].evidence.sensor_versions["nuance_stub"] == "stub-0.1"
    assert records[3].evidence.overall_confidence == 0.88
    assert records[4].evidence.overall_confidence == 0.62


def test_escalation_queues_but_block_does_not(tmp_path, monkeypatch):
    pipe = pipeline(tmp_path, monkeypatch)
    scenario_2 = pipe.run_scenario(2)
    scenario_3 = pipe.run_scenario(3)

    assert scenario_2.record.executed is False
    assert scenario_2.enforcement_outcome.queued is True
    assert scenario_2.enforcement_outcome.queue_item.required_approval_role == "finance_supervisor"
    assert scenario_3.record.executed is False
    assert scenario_3.enforcement_outcome.queued is False
    assert len(pipe.approval_queue.list_pending()) == 1


def test_threshold_flip_for_scenario_5(tmp_path, monkeypatch):
    pipe = pipeline(tmp_path, monkeypatch)
    assert pipe.run_scenario(5).decision.decision == "escalate"
    pipe.settings_store.update_threshold(0.60)
    lowered = pipe.run_scenario(5)
    assert lowered.decision.decision == "allow_with_logging"
    assert lowered.decision.control_id == "COMM-EMAIL-003"
    assert lowered.decision.threshold_used == 0.60
