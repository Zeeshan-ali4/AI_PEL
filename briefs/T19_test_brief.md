# Test Brief — T19: Settings page (DEMO-READY milestone)

## Spec references
- MASTER_SPEC.md: §6 configurable `HIGH_CONFIDENCE` threshold and per-control modes; §8 enforcement modes; §8A item 7 (Settings page requirements, including the live impact-panel worked example); §12 acceptance criteria (threshold change flips Scenario 5 live, with no restart).
- TASK_LEDGER.md: T19 goal, dependencies, allowed files, Done when, Verify step, Reviewer focus.
- Architect brief: `briefs/T19_architect_brief.md` non-negotiables — reuse the existing settings store/pipeline/OPA path, no second source of truth for threshold/mode logic, immediate effect with no restart, accurate live impact panel.

## Target test location
- Folder: `tests/T19_settings_ui/`
- Files:
  - `conftest.py` — real-OPA + sqlite-backed pipeline fixture, mirroring `tests/T18_audit_ui/conftest.py`.
  - `test_settings_page.py` — covers page rendering, threshold persistence, control-mode persistence, and the live Scenario 5 impact panel.

## Test cases

### test_settings_page_renders_current_threshold_and_control_modes
- **Traces to:** MASTER_SPEC.md §8A item 7; TASK_LEDGER T19 Goal.
- **Input:** `GET /settings` against a freshly seeded settings store (defaults).
- **Expected outcome:** HTTP 200; the page shows the current threshold value and every control's current mode from the settings store.

### test_update_threshold_persists_and_takes_effect_without_restart
- **Traces to:** MASTER_SPEC.md §12 acceptance criterion; TASK_LEDGER T19 Done when/Verify step.
- **Input:** `POST /settings/threshold` with `threshold=0.60`, then run Scenario 5 via `POST /run/5`.
- **Expected outcome:** Settings store reads back `0.60`; Scenario 5's decision is `allow_with_logging` with `threshold_used == 0.60`, with no app restart between the threshold change and the scenario run.

### test_update_control_mode_persists_and_reflects_on_reload
- **Traces to:** TASK_LEDGER T19 Goal/Done when; Architect brief per-control mode requirement.
- **Input:** `POST /settings/control-mode` with `control_id=FIN-PAY-001`, `mode=full`, then `GET /settings`.
- **Expected outcome:** Settings store reflects `full` for `FIN-PAY-001`; the reloaded settings page shows `full` selected for that control.

### test_impact_panel_reflects_accurate_scenario_5_outcomes_at_both_thresholds
- **Traces to:** MASTER_SPEC.md §8A item 7 worked example; Architect brief non-negotiable on impact-panel accuracy.
- **Input:** With the threshold saved at the default `0.75`, `GET /settings?preview_threshold=0.60`.
- **Expected outcome:** The page states the current-threshold outcome is `escalate` (Scenario 5's fixed `0.62` confidence is below `0.75`) and the preview-threshold outcome is `allow_with_logging` (above `0.60`), and indicates the outcome would change.
- **Notes:** Must be derived via the real pipeline/OPA path (no hand-written if/else duplicating policy logic in the test or the route).

### test_invalid_threshold_is_rejected_with_no_silent_acceptance
- **Traces to:** Architect brief non-negotiable on settings storage integrity.
- **Input:** `POST /settings/threshold` with `threshold=1.5`.
- **Expected outcome:** The stored threshold is unchanged; the settings page communicates the rejection rather than silently accepting an out-of-range value.

## Coverage checklist
- [x] Happy path: page renders current settings; threshold and mode updates persist and take effect immediately.
- [x] Edge case: out-of-range threshold rejected without mutating stored state.
- [x] Spec non-negotiable verified: live Scenario 5 flip from `escalate` to `allow_with_logging` at `0.60`, matching §7/§12 exactly, with `threshold_used` echoed.
- [x] Real dependencies flagged: tests exercise the real settings store, real OPA (via the `opa_url`/`wired_pipeline` fixture pattern from T15–T18), and the real pipeline — no mocked decision logic.

## Gaps or ambiguities
- Exact route paths (`/settings`, `/settings/threshold`, `/settings/control-mode`) are not prescribed by the spec/ledger; tests discover behaviour through the implementer's chosen routes consistent with the T14–T18 server-rendered conventions.
