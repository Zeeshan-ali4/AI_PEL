# Test Brief — T14: base.html + control dashboard (landing)

## Spec references
- MASTER_SPEC.md: §6 control library and framework mappings; §8 enforcement modes; §8A item 1 control dashboard; §9 auditable-surface counter; §11 pipeline wiring for run records; §12 acceptance criteria relevant to the landing surface.
- TASK_LEDGER.md: T14 goal, files, Done when, Verify, and Reviewer focus.
- Architect brief: `briefs/T14_architect_brief.md` was not present when this PM/BA brief was written. The Implementer/Reviewer should reconcile this brief with the Architect brief if one is added later before coding starts.

## Target test location
- Folder: `tests/T14_dashboard/`
- Suggested files:
  - `test_dashboard_rendering.py` — covers dashboard page availability, shared layout, control table content, framework chips, current modes, and board-ready language.
  - `test_dashboard_counts.py` — covers live counts and auditable-surface counter updating from real audit records after scenario runs.
  - `test_dashboard_mode_toggle.py` — covers enforcement-mode toggle persistence through the settings store and validation of allowed modes.

## Test cases

### test_landing_page_renders_shared_dashboard_layout
- **Traces to:** MASTER_SPEC.md §8A item 1; TASK_LEDGER.md T14 goal and Done when.
- **Input:** Start the FastAPI app with the T14 routes registered and request `GET /` using the application test client.
- **Expected outcome:** Response status is 200 and response HTML contains a complete landing dashboard inside the shared `base.html` layout. It must include a clear page title such as “Control dashboard” or “Assurance dashboard”, top-level navigation/header structure from the base template, and visible dashboard sections for controls, enforcement mode, live counts, and auditable surface.
- **Notes:** This is an acceptance test of the rendered user-facing page, not a template helper unit test. It should parse the returned HTML rather than assert only raw status code.

### test_dashboard_lists_every_enabled_control_from_controls_json
- **Traces to:** MASTER_SPEC.md §6; MASTER_SPEC.md §8A item 1; TASK_LEDGER.md T14 Done when.
- **Input:** Request `GET /` with the repository `opa/data/controls.json` as the control source.
- **Expected outcome:** The rendered control table includes every enabled control ID from `controls.json`: `FIN-PAY-001`, `FIN-PAY-002`, `FIN-PAY-003`, `FIN-PAY-004`, `COMM-EMAIL-001`, `COMM-EMAIL-002`, and `COMM-EMAIL-003`. For each row, the page displays the control ID, the plain-English description/purpose from `controls.json`, the tier, current mode, framework mappings, and live decision counts.
- **Notes:** The test should fail if controls are hard-coded incompletely or if an enabled control in `controls.json` is omitted. It may assert against the current known IDs plus compare the number of rendered rows to the enabled controls in the JSON file.

### test_dashboard_renders_tiers_as_plain_english_board_labels
- **Traces to:** MASTER_SPEC.md §8A item 1; MASTER_SPEC.md §6 decision tiers; TASK_LEDGER.md Reviewer focus.
- **Input:** Request `GET /`.
- **Expected outcome:** Control tiers render as board-readable labels, not raw internal jargon only: `FIN-PAY-001` appears as the Prohibited/blocking tier; `FIN-PAY-002`, `FIN-PAY-003`, `FIN-PAY-004`, `COMM-EMAIL-001`, and `COMM-EMAIL-002` appear as Escalate/human-decision tier controls; `COMM-EMAIL-003` appears as a Log/allow-with-logging tier control.
- **Notes:** This verifies the dashboard “reads like something shown to a board.” Exact CSS classes are not in scope for PM/BA acceptance; focus on visible text semantics.

### test_dashboard_framework_chips_match_control_metadata
- **Traces to:** MASTER_SPEC.md §6 framework mappings; MASTER_SPEC.md §8A item 1; TASK_LEDGER.md Reviewer focus.
- **Input:** Request `GET /`.
- **Expected outcome:** Each control row renders all framework mappings from `opa/data/controls.json` as visible chip-like labels or equivalent separated visual tokens. Required examples include `Internal Fraud & Financial Crime Policy` for `FIN-PAY-001`, `Internal Delegated-Authority Policy` for `FIN-PAY-002`, `UK GDPR Art.9 / DPA 2018` for `COMM-EMAIL-001`, and `UK GDPR Art.5(2) accountability` plus `Record-keeping control RK-03` for `COMM-EMAIL-003`.
- **Notes:** The test should not accept framework mappings being collapsed into an unrelated generic “compliance” label. Use the real metadata file; do not mock framework mappings.

### test_dashboard_displays_current_modes_from_settings_store
- **Traces to:** MASTER_SPEC.md §8; MASTER_SPEC.md §8A item 1; TASK_LEDGER.md T14 Done when.
- **Input:** Persist mixed control modes in the settings store, for example `FIN-PAY-001=full`, `FIN-PAY-002=soft`, and `COMM-EMAIL-003=shadow`, then request `GET /`.
- **Expected outcome:** The corresponding control rows show the persisted current modes exactly (`full`, `soft`, `shadow`) rather than defaulting all rows to a static value. Modes must come from the runtime settings row.
- **Notes:** This should exercise the real settings store path available in the app test configuration. A temporary SQLite settings URL is acceptable if it uses the production `SettingsStore` implementation; do not replace the store with a mock object.

