# Test Brief — T23: Policy rule editor (extends T19)

## Spec references
- `MASTER_SPEC.md`: §5.4 Decision schema (`threshold_used`), §6 Control library + decision precedence, §7 scenario table (especially Scenario 2 and Scenario 5), §8A item 7 Settings, §12 acceptance criteria for live runtime settings.
- `TASK_LEDGER.md`: T23 goal, files, key notes, done criteria, verify step, and reviewer focus.
- `briefs/T23_architect_brief.md`: allowed files, non-negotiables, OPA input/config expectations, and task-specific verification notes.

## Target test location
- Folder: `tests/T23_rule_editor/`
- Suggested files:
  - `test_control_toggles.py` — covers control enabled/disabled behaviour, FIN-PAY-002 demo path, and disabled controls being skipped by OPA rather than post-filtered in Python.
  - `test_control_parameters.py` — covers runtime FIN-PAY-002 amount-threshold changes, default seed values, and preservation of T19 confidence-threshold behaviour.
  - `test_settings_persistence.py` — covers settings page/form persistence across refresh/reload and app restart-equivalent store reinitialisation.

## Test cases

### test_fin_pay_002_disabled_allows_scenario_2
- **Traces to:** `TASK_LEDGER.md` T23 done criteria 1-2; `MASTER_SPEC.md` §6 FIN-PAY-002; §7 Scenario 2; §8A Settings.
- **Input:** Use the real pipeline/OPA path for Scenario 2: payment of £850 for `CUST-100` with no approval. Set runtime control config so `FIN-PAY-002.enabled = false`; leave all other controls at default enabled state and amount threshold at 500.
- **Expected outcome:** Decision is exactly `allow`; `FIN-PAY-002` is absent from `triggered_controls`; no required approval role is returned; the result is produced by the normal OPA-backed decision path.
- **Notes:** This must use real OPA/Rego evaluation. Do not mock OPA or simulate a Python-side filtered decision. Payment path must keep `evidence.evaluated = false`.

### test_fin_pay_002_reenabled_restores_scenario_2_escalation
- **Traces to:** `TASK_LEDGER.md` T23 done criteria 3; `MASTER_SPEC.md` §6 FIN-PAY-002; §7 Scenario 2.
- **Input:** First disable `FIN-PAY-002` and run/evaluate Scenario 2, then re-enable `FIN-PAY-002` without restarting the app. Re-run/evaluate the same Scenario 2 payment of £850 for `CUST-100` with no approval.
- **Expected outcome:** First evaluation returns `allow`; second evaluation returns `escalate`; `control_id` is `FIN-PAY-002`; `triggered_controls` includes `FIN-PAY-002`; `required_approval_role` is `finance_supervisor`; `threshold_used` still reflects the configured confidence threshold for the decision record.
- **Notes:** The second result proves changes take effect on the next evaluation and require no restart.

### test_fin_pay_002_threshold_1000_allows_scenario_2
- **Traces to:** `TASK_LEDGER.md` T23 done criteria 4; `MASTER_SPEC.md` §6 FIN-PAY-002 threshold trigger; §7 Scenario 2.
- **Input:** Set `FIN-PAY-002.enabled = true` and set `FIN-PAY-002.parameters.amount_threshold = 1000`. Run/evaluate Scenario 2 payment of £850 for `CUST-100` with no approval.
- **Expected outcome:** Decision is exactly `allow`; `FIN-PAY-002` is absent from `triggered_controls`; no `finance_supervisor` approval is required.
- **Notes:** This must verify Rego reads the configured runtime threshold from `input.config.parameters["FIN-PAY-002"].amount_threshold` or the implementation's explicit equivalent config path, with safe defaults. Do not accept hardcoded-500 behaviour.

