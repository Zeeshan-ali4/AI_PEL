# Test Brief — T19: Settings page (DEMO-READY milestone)

## Spec references
- MASTER_SPEC.md: §6 control library and decision precedence; §7 Scenario 5 confidence and expected default outcome; §8 enforcement modes; §8A item 7 Settings page; §11 pipeline loads runtime settings before OPA; §12 acceptance criteria for the live Scenario 5 threshold flip.
- TASK_LEDGER.md: T19 goal, dependencies, allowed files, Done when, Verify step, and Reviewer focus.
- briefs/T19_architect_brief.md: T19 allowed files, implementation objective, non-negotiables, and recommended programmatic checks.

## Target test location
- Folder: `tests/T19_settings_ui/`
- Suggested files:
  - `__init__.py` — package marker for the T19 test folder.
  - `test_settings_page.py` — covers rendering the Settings page, displaying the current threshold, displaying the Scenario 5 live impact panel, validating threshold form submissions, and showing per-control mode selectors.
  - `test_settings_persistence.py` — covers posting threshold and per-control mode updates, persistence on reload, and immediate effect on a subsequent Scenario 5 run through the existing pipeline/route path.

## Test cases

### test_settings_page_renders_current_threshold_and_impact_panel
- **Traces to:** MASTER_SPEC.md §8A item 7; MASTER_SPEC.md §7 Scenario 5; TASK_LEDGER.md T19 Goal.
- **Input:** Start the app test client with the settings store seeded to the default high-confidence threshold `0.75`, then request `GET /settings` (or the existing settings route if named differently by prior UI work).
- **Expected outcome:** Response status is `200`; the HTML contains the current threshold value `0.75`; the live impact panel references Scenario 5 and its fixed confidence `0.62`; the panel states that at the current threshold Scenario 5 escalates; the page copy makes clear that risk owns/tunes the policy.
- **Notes:** This is a functional UI test. It should assert user-visible text/fields, not private helper names.

### test_settings_page_shows_lower_threshold_allow_with_logging_impact
- **Traces to:** MASTER_SPEC.md §6 threshold semantics; MASTER_SPEC.md §8A item 7 live impact panel; MASTER_SPEC.md §12 threshold flip acceptance criterion.
- **Input:** Seed or update the settings store so `high_confidence_threshold = 0.60`, then request `GET /settings`.
- **Expected outcome:** Response status is `200`; the live impact panel states that Scenario 5 with confidence `0.62` would resolve to `allow_with_logging` at threshold `0.60`; the page must not continue to describe Scenario 5 as escalating under the current threshold.
- **Notes:** The panel may also include explanatory copy comparing `0.75` and `0.60`, but assertions should verify the current-threshold outcome is accurate.

### test_post_threshold_update_persists_and_renders_on_reload
- **Traces to:** MASTER_SPEC.md §4 DB-backed runtime settings row; MASTER_SPEC.md §8A item 7 persistence; TASK_LEDGER.md T19 Done when.
- **Input:** Submit the Settings threshold form with `high_confidence_threshold=0.60`, then request `GET /settings` again using the same backing settings store/database.
- **Expected outcome:** The POST succeeds with an expected redirect or `200` response according to existing UI conventions; the settings store value is updated to `0.60`; the reload renders `0.60` as the current value and shows the Scenario 5 allow-with-logging impact.
- **Notes:** Use the real settings store/database integration already used by the app test harness. Do not replace settings persistence with a mock.

### test_invalid_threshold_submission_is_rejected_without_overwriting_existing_value
- **Traces to:** MASTER_SPEC.md §6 configurable threshold; MASTER_SPEC.md §8A item 7 editable settings; TASK_LEDGER.md T19 Reviewer focus on accurate risk-owned policy configuration.
- **Input:** With an existing valid threshold such as `0.75`, submit an invalid threshold value outside the meaningful confidence range, for example `-0.1` or `1.5`.
- **Expected outcome:** The UI rejects the update with a visible validation error or equivalent non-success response; the persisted threshold remains the previous valid value; a subsequent `GET /settings` still renders the previous valid threshold and matching Scenario 5 impact.
- **Notes:** This protects the demo from accepting impossible confidence thresholds. If existing settings-store validation defines a stricter range or error shape, tests should follow that contract while preserving the user-facing rejection assertion.

