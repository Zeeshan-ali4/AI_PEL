# Reviewer Brief — T23: Policy rule editor (extends T19)

## Files reviewed against architect/test briefs
- `app/settings_store.py`
- `opa/data/controls.json`
- `opa/policies/common.rego`
- `opa/policies/payment.rego`
- `app/policy/opa_client.py` (docstring only — OPA input contract)
- `app/web/routes.py`
- `app/web/templates/settings.html`
- `tests/T23_rule_editor/` (conftest, test_control_toggles.py, test_control_parameters.py, test_settings_persistence.py)
- `tests/T08_settings/test_settings_store.py` (minimal regression update)

## Scope check
- `email.rego` was not modified, which is fine: the shared `control_enabled()` helper
  already lives in `common.rego` and is called by `payment.rego` and `email.rego`
  identically, so extending it in one place covers both files without touching
  `email.rego`'s rule bodies.
- `common.rego` was touched even though the architect brief's allowed-files list named
  only `payment.rego`/`email.rego`. This is the correct location for the change since
  `control_enabled()` is defined there and shared by both policy files — duplicating the
  logic into each file to avoid touching common.rego would have been worse. No other
  control logic in `common.rego` was altered.
- `app/policy/opa_client.py` was touched only to update the OPA input-contract docstring
  describing the new `control_enabled`/`parameters` keys under `input.config`. No
  decision logic was added there — consistent with "Python may assemble config but must
  not decide."
- `tests/T08_settings/test_settings_store.py` was updated to keep an existing T08
  regression test correct after extending `to_policy_config()`'s output shape; `tests/`
  is always an allowed location per AGENTS.md.

## Functional review
- `control_enabled(id)` in `common.rego` now reads
  `object.get(object.get(input.config, "control_enabled", {}), id, true)` — defaults to
  enabled when unset, and still excludes `proposed` controls (FIN-PAY-004 guard intact).
- `payment.rego` reads `FIN-PAY-002`'s threshold via `fin_pay_002_amount_threshold`,
  sourced from `input.config.parameters["FIN-PAY-002"].amount_threshold` with a safe
  default of 500 — matches pre-T23 hardcoded behaviour exactly when unset.
- `opa/data/controls.json` adds `"parameters": {"amount_threshold": 500}` to
  `FIN-PAY-002` as metadata/default only; runtime overrides flow through the DB-backed
  settings store, not by editing this file at runtime.
- `SettingsStore` adds `control_enabled` and `parameters` columns (SQLite + Postgres),
  migrates existing rows via `_add_column_if_missing_sqlite` / `ADD COLUMN IF NOT EXISTS`,
  and exposes `update_control_enabled()` / `update_control_parameter()`. Both feed
  straight into `to_policy_config()` → `input.config`, so OPA/Rego remains the decision
  maker — no Python post-filtering of `triggered_controls` observed anywhere in the diff.
- `routes.py` adds `/settings/control-enabled` and `/settings/control-parameter` POST
  routes, both redirecting back to `/settings` with a confirmation banner. The Scenario 5
  impact panel (`_build_impact_panel`) was updated to take the full policy config instead
  of just `control_modes`, preserving the T19 threshold-preview behaviour while picking up
  T23's new config keys.
- `settings.html` adds an "Enabled" toggle column and a "Parameter" column (amount
  threshold input, FIN-PAY-002 only) below the existing confidence-threshold section,
  inline (no modal), each save banner says "takes effect on the next evaluation — no
  restart needed" — matches the non-technical-confirmation requirement.

## Test review
- `tests/T23_rule_editor/` covers the full PM/BA test brief: disable/re-enable
  FIN-PAY-002, threshold 500→1000→500, default-seed preservation, persistence across a
  simulated store reinitialisation, settings-page rendering of all controls, and the T19
  confidence-threshold regression — all via the real OPA/Rego path per `conftest.py`
  (spins up a real `opa` binary or uses `OPA_URL`; skips with a clear message if neither
  is available, never substitutes a hand-written decision).
- Local run in this sandbox (no Docker/OPA binary available): `8 passed, 20 skipped` —
  the 8 passing are non-OPA-dependent (settings-store unit-level persistence checks); the
  20 skipped are exactly the real-OPA acceptance tests that require an OPA binary or
  `OPA_URL`, which this sandbox cannot provide. **Recommend re-running with
  `docker compose up -d opa` or a local `opa` binary before sign-off** to exercise the
  Rego-backed assertions end-to-end (the primary ledger verify step depends on this).

## Verdict
Implementation matches the architect brief and test brief. No decision logic leaked into
Python; disabled controls are genuinely skipped inside Rego; FIN-PAY-002's threshold is
runtime-configurable with a safe default; FIN-PAY-004's proposed-guard is preserved;
persistence is DB-backed and migrates existing rows. Outstanding action before marking
`DONE`: run the skipped OPA-backed tests in an environment with OPA available (per the
ledger's Verify step) to get a green, non-skipped pytest run.