### test_fin_pay_002_threshold_500_restores_escalation
- **Traces to:** `TASK_LEDGER.md` T23 done criteria 5; `MASTER_SPEC.md` §6 FIN-PAY-002; §7 Scenario 2.
- **Input:** After setting threshold to 1000 and observing `allow`, set `FIN-PAY-002.parameters.amount_threshold = 500`. Re-run/evaluate Scenario 2 payment of £850 for `CUST-100` with no approval.
- **Expected outcome:** Decision is exactly `escalate`; `control_id` is `FIN-PAY-002`; `triggered_controls` includes `FIN-PAY-002`; `required_approval_role` is `finance_supervisor`.
- **Notes:** This is the core buyer demo beat: policy configuration changes observable behaviour without code changes or restart.

### test_all_controls_have_persisted_enabled_flags_and_ui_rows
- **Traces to:** `TASK_LEDGER.md` T23 done criterion 1 and UI notes; `MASTER_SPEC.md` §6 control library; §8A Settings.
- **Input:** Load/render the settings page after seeding defaults. Inspect the controls section and the persisted runtime config for every control defined in `opa/data/controls.json`.
- **Expected outcome:** Every control from `controls.json` has a persisted enabled/disabled value and a settings-page row showing ID, plain-English name/purpose, enabled toggle, and current mode. `FIN-PAY-002` additionally exposes an inline amount-threshold input. The existing confidence-threshold editor remains present.
- **Notes:** This is a functional UI acceptance test. It may use FastAPI/TestClient plus the real settings store. It should not require browser automation unless the current suite already uses it.

### test_settings_page_save_persists_control_toggle_and_parameter_after_refresh
- **Traces to:** `TASK_LEDGER.md` T23 done criterion 6; `MASTER_SPEC.md` §8A Settings.
- **Input:** Submit settings-page form data that disables `FIN-PAY-002` and sets its amount threshold to 1000. Then request the settings page again using the same DB-backed settings store.
- **Expected outcome:** The settings page shows `FIN-PAY-002` disabled and amount threshold 1000 after refresh; the next Scenario 2 evaluation returns `allow`.
- **Notes:** This covers page-refresh persistence. Use the real DB-backed settings path used by the application, not an in-memory-only substitute, unless the existing test harness provides an isolated test database with the same persistence semantics.

### test_control_settings_survive_store_reinitialisation
- **Traces to:** `TASK_LEDGER.md` T23 verify step restart persistence; §8A Settings persistence.
- **Input:** Save settings with `FIN-PAY-002.enabled = false` and `amount_threshold = 1000`. Recreate/reinitialise the application settings store against the same underlying database, simulating an app restart. Load settings and evaluate Scenario 2.
- **Expected outcome:** Loaded settings still show `FIN-PAY-002.enabled = false` and `amount_threshold = 1000`; Scenario 2 evaluates to `allow`. Restore defaults as test cleanup if the harness shares state.
- **Notes:** This does not need to restart Docker inside pytest; it must exercise equivalent DB-backed persistence by constructing a fresh store/client instance using the same persisted data.

### test_default_seed_config_preserves_existing_policy_behaviour
- **Traces to:** `TASK_LEDGER.md` T23 settings-store notes; `MASTER_SPEC.md` §6, §7, §12.
- **Input:** Start from an empty settings row/database and allow defaults to seed. Evaluate Scenario 2 and inspect runtime control config.
- **Expected outcome:** All currently active, non-proposed controls are enabled by default; `FIN-PAY-002.parameters.amount_threshold` defaults to 500; confidence threshold defaults to 0.75; Scenario 2 returns `escalate` to `finance_supervisor`.
- **Notes:** `FIN-PAY-004` remains proposed and must not accidentally become an active scenario-affecting control. If `FIN-PAY-004` appears in the UI/config, the test should assert its proposed/disabled semantics preserve existing scenario outcomes.

