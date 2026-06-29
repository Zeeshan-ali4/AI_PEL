# QA Brief — T26: "If a regulator asked..." evidence mapping

## Scope check
- Files touched match the Architect Brief's allowed-files list exactly: `app/web/regulator_questions.py`, `app/web/routes.py` (wiring only), `app/web/templates/_regulator_questions.html`, `app/web/templates/decision.html` (+include), `app/web/templates/record.html` (+include), `tests/T26_regulator_questions/{__init__.py,conftest.py,test_mapping.py,test_views.py}`.
- No schema, Rego, or policy-logic files touched. No scope creep beyond T26.

## Static/code verification performed
- Read `app/web/regulator_questions.py` in full: `build_regulator_question_rows(record)` returns exactly six ordered rows (interception, policy, evidence/context, judge, human oversight, integrity), each with non-empty `question`, `answer_field_label`, `answer_value`. All values are derived from existing `EvidenceRecord`/`Action`/`Context`/`Evidence`/`Decision` fields — no new computation, no fabricated entities/approvals/controls.
  - Payment path (`evidence.evaluated=False`) explicitly states the semantic layer was not invoked, sourced from `action.action_type` and `evidence.evaluated` — no invented entities.
  - Email path cites `detected_entities`, `vulnerability_indicators`, `overall_confidence`, `sensor_versions`, and labels Presidio as real / nuance_stub as a model stand-in.
  - `fail_closed` adds a conditional `fail_context` block from `decision.failure_mode`, `context_used.context_resolution_ok`, `evidence.sensor_error` — never blank, never framed as a normal allow/block/escalate outcome.
  - `approval_decision` records branch on `record.record_type` and surface `human_approver`, `approval_reason`, `references_hash`, framed as an appended record, not a mutation.
  - Non-escalation records (`required_approval_role is None`) state no approval was required without inventing an approver.
  - Null/empty optional fields (`control_id`, `triggered_controls`, `framework_mappings`, `references_hash`) render explicit "None (`field` is null/empty)" text rather than blanks or invented values.
  - `_judge_row` preserves the model-is-not-the-judge principle: states OPA/the policy engine made the binding decision and sensors only informed it.
- Confirmed via `grep` that `regulator_question_rows` is built once per route (`app/web/routes.py:558`, `:805`) from the same persisted/result record passed to the rest of the view context, and that `decision.html`/`record.html` only `{% include "_regulator_questions.html" %}` — no duplicate question text in any template (`_regulator_questions.html` itself only contains the panel heading/note, iterating `row.question`/`row.answer_field_label`/`row.answer_value`).

## Tests executed
- Environment constraints: this sandbox has no running Docker daemon (`docker compose up` fails — no `/var/run/docker.sock`) and no network access to the OPA binary download host (403 from the egress proxy, policy-blocked, not a configuration issue). No local `opa` binary or Postgres server is available. These are the same constraints the Reviewer hit.
- Built a local venv, installed `requirements.txt`, ran:
  - `pytest -v tests/T26_regulator_questions/` → **1 passed, 12 skipped**. The single runnable test, `test_templates_do_not_define_duplicate_question_text`, passes. The remaining 12 tests in `test_mapping.py`/`test_views.py` skip cleanly via `pytest.skip("OPA binary not available...")` in `conftest.py`'s `opa_url` fixture — this is correct, intentional behaviour (no mocking-around of OPA), not a defect.
  - `pytest -q tests/ -k "not T26"` (broader regression check) → 165 passed, 91 skipped, 2 failed, 4 errors — all pre-existing and Postgres-connectivity-related (`tests/T15_scenarios_ui` and `tests/test_policy_decisions.py`), unrelated to T26 and present before this task's changes. No new failures attributable to T26.

## Coverage vs PM/BA Test Brief
All eleven test brief cases are implemented in `test_mapping.py`/`test_views.py` and are field-backed (assert against literal field-derived substrings, not brittle full-sentence copy matching), consistent with the brief's "stable fragments, not final copy" guidance. Reviewed each test body against its brief case; mapping is faithful — no case is missing, no case is weakened to a tautology.

## Outstanding item (carried from Reviewer Brief, unresolved by QA)
The 12 OPA-backed integration tests in `tests/T26_regulator_questions/` and the ledger's manual Verify step (six scenarios + one approval + one fail-closed simulation through the live UI) require Docker/OPA, which is unavailable in both the Reviewer's and this QA sandbox. This is an environment limitation, not a defect found in the implementation. Recommend running `docker compose run --rm app pytest -q tests/T26_regulator_questions/` and the manual UI walk-through in an environment with Docker before the human gate marks T26 `DONE`.

## QA verdict
**Pass, conditional on the Docker/OPA-backed run above.** Code review finds no fabricated answers, no schema drift, no policy-logic leakage into Python, single source of truth for question text maintained, and the one test runnable in this sandbox passes. No regressions introduced in the broader suite. Do not mark T26 `DONE` until the 12 skipped tests have been executed (green) and the manual six-scenario + approval + fail-closed Verify step has been performed in an environment with Docker/OPA available.
