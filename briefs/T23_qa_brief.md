# QA Brief — T23: Policy rule editor (extends T19)

## Environment
- Real OPA binary (v1.18.0, static linux/amd64 build) obtained for this QA pass and run on PATH so `tests/T23_rule_editor/conftest.py` exercises the genuine Rego-backed acceptance path rather than skipping (the reviewer's sandbox had no `opa` binary and 20 of these tests were skipped — that gap is now closed).
- No Docker daemon available in this sandbox, so the full `docker compose` stack could not be brought up; OPA was run as a standalone process per the conftest's existing fallback mechanism, against the real `opa/policies` + `opa/data` bundle. Postgres-backed persistence was exercised via the existing SQLite-equivalent test harness used by `tests/T23_rule_editor/test_settings_persistence.py`.

## Test run results

### tests/T23_rule_editor/ (target suite)
`13 passed` — zero skipped, zero failed. All real-OPA acceptance tests in the PM/BA test brief executed against genuine Rego evaluation:
- `test_fin_pay_002_disabled_allows_scenario_2`
- `test_fin_pay_002_reenabled_restores_scenario_2_escalation`
- `test_disabled_email_control_is_skipped_by_opa`
- `test_settings_control_enabled_route_persists_and_takes_effect`
- `test_default_seed_config_preserves_existing_policy_behaviour`
- `test_fin_pay_002_threshold_1000_allows_scenario_2`
- `test_fin_pay_002_threshold_500_restores_escalation`
- `test_settings_control_parameter_route_persists_and_takes_effect`
- `test_t19_confidence_threshold_behaviour_still_works`
- `test_all_controls_have_persisted_enabled_flags_and_ui_rows`
- `test_settings_page_save_persists_control_toggle_and_parameter_after_refresh`
- `test_control_settings_survive_store_reinitialisation`
- `test_settings_confirmation_mentions_next_evaluation`

All 9 test-brief-named scenarios are covered 1:1 (some implemented as combined assertions within the same test function); no test brief case is missing coverage.

### Regression suites named in the architect brief's task-specific checks
- `tests/T19_settings_ui/`, `tests/T10_policy/`, `tests/T08_settings/` — `27 passed`, 0 failed. T19's threshold-flip demo and T10's full control-precedence behaviour are unaffected by the T23 changes.

### Full repo suite (`tests/`)
`232 passed, 2 skipped, 3 failed, 4 errors` in one full run. All failures/errors are pre-existing and out of T23 scope, confirmed below — none touch files T23 is allowed to change:
- `tests/T14_dashboard/test_dashboard_counts.py::test_dashboard_auditable_surface_counter_explains_gate_not_agent_logging` and `tests/T14_dashboard/test_dashboard_rendering.py::test_landing_page_renders_shared_dashboard_layout` — fail identically when checked out at the pre-T23 merge commit (`d1b440e`, the T22 merge). `dashboard.html` has no literal "Controls" heading and is missing the exact "complete, unauditable agent transcript" string the test expects. T23 does not touch `dashboard.html`. Pre-existing T14 defect, not a T23 regression.
- `tests/test_policy_decisions.py` (4 errors) — hardcodes `OPA_URL=http://opa:8181`, the docker-compose service hostname, and fails fast with `Name or service not known` outside a compose network. This is the T20 task's file (T20 status is still `To do` in the ledger) and is environment-dependent by design; not a T23 file and not actionable from this sandbox.
- `tests/T22_event_feed/test_pipeline_trace.py::test_existing_run_routes_still_return_compatible_results` — failed only under full-suite resource contention (many OPA subprocesses spun up across the session in parallel); reran in isolation immediately after and it passed cleanly. Not a real regression; flaky under load, not specific to T23.

## Scope/file check against ledger + architect brief
Diff for this task touches only: `app/settings_store.py`, `opa/data/controls.json`, `opa/policies/common.rego` (shared `control_enabled()` helper used by both `payment.rego` and `email.rego`, reviewer-justified), `opa/policies/payment.rego`, `app/policy/opa_client.py` (docstring only), `app/web/routes.py`, `app/web/templates/settings.html`, `tests/T23_rule_editor/`, plus a minimal `tests/T08_settings/` regression fix. All within the allowed list or the always-allowed `tests/` exception. No schema, directory layout, or scenario-outcome changes.

## Verify step (TASK_LEDGER.md) — confirmed against real OPA
1. Disable `FIN-PAY-002` → Scenario 2 → `allow`. **Confirmed** (`test_fin_pay_002_disabled_allows_scenario_2`).
2. Re-enable `FIN-PAY-002` → Scenario 2 → `escalate`. **Confirmed** (`test_fin_pay_002_reenabled_restores_scenario_2_escalation`).
3. Threshold → 1000 → Scenario 2 → `allow`. **Confirmed** (`test_fin_pay_002_threshold_1000_allows_scenario_2`).
4. Threshold → 500 → Scenario 2 → `escalate`. **Confirmed** (`test_fin_pay_002_threshold_500_restores_escalation`).
5. Restart-equivalent persistence. **Confirmed** (`test_control_settings_survive_store_reinitialisation`, store reinitialised against the same underlying DB).

Additional non-negotiables checked directly in the Rego/diff: disabled controls are skipped inside `common.rego`'s `control_enabled()` (no Python post-filtering of `triggered_controls` anywhere in the diff); `FIN-PAY-002`'s threshold is read from `input.config.parameters["FIN-PAY-002"].amount_threshold` with a safe default of 500; `FIN-PAY-004`'s proposed-guard is untouched; payment scenarios still report `evidence.evaluated=false`.

## Verdict
**PASS.** The reviewer's one outstanding action — re-running the OPA-dependent tests with a real `opa` binary available — has been completed in this QA pass: 13/13 real-Rego acceptance tests pass with zero skips. Combined with clean T19/T10/T08 regression runs and a full-suite run whose only failures/errors are pre-existing, out-of-scope (T14, T20-pending) or load-induced flakes unrelated to T23, this task meets every "Done when" criterion in `TASK_LEDGER.md` and is ready to be marked `DONE`.
