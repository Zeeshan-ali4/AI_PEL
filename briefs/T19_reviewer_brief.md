# Review Report — T19: Settings page (DEMO-READY milestone)

## Verdict
REQUEST CHANGES

## Critical findings
- The Implementer modified `briefs/T19_test_brief.md`, a PM/BA-owned deliverable, outside the Implementer's allowed file list (`app/web/templates/settings.html`, `app/web/routes.py`, `tests/T19_settings_ui/`). This is a file-boundary violation under AGENTS.md ("touch only the files listed for the current task").
- The rewritten test brief silently dropped two PM/BA-specified test cases with no replacement: `test_per_control_modes_render_for_each_known_control` (asserts every known control ID renders with shadow/soft/full options) and `test_default_threshold_keeps_scenario_5_escalated` (the regression guard that the default `0.75` threshold still escalates Scenario 5 to `COMM-EMAIL-002`/`vulnerable_customer_team`). The Reviewer's job under AGENTS.md item 8/9 is to check "test brief fidelity" — the brief on disk no longer matches what PM/BA actually specified, and the implemented test suite (`tests/T19_settings_ui/test_settings_page.py`) does not cover either dropped case. The default-threshold-escalates path for Scenario 5 is the spec's primary baseline (§7) and is currently unverified by any T19 test.
- `TASK_LEDGER.md` status for T19 was changed from "To do" to "Review" by the Implementer. Per AGENTS.md, the build workflow has the Reviewer/Human gate ledger status changes after review, not the Implementer mid-task. Minor compared to the brief rewrite, but still an out-of-scope file touch.

## Spec and ledger compliance
- Correct task only: yes (no other task's allowed files were touched besides the boundary issues above)
- Dependencies respected: yes (T08, T15 both Done)
- Allowed files only: no — `briefs/T19_test_brief.md` and `TASK_LEDGER.md` were modified; only `app/web/templates/settings.html`, `app/web/routes.py`, and `tests/T19_settings_ui/` were authorized
- `Done when` satisfied: unclear — the live threshold flip for Scenario 5 (0.60 → `allow_with_logging`) is implemented and routed through the real pipeline/OPA path, but verification could not be run in this sandbox (no `opa` binary available, all 5 tests skipped)
- `Verify` satisfied: not run — `pytest tests/T19_settings_ui/` produced 5 skipped (OPA binary unavailable in this environment); no manual UI walkthrough could be performed here
- Reviewer focus satisfied: partially — the impact panel demonstrably recomputes through the real OPA path (`_scenario_5_decision_preview` reuses normaliser → context resolver → evidence builder → `opa_client.decide`, no hardcoded if/else), supporting "risk owns the policy," but the missing default-threshold regression test means the panel's "still escalates today" claim has no automated guard against drift.

## Product invariant checks
- Model is not judge: pass — settings UI never evaluates evidence itself
- OPA/PDP owns decisions: pass — `_scenario_5_decision_preview` calls `opa_client.decide`; no decision logic duplicated in Python/Jinja
- Evidence has no decision fields: not applicable (not touched this task)
- Fail-closed preserved: not applicable (not touched this task)
- Append-only audit preserved: pass — impact-panel preview explicitly does not write to the audit store; only `/run/{id}` (existing T13 route) writes records
- Stubs labelled: pass — settings.html explicitly labels the nuance stub's fixed confidence and that the panel "reruns the real policy decision (through OPA, not a hand-written rule here)"
- Scenario outcomes preserved: unclear — no regression test confirms the default `0.75` threshold still yields `escalate` for Scenario 5 after this change; cannot confirm purely by inspection that nothing in this diff could affect the baseline path, since the dropped test would have been the only direct guard

## Required changes
1. Revert `briefs/T19_test_brief.md` to the PM/BA-authored version, or have the PM/BA agent (not the Implementer) author any revision. The Implementer must not edit other roles' brief files.
2. Restore test coverage for the two dropped cases — at minimum, add back a test asserting the default `0.75` threshold still resolves Scenario 5 to `escalate` (control `COMM-EMAIL-002`, role `vulnerable_customer_team`) with `threshold_used == 0.75`, and a test asserting every enabled control from `controls.json` renders with `shadow`/`soft`/`full` options on `/settings`.
3. Revert the `TASK_LEDGER.md` status edit; status transitions are the Reviewer/Human's responsibility, not the Implementer's.

## Non-blocking notes
- Verification was not run end-to-end in this sandbox because the `opa` binary is unavailable (network egress blocked); this mirrors the precedent noted for T18. The route logic, template, and existing test cases otherwise read as spec-compliant and should be re-verified with a real OPA instance before sign-off.
