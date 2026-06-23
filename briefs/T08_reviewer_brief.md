# Review Report — T08: Settings store (runtime-editable)

## Verdict
APPROVE

## Critical findings
- None

## Spec and ledger compliance
- Correct task only: yes
- Dependencies respected: yes (T01 is DONE)
- Allowed files only: yes (`app/settings_store.py`, `tests/T08_settings/__init__.py`, `tests/T08_settings/test_settings_store.py`)
- `Done when` satisfied: yes — can read defaults (0.75), update threshold, value persists across fresh store instance
- `Verify` satisfied: yes — tests demonstrate update to 0.60 persists across a fresh SettingsStore instance against the same DB
- Reviewer focus satisfied: yes — persistence works via real SQLite in tests and Postgres path in production; threshold is a single source in one DB row with `CHECK (id = 1)` constraint; no hard-coded 0.75 outside the `DEFAULT_HIGH_CONFIDENCE_THRESHOLD` constant

## Product invariant checks
- Model is not judge: not applicable
- OPA/PDP owns decisions: pass — no decision logic in settings store
- Evidence has no decision fields: not applicable
- Fail-closed preserved: not applicable
- Append-only audit preserved: not applicable
- Stubs labelled: not applicable
- Scenario outcomes preserved: not applicable

## Required changes
None.

## Non-blocking notes
- The SQLite path for tests and Postgres path for production is a clean dual-backend design. The `CHECK (id = 1)` constraint on both backends enforces the single-row invariant at the DB level.
- Default per-control modes are all `shadow`, consistent with the safe-adoption story (spec §8). Good default choice.
- The `to_policy_config()` method on `RuntimeSettings` provides a clean handoff shape for T10/T13 without embedding any policy logic.
- All 6 test cases from the PM/BA Test Brief are covered (seed defaults, persistence across restart, invalid thresholds, invalid modes, single-row invariant, policy-config payload shape). Tests are in a single file (`test_settings_store.py`) rather than split by concern — acceptable given the narrow scope of T08 (one module, one concept).