### test_per_control_modes_render_for_each_known_control
- **Traces to:** MASTER_SPEC.md §6 control library; MASTER_SPEC.md §8 enforcement modes; MASTER_SPEC.md §8A item 7 editable per-control mode; TASK_LEDGER.md T19 Goal.
- **Input:** Request `GET /settings` with controls available from `opa/data/controls.json` and settings seeded with current per-control modes.
- **Expected outcome:** The page renders one editable mode selector/control for each existing control ID; each selector offers exactly the known modes `shadow`, `soft`, and `full`; user-visible control IDs include at minimum `FIN-PAY-001`, `FIN-PAY-002`, `FIN-PAY-003`, `FIN-PAY-004`, `COMM-EMAIL-001`, `COMM-EMAIL-002`, and `COMM-EMAIL-003` when those controls are present in controls metadata.
- **Notes:** This test should not hard-code framework mappings beyond checking that the Settings page is sourced from the same known control list used elsewhere. If FIN-PAY-004 is disabled/proposed in metadata but still displayed by the dashboard, the Settings page should follow that existing dashboard convention.

### test_post_per_control_mode_update_persists_and_renders_on_reload
- **Traces to:** MASTER_SPEC.md §8 enforcement modes; MASTER_SPEC.md §8A item 7 persistence; TASK_LEDGER.md T19 Goal.
- **Input:** Submit the Settings per-control mode form changing a representative control, such as `COMM-EMAIL-002`, to `shadow`, then request `GET /settings` again using the same backing settings store/database.
- **Expected outcome:** The POST succeeds with the app's expected redirect or success response; the settings store reflects the new mode for `COMM-EMAIL-002`; the settings reload shows `shadow` selected for that control and leaves unrelated control modes unchanged.
- **Notes:** Use at least one email control tied to Scenario 5 so the test supports the milestone story, but do not alter OPA policy logic.

### test_threshold_change_takes_effect_for_scenario_5_without_restart
- **Traces to:** MASTER_SPEC.md §6 threshold passed into OPA input and echoed as `threshold_used`; MASTER_SPEC.md §7 Scenario 5; MASTER_SPEC.md §11 runtime settings loaded before OPA; MASTER_SPEC.md §12 acceptance criterion; TASK_LEDGER.md T19 Done when and Verify step.
- **Input:** In one running app/test-client session, submit threshold `0.60` through the Settings UI, then run Scenario 5 through the existing scenario execution route/API used by the UI (for example `POST /run/5` or the established route from earlier tasks).
- **Expected outcome:** Scenario 5 returns/renders decision `allow_with_logging` without restarting the app; the decision includes `threshold_used` equal to `0.60` (allowing normal numeric formatting such as `0.6`); the response does not show the default `0.75` threshold.
- **Notes:** This is the critical demo-ready acceptance test. It must exercise the real pipeline/OPA path and real settings store. OPA must be a real instance when the project test harness supports integration tests; do not mock policy decisions.

### test_default_threshold_keeps_scenario_5_escalated
- **Traces to:** MASTER_SPEC.md §7 Scenario 5 expected default outcome; MASTER_SPEC.md §6 default-to-human and threshold semantics; TASK_LEDGER.md T19 Reviewer focus.
- **Input:** With default threshold `0.75`, run Scenario 5 through the existing scenario execution route/API.
- **Expected outcome:** Scenario 5 resolves to `escalate`, identifies `COMM-EMAIL-002`, and routes to `vulnerable_customer_team`; `threshold_used` is `0.75`.
- **Notes:** This guards against the Settings page implementation accidentally changing baseline scenario outcomes or moving decision logic out of OPA.

## Coverage checklist
- [ ] Happy path covered: Settings page renders current threshold, Scenario 5 impact, and per-control mode controls.
- [ ] Error/edge cases covered: invalid threshold submissions are rejected and do not overwrite valid settings.
- [ ] Spec non-negotiables verified: threshold remains runtime-configurable, Scenario 5 flips only through settings/OPA semantics, and per-control modes remain within `shadow`, `soft`, `full`.
- [ ] Real dependencies flagged: persistence tests must use the real settings store/database integration; Scenario 5 flip tests must exercise the real pipeline/OPA path where supported, not mocked policy decisions.

## Gaps or ambiguities
- The ledger lists allowed files as `app/web/templates/settings.html`, routes, and `tests/T19_settings_ui/`; the Architect Brief resolves `routes` to `app/web/routes.py`. Tests should follow that scope.
- The exact Settings URL and scenario-run URL depend on routes established by T14–T18. Implementer should use the existing route names/paths rather than introducing duplicate endpoints.
- The spec does not define the exact validation response for invalid thresholds. The test should assert user-visible rejection and unchanged persistence, while allowing either a `400` response or a rendered form error if that matches existing UI conventions.
