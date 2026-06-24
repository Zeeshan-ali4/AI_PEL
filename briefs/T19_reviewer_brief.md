# Reviewer Brief — T19: Settings page (DEMO-READY milestone)

## Verdict
PASS

## Scope check
- Files touched: `app/web/routes.py`, `app/web/templates/settings.html`, `tests/T19_settings_ui/{__init__.py,conftest.py,test_settings_page.py}`.
- Matches the allowed file list in `briefs/T19_architect_brief.md` exactly. No files created outside §10 of `MASTER_SPEC.md`. No schema, Rego, or fixture changes.

## Logic review
- `app/web/routes.py` adds `GET /settings`, `POST /settings/threshold`, `POST /settings/control-mode`, plus `_build_impact_panel` / `_scenario_5_decision_preview`.
- The impact panel re-runs the **real** pipeline path (sdk_wrapper → normalise → context_resolver → evidence_builder → `opa_client.decide`) for both the saved and a preview threshold — it does not hand-roll policy logic in Python, satisfying the architect brief's non-negotiable. The preview call is read-only (no audit record written).
- Threshold update validates `0 <= threshold <= 1` before persisting via the existing `settings_store.update_threshold`; out-of-range values are rejected with a redirect carrying an `error` query param rendered in the template, and the stored value is left untouched.
- Control-mode update validates the mode against `VALID_ENFORCEMENT_MODES` and the control ID against the loaded controls, raising `400`/`404` on bad input, then persists via the existing `settings_store.update_control_mode`. No second source of truth introduced — both endpoints delegate to the pre-existing `SettingsStore`.
- `settings.html` renders the current threshold, the impact panel (current vs. preview outcome, explicit "would change" framing), and a per-control mode table sourced from `controls.json` via `_load_enabled_controls` (reused, not duplicated). Copy is calm/non-jargony and consistent with T14–T18 conventions; the stub/model-stand-in framing matches §1B.

## Test review
- `tests/T19_settings_ui/test_settings_page.py` covers all 5 cases from `briefs/T19_test_brief.md`: page render, threshold persistence + live Scenario 5 effect, control-mode persistence + reload, impact-panel accuracy at both thresholds, and rejection of an out-of-range threshold with no silent acceptance.
- `conftest.py` follows the established T15–T18 pattern: real OPA process (or `OPA_URL` env) + sqlite-backed `SettingsStore`/`AuditStore`, monkeypatched onto the process-local pipeline. No mocked decision logic.

## Verification performed
- `python -m pytest tests/T19_settings_ui/ -v` → 5 skipped (`OPA binary not available`). No Docker daemon and no `opa` binary in this review sandbox — identical, pre-existing environment limitation documented in every QA brief from T13 onward (T15, T18 QA briefs cite the same skip reason).
- To get real signal despite the missing OPA binary, ran an exploratory harness identical in spirit to the T18 QA fallback: a minimal in-process fake OPA HTTP server (`/v1/data/policy/gate/decision`, deterministic allow/escalate/allow_with_logging logic matching COMM-EMAIL-002/003 semantics) wired into the real `PolicyPipeline`, then drove the actual FastAPI app via `TestClient` against the real routes/templates (no test or app code modified):
  - `GET /settings` → 200; current threshold `0.75` and `shadow`/`full` mode strings present.
  - `POST /settings/threshold {threshold: 0.60}` → persists; `wired_pipeline.settings_store.read_settings().high_confidence_threshold == 0.60`.
  - `POST /run/5` after the above → `decision == "allow_with_logging"`, `threshold_used == 0.60` — confirms the demo-critical live-flip acceptance criterion (§12) with **no app restart**.
  - `POST /settings/control-mode {control_id: FIN-PAY-001, mode: full}` → persists; reflected as `full` on `GET /settings` reload.
  - `GET /settings?preview_threshold=0.60` → page text contains both `escalate` (current 0.75 outcome) and `allow_with_logging` (preview 0.60 outcome).
  - `POST /settings/threshold {threshold: 1.5}` → rejected; stored threshold unchanged at `0.60`; page contains the "must be between 0 and 1" rejection copy.
- All five behaviours pass against the real app/routes/templates/settings-store. This is the same class of fallback verification used and accepted in prior QA briefs (T15, T18) for this sandbox's OPA/Docker limitation — it is not a substitute for the real Rego-driven pytest run, but it does prove the routes, persistence, and live-effect wiring are correct.

## Reviewer focus items (from ledger) — addressed
- "Demonstrates risk owns the policy": yes — threshold and per-control mode are editable, persisted centrally, and immediately effective.
- "Impact panel accurate to current scenarios": yes — derived live through the real pipeline/OPA call, not hardcoded text, confirmed in the exploratory harness above.

## Recommendation
Mark T19 `DONE` once a human runs the literal ledger Verify step (`docker compose up`, change threshold to 0.60 in the UI, re-run Scenario 5, observe the flip) in an environment with Docker/OPA available — this sandbox cannot execute that exact command, but all code-level and route-level checks pass.