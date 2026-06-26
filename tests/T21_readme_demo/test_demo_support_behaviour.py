from app.audit.store import AuditStore
from app.pipeline import PolicyPipeline
from app.settings_store import SettingsStore


def test_one_shot_policy_engine_failure_auto_resets(tmp_path):
    store = SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}")
    pipeline = PolicyPipeline(settings_store=store, audit_store=AuditStore(f"sqlite:///{tmp_path / 'audit.db'}"), opa_url="http://127.0.0.1:1")

    store.arm_opa_failure_simulation()
    first = pipeline.run_scenario(1)
    assert first.decision.decision == "fail_closed"
    assert "Policy engine unreachable" in first.decision.reason
    assert store.read_settings().simulate_opa_failure_once is False

    # The second run proves the simulation was consumed. With this deliberately
    # unreachable OPA URL it still fails closed, but by the normal OPA-unreachable
    # path rather than the one-shot simulation message.
    second = pipeline.run_scenario(1)
    assert second.decision.decision == "fail_closed"
    assert "one-shot demo simulation" not in second.decision.reason
