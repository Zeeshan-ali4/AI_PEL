# Architect Brief — T19: Settings page (DEMO-READY milestone)

## Task selected
- Task: T19 — Settings page (DEMO-READY milestone)
- Current status: TODO (implicit: task has no status line marked Done/Review in `TASK_LEDGER.md`; ledger current task is T19)
- Dependencies checked: pass — T08 is marked Done and T15 is marked Done in `TASK_LEDGER.md`; current build state says last completed task is T18 and known blockers are none.

## Source-of-truth references
- MASTER_SPEC.md: §1 value pillars (governed, configurable policy); §2 principles (model is not judge, uncertainty escalates, fail closed); §4 technology decisions (DB-backed runtime settings row); §5.4 Decision includes `threshold_used`; §6 configurable `HIGH_CONFIDENCE` threshold, control library, decision precedence, and per-control framework mappings; §7 Scenario 5 has nuance stub confidence 0.62 and normally escalates under the default 0.75 threshold; §8 enforcement modes; §8A item 7 Settings page requirements; §10 canonical file layout; §11 pipeline loads runtime settings before OPA; §12 acceptance criteria including live Scenario 5 threshold flip.
- TASK_LEDGER.md: T19 goal, dependencies, allowed files, Done when, Verify, and Reviewer focus.
- AGENTS.md: work exactly one task; do not start next task; touch only task-listed files plus `tests/`; do not change schemas, directory layout, control IDs, scenario outcomes, or policy logic; downstream Implementer must create committed pytest tests under the T19 test subfolder.

## Allowed files
- `app/web/templates/settings.html`
- `app/web/routes.py`
- `tests/T19_settings_ui/`

## Implementation objective
Build the assurance UI Settings page for T19 only. The page must let a risk owner edit the runtime high-confidence threshold and per-control enforcement modes, persist those changes through the existing settings store, and make those settings affect subsequent policy decisions immediately without restarting the app. It must include a clear live impact panel explaining Scenario 5's current threshold outcome, especially the demo point: at the default `0.75`, Scenario 5's `0.62` confidence escalates; at `0.60`, Scenario 5 would allow-with-logging.

## Non-negotiables
- Do not implement settings storage or policy logic in this task; use the existing DB-backed settings store and existing pipeline/OPA path. The Settings UI must not become a second source of truth for thresholds or modes.
- Do not change schemas, Rego policies, controls metadata shape, scenario fixture data, or the expected scenario outcomes in `MASTER_SPEC.md` §7.
- Do not add files outside the allowed list. If a needed route/helper appears to require files outside `app/web/routes.py`, stop and escalate rather than broadening scope.
- Keep all implementation inside server-rendered FastAPI/Jinja2 conventions already established by T14–T18. No JS build tooling.
- The UI copy must support the Head of Risk & Assurance demo: calm, readable, non-jargony, and explicit that risk owns the policy.
- The live impact panel must be accurate for Scenario 5's fixed nuance confidence of `0.62` and the current stored threshold. It should not claim a binding OPA decision unless it is derived consistently from the current threshold/control semantics.
- Per-control mode editing must present the known modes `shadow`, `soft`, and `full` and persist changes for each existing control from `opa/data/controls.json`/settings data as already used by the dashboard.
- Changes must take effect immediately for subsequent runs. The critical acceptance proof is: set threshold to `0.60`, re-run Scenario 5, and observe `allow_with_logging` without app restart.
- Every task produces tests. The Implementer must create pytest tests under `tests/T19_settings_ui/`, including `__init__.py` and at least one real `test_*.py` file.

## Verify step
Ledger manual verification: change the threshold live; re-run Scenario 5; observe the flip to `allow_with_logging`. Demo is now runnable end-to-end.

Recommended programmatic checks for the Implementer/QA:
- `docker compose run --rm app pytest tests/T19_settings_ui/`
- If feasible in the existing test harness, assert the settings page renders the current threshold, posts a new threshold of `0.60`, persists it, and a subsequent Scenario 5 run uses the new threshold and returns `allow_with_logging` with `threshold_used` equal to `0.60`.
- If feasible in the existing test harness, assert per-control mode form submissions persist and the settings page reflects the updated mode on reload.

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T19_architect_brief.md and briefs/T19_test_brief.md. Implement exactly T19. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
