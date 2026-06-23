from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.settings_store import DEFAULT_HIGH_CONFIDENCE_THRESHOLD, VALID_ENFORCEMENT_MODES, SettingsStore


def store_url(tmp_path):
    return f"sqlite:///{tmp_path / 'settings.db'}"


def test_settings_seed_defaults_on_empty_store(tmp_path):
    store = SettingsStore(store_url(tmp_path))

    settings = store.read_settings()

    assert settings.high_confidence_threshold == DEFAULT_HIGH_CONFIDENCE_THRESHOLD == 0.75
    assert store.row_count() == 1
    assert settings.control_modes
    assert set(settings.control_modes.values()) <= VALID_ENFORCEMENT_MODES


def test_threshold_update_persists_across_fresh_store_instance(tmp_path):
    url = store_url(tmp_path)
    store = SettingsStore(url)
    store.read_settings()

    updated = store.update_threshold(0.60)
    restarted_store = SettingsStore(url)

    assert updated.high_confidence_threshold == 0.60
    assert restarted_store.read_settings().high_confidence_threshold == 0.60
    assert restarted_store.row_count() == 1


@pytest.mark.parametrize("invalid_threshold", [-0.01, 1.01, "not-a-number"])
def test_threshold_update_rejects_invalid_values(tmp_path, invalid_threshold):
    store = SettingsStore(store_url(tmp_path))
    store.update_threshold(0.60)

    with pytest.raises(ValidationError):
        store.update_threshold(invalid_threshold)  # type: ignore[arg-type]

    assert store.read_settings().high_confidence_threshold == 0.60
    assert store.row_count() == 1


def test_per_control_modes_accept_only_spec_modes(tmp_path):
    store = SettingsStore(store_url(tmp_path))

    for mode in ("shadow", "soft", "full"):
        settings = store.update_control_mode("COMM-EMAIL-002", mode)
        assert settings.control_modes["COMM-EMAIL-002"] == mode
        assert store.read_settings().control_modes["COMM-EMAIL-002"] == mode

    with pytest.raises(ValidationError):
        store.update_control_mode("COMM-EMAIL-002", "monitor")  # type: ignore[arg-type]

    assert store.read_settings().control_modes["COMM-EMAIL-002"] == "full"
    assert store.row_count() == 1


def test_settings_store_uses_single_authoritative_row(tmp_path):
    store = SettingsStore(store_url(tmp_path))

    for threshold in (0.75, 0.60, 0.80):
        store.read_settings()
        store.update_threshold(threshold)
        store.update_control_mode("FIN-PAY-002", "soft")
        store.update_control_mode("FIN-PAY-002", "full")

    settings = store.read_settings()
    assert store.row_count() == 1
    assert settings.high_confidence_threshold == 0.80
    assert settings.control_modes["FIN-PAY-002"] == "full"


def test_settings_payload_ready_for_future_policy_config(tmp_path):
    store = SettingsStore(store_url(tmp_path))
    store.update_threshold(0.60)
    store.update_control_mode("COMM-EMAIL-002", "soft")

    payload = store.read_settings().to_policy_config()

    assert payload == {
        "high_confidence_threshold": 0.60,
        "control_modes": {
            **store.read_settings().control_modes,
            "COMM-EMAIL-002": "soft",
        },
    }
    forbidden_policy_decision_fields = {"decision", "allow", "block", "escalate", "threshold_used"}
    assert forbidden_policy_decision_fields.isdisjoint(payload)
