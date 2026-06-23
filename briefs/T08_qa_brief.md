# QA Report — T08: Settings store (runtime-editable)

## Verdict
PASS

## Ledger verification
- Command run: `pytest tests/T08_settings/ -v` (SQLite-backed, simulating persistence across restart)
- Result: passed — threshold update to 0.60 persists across a fresh SettingsStore instance (test_threshold_update_persists_across_fresh_store_instance)

## Test suite results
- Command run: `pytest tests/T08_settings/ -v`
- Total: 8 | Passed: 8 | Failed: 0 | Errors: 0
- Output summary: All 8 tests passed in 0.46s. Parametrized invalid threshold test covers -0.01, 1.01, and "not-a-number".

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `tests/T08_settings/__init__.py` | exists | ok |
| `tests/T08_settings/test_settings_store.py` | exists | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| test_settings_seed_defaults_on_empty_store | test_settings_seed_defaults_on_empty_store | test_settings_store.py | yes | Asserts threshold==0.75, row_count==1, all modes valid |
| test_threshold_update_persists_across_fresh_store_instance | test_threshold_update_persists_across_fresh_store_instance | test_settings_store.py | yes | Creates fresh SettingsStore against same DB, confirms 0.60 persists |
| test_threshold_update_rejects_invalid_values | test_threshold_update_rejects_invalid_values (parametrized) | test_settings_store.py | yes | Tests -0.01, 1.01, "not-a-number"; confirms prior valid value unchanged |
| test_per_control_modes_accept_only_spec_modes | test_per_control_modes_accept_only_spec_modes | test_settings_store.py | yes | Cycles shadow/soft/full, rejects "monitor", confirms last valid mode persists |
| test_settings_store_uses_single_authoritative_row | test_settings_store_uses_single_authoritative_row | test_settings_store.py | yes | Repeated reads/updates, asserts row_count==1 throughout |
| test_settings_payload_ready_for_future_policy_config | test_settings_payload_ready_for_future_policy_config | test_settings_store.py | yes | Checks to_policy_config() shape, asserts no decision/allow/block/escalate fields |

### Extra tests (Implementer-added)
- None beyond the brief's 6 cases (the 8 total count includes 3 parametrized variants of the invalid threshold test).

## Spec non-negotiable checks
- No decision/allow/block/escalate fields on settings store or its output: passed
- No policy logic in Python (settings store stores config only, no scenario evaluation): passed
- Single-row invariant enforced at DB level via CHECK (id = 1): passed
- Default threshold is 0.75 (DEFAULT_HIGH_CONFIDENCE_THRESHOLD constant): passed
- Per-control modes constrained to shadow/soft/full via Pydantic validation: passed
- Default per-control modes all set to "shadow" (safe adoption per spec §8): passed

## Failures
- None

## Recommendation
Proceed to human approval. All 6 test brief cases are covered, all 8 tests pass, implementation matches spec requirements, and no spec non-negotiables are violated.