### test_dashboard_live_counts_initially_show_zero_when_audit_store_empty
- **Traces to:** MASTER_SPEC.md §8A item 1; MASTER_SPEC.md §9; TASK_LEDGER.md T14 Done when.
- **Input:** Use an empty audit store, then request `GET /`.
- **Expected outcome:** Each control row renders live count fields for allowed, escalated, blocked, and logged outcomes, with zero values when no audit records exist. The auditable-surface counter is present and shows zero evaluated gate records, or an equivalent explicit empty-state count.
- **Notes:** Counts must be visible, not only present in hidden JSON. The test should use the real audit store schema/path configured for tests; do not mock counts.

### test_dashboard_live_counts_update_after_running_scenarios
- **Traces to:** MASTER_SPEC.md §8A item 1; MASTER_SPEC.md §9; MASTER_SPEC.md §11; TASK_LEDGER.md T14 Verify.
- **Input:** In a clean test data store, run at least two canonical scenarios through `POST /run/{scenario_id}` before requesting `GET /`; use scenario 3 to produce a `block`/`FIN-PAY-001` record and scenario 6 to produce an `allow_with_logging`/`COMM-EMAIL-003` record.
- **Expected outcome:** After refresh, the dashboard shows increased real counts for the triggered controls: `FIN-PAY-001` has a blocked count incremented by at least 1, `COMM-EMAIL-003` has a logged or allow-with-logging count incremented by at least 1, and the auditable-surface counter increments to reflect the action evaluation records written by the pipeline.
- **Notes:** This is the core T14 acceptance test. It must use the real pipeline/audit-store integration already delivered by T13; do not seed fake dashboard-only counters. If the suite uses Docker, OPA/Postgres must be real service instances. If it uses local SQLite test stores, they must still be the real store implementations.

### test_dashboard_enforcement_mode_toggle_persists_selected_mode
- **Traces to:** MASTER_SPEC.md §8 single visible toggle; MASTER_SPEC.md §8A item 1; TASK_LEDGER.md T14 Done when and Verify.
- **Input:** Request `GET /`, submit the dashboard enforcement-mode toggle to set a valid mode such as `full`, then request `GET /` again and read settings through `SettingsStore`.
- **Expected outcome:** The submitted mode persists in the settings store and the refreshed dashboard shows `full` as the selected/current mode. If the T14 implementation applies one global dashboard toggle across all controls, every control mode in the settings row should be `full`; if it exposes per-control controls already supported by the settings store, the test should assert the specific submitted control mode persisted.
- **Notes:** The task wording calls for “the enforcement-mode toggle” while the settings model stores per-control modes. This acceptance test allows either a global toggle that updates all current T14 modes or a per-control toggle, as long as the visible toggle persists via `SettingsStore` and affects what the dashboard displays.

### test_dashboard_rejects_invalid_enforcement_mode_submission
- **Traces to:** MASTER_SPEC.md §8 allowed modes `shadow`, `soft`, `full`; TASK_LEDGER.md T14 mode-toggle persistence.
- **Input:** Submit the dashboard mode update endpoint/form with an invalid mode such as `observe` or `disabled`.
- **Expected outcome:** The app rejects the submission with a 4xx response or a validation error message and does not change the persisted settings row. A subsequent `GET /` still shows the previously persisted valid mode.
- **Notes:** This covers the main edge case for the UI control. The Implementer should choose the route/form shape; the test should target that public UI/API contract, not a private helper.

### test_dashboard_auditable_surface_counter_explains_gate_not_agent_logging
- **Traces to:** MASTER_SPEC.md §9; MASTER_SPEC.md §8A item 1; TASK_LEDGER.md T14 goal.
- **Input:** Request `GET /` after zero or more action-evaluation records exist.
- **Expected outcome:** The page includes an auditable-surface counter with visible wording that communicates the gate logs proposed consequential actions rather than all agent thoughts/tokens. It should display the current count of gate evaluations/records and should not imply full agent transcript logging.
- **Notes:** This is a buyer-facing assurance requirement. Avoid testing exact marketing copy, but assert for key concepts such as “auditable surface”, “gate”, “proposed actions”, or equivalent visible wording.

## Coverage checklist
- [x] Happy path covered: dashboard renders, controls load, metadata displays, modes display.
- [x] Error/edge cases covered: empty audit store and invalid mode submission.
- [x] Spec non-negotiables verified: controls and framework mappings come from policy metadata; counts come from audit records; mode changes persist through runtime settings; UI frames the auditable gate rather than model judgement.
- [x] Real dependencies flagged (no mocks where forbidden): live counts must use the real audit store implementation; scenario-driven count updates must use the real T13 pipeline and OPA/Postgres services where the selected test environment supports them.

## Gaps or ambiguities
- `briefs/T14_architect_brief.md` was absent, so this brief is derived from `MASTER_SPEC.md`, `TASK_LEDGER.md`, and existing T13/T08/T12 surfaces only. The downstream Implementer should pause if a later Architect brief conflicts with this acceptance framing.
- T14 says “the enforcement-mode toggle,” while the settings store supports per-control modes and §8 says a single `enforcement_mode` per run. Tests should accept either a global dashboard toggle that updates all control modes for T14 or per-control toggles, provided the selected mode is visible and persisted through `SettingsStore`.
- The exact UI route/method for persisting the mode toggle is not specified in the ledger. The Implementer should expose a public, testable form or endpoint used by the dashboard; tests should exercise that public contract once implemented.