### test_t19_confidence_threshold_behaviour_still_works
- **Traces to:** `MASTER_SPEC.md` §6 configurable `HIGH_CONFIDENCE`; §7 Scenario 5; §12 acceptance criterion for threshold change; T23 architect brief preservation of T19 behaviour.
- **Input:** Use the real email Scenario 5 path with external recipient and deterministic nuance stub confidence 0.62. First evaluate with confidence threshold 0.75. Then set threshold to 0.60 through the settings store/UI path and re-evaluate without restart.
- **Expected outcome:** At threshold 0.75, Scenario 5 returns `escalate` with `control_id = COMM-EMAIL-002`, `required_approval_role = vulnerable_customer_team`, and `threshold_used = 0.75`. At threshold 0.60, Scenario 5 returns `allow_with_logging` and `threshold_used = 0.60`.
- **Notes:** This must use real OPA/Rego and the deterministic nuance stub path. Do not mock semantic evidence or policy decisions. This is in T23 scope only as a regression guard that the rule editor did not break T19 threshold settings.

### test_disabled_email_control_is_skipped_by_opa
- **Traces to:** `TASK_LEDGER.md` T23 OPA integration notes; `MASTER_SPEC.md` §6 COMM-EMAIL controls; non-negotiable that OPA/Rego makes decisions.
- **Input:** Disable `COMM-EMAIL-002` in runtime config. Evaluate Scenario 5 with threshold 0.75 and the normal deterministic evidence that would otherwise trigger `COMM-EMAIL-002`.
- **Expected outcome:** `COMM-EMAIL-002` is absent from `triggered_controls`; decision falls through according to the remaining enabled controls and evidence, expected `allow_with_logging` if personal data logging control applies, otherwise `allow` if the fixture has no personal data trigger. The decision must not be `escalate` due to `COMM-EMAIL-002`.
- **Notes:** This guards the generic enabled-toggle behaviour beyond FIN-PAY-002. It must be driven by real OPA config input, not Python post-processing.

### test_settings_confirmation_mentions_next_evaluation
- **Traces to:** `TASK_LEDGER.md` T23 UI notes; `MASTER_SPEC.md` §8A Settings tone/accessibility.
- **Input:** Submit a valid settings update from the settings page.
- **Expected outcome:** The response/page shows a clear confirmation message that changes take effect on the next evaluation. The message should be understandable to a non-technical risk user.
- **Notes:** This is a UI acceptance check, not a styling snapshot. Assert meaningful text rather than brittle markup.

## Coverage checklist
- [x] Happy path covered: default Scenario 2 escalation, disable-to-allow, re-enable-to-escalate, threshold 1000-to-allow, threshold 500-to-escalate.
- [x] Error/edge cases covered: default seeding, persistence across refresh/store reinitialisation, proposed FIN-PAY-004 guard, T19 threshold regression.
- [x] Spec non-negotiables verified: OPA/Rego remains the judge; disabled controls skipped in Rego; Python does not post-filter decisions; payment path does not invoke semantic layer; scenario outcomes remain stable unless settings are deliberately changed.
- [x] Real dependencies flagged: tests that evaluate policy decisions must use real OPA/Rego; persistence tests must use the real DB-backed settings path or an equivalent isolated test database; semantic regression must use the real deterministic evidence pipeline.

## Gaps or ambiguities
- The ledger says “one or two editable parameters per control” but then narrows T23 to FIN-PAY-002 amount threshold plus the existing T19 confidence threshold. Treat only those two as editable unless `MASTER_SPEC.md` is updated.
- The exact expected fallback for Scenario 5 with `COMM-EMAIL-002` disabled depends on whether the implemented fixture/evidence also triggers `COMM-EMAIL-003`; the test should assert that `COMM-EMAIL-002` does not trigger and that the result follows remaining enabled OPA controls, not a Python override.
- The task requires restart persistence. In pytest, a full Docker restart is likely better left to manual QA; the automated acceptance test should simulate restart by reinitialising the app/settings store against the same database.
