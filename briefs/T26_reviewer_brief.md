# Reviewer Brief — T26: "If a regulator asked..." evidence mapping

## Scope check
- Files touched (commit `aacfc59`): `app/web/regulator_questions.py`, `app/web/routes.py` (+3 lines wiring), `app/web/templates/_regulator_questions.html`, `app/web/templates/decision.html` (+2 lines include), `app/web/templates/record.html` (+2 lines include), `tests/T26_regulator_questions/{__init__.py,conftest.py,test_mapping.py,test_views.py}`.
- Matches the Architect Brief's allowed-files list exactly. No schema files, Rego, or policy logic touched. No scope creep.

## Correctness against MASTER_SPEC.md / briefs
- **No schema change.** `app/web/regulator_questions.py` only reads existing fields off `EvidenceRecord`/`Action`/`Context`/`Evidence`/`Decision`; no new Pydantic fields, no allow/block field introduced anywhere. Consistent with golden rule 4 and the non-negotiable that only T29 may touch the schema.
- **No decision logic in Python.** The module is a pure read/format function (`build_regulator_question_rows`); it does not call OPA, does not compute a decision, and does not alter `executed`/control outcomes.
- **Single source of truth.** `QUESTIONS` dict lives only in `regulator_questions.py`; `_regulator_questions.html` iterates `regulator_question_rows` with no embedded question copy; `decision.html`/`record.html` only `{% include %}` the partial. `test_templates_do_not_define_duplicate_question_text` enforces this directly by asserting question strings are absent from all three template files and present only in the module.
- **Six-question minimum met** (interception, policy, evidence/context, judge, human oversight, integrity) — matches the Architect Brief's suggested coverage and TASK_LEDGER's Done criterion 1.
- **Edge cases handled correctly, field-backed, no fabrication:**
  - Payment (`evidence.evaluated=False`) → explicit "semantic layer not invoked/not needed" wording sourced from `action.action_type` and `evidence.evaluated`, no invented entities.
  - Email (`evidence.evaluated=True`) → cites `detected_entities`, `vulnerability_indicators`, `overall_confidence`, `sensor_versions`; explicitly labels Presidio as real and nuance_stub as a model stand-in; never claims the model decided.
  - `fail_closed` → `_judge_row` adds a conditional `fail_context` block sourced from `decision.failure_mode`, `context_used.context_resolution_ok`, `evidence.sensor_error` — not blank, not treated as a normal allow/block/escalate outcome.
  - `approval_decision` records → `_human_oversight_row` branches on `record.record_type == RecordType.APPROVAL_DECISION` and renders `human_approver`, `approval_reason`, `references_hash`, framed explicitly as "a new appended record, not a mutation," consistent with §5.5 append-only semantics.
  - Non-escalation records (`required_approval_role is None`) → conservative "no human approval was required" wording without inventing an approver.
  - Null/empty optional fields (`control_id`, `triggered_controls`, `framework_mappings`, `references_hash`) → rendered as explicit "None (`field` is null/empty)" rather than blank or fabricated text.
- **Judge framing preserved.** `_judge_row` states OPA/the policy engine made the binding decision and that "evidence sensors only informed" it — keeps the model-is-not-the-judge principle intact (§2) in user-facing copy, not just in code structure.
- **Decision-view and record-view parity.** Both routes (`routes.py:558`, `routes.py:805`) pass `regulator_question_rows` built from the same `EvidenceRecord` rather than recomputing from separate objects, matching the Architect Brief's instruction to reuse `result.record`/the persisted record.
- **Panel is additive, not duplicative.** The partial sits as its own `<section>` alongside (not replacing) the existing Evidence/Binding decision sections in both templates (confirmed by `Binding decision` and `Evidence` still asserted present in `test_decision_page_renders_regulator_panel_with_rows_after_scenario_run`).

## Test coverage assessment
- `tests/T26_regulator_questions/test_mapping.py` and `test_views.py` closely trace to every test case in the PM/BA Test Brief (ordered minimum rows, six-concern coverage, all six §7 scenario outcomes, payment-vs-email semantic differentiation, fail-closed, approval-decision, non-escalation, route/template rendering, no-duplicate-text, conservative-null rendering). Each assertion is field-backed (checks for literal field-derived substrings like `decision.control_id is null`, `record_type=approval_decision`), not copy-matching brittle full sentences.
- `conftest.py` follows the established pattern from T15/T16 (`wired_pipeline` fixture: real pipeline wired to sqlite-backed settings/audit stores and a real OPA process), so these are genuine integration tests against real pipeline-generated records, not mocked fixtures — consistent with AGENTS.md's "Presidio, OPA, and the audit hash chain must be real."
- Gracefully skips OPA-dependent tests when no `opa` binary is on `PATH` (`pytest.skip`), rather than mocking OPA out — correct behaviour for an environment without OPA installed, and does not weaken the test when OPA is present in CI/dev.

## Verification performed in this review
- Reviewed full diff and templates by hand against both briefs and MASTER_SPEC.md §1, §2, §5, §6, §7, §8A.
- Installed the project's `requirements.txt` into a local venv (Docker daemon unavailable in this environment, so `docker compose run` could not be used) and ran `pytest -v tests/T26_regulator_questions/`: **1 passed, 12 skipped** — the only test runnable without Postgres/OPA (`test_templates_do_not_define_duplicate_question_text`) passes; the remaining 12 integration tests skip cleanly because no `opa` binary/network access was available to fetch one in this sandbox (could not download the OPA binary — no outbound network for that host). They were not run end-to-end here.
- Did not find any place where an answer is fabricated independent of the record's own fields; did not find any reintroduction of a decision/allow/block field anywhere in the new code.

## Outstanding item for QA / human gate
- The 12 OPA-backed tests in `tests/T26_regulator_questions/` (real-pipeline scenario runs, fail-closed simulation, approval-decision flow, full route rendering) need to be executed in an environment with Docker/OPA available (e.g. `docker compose run --rm app pytest -q tests/T26_regulator_questions/`) before this task is marked `DONE`. Static review of the implementation against both briefs found no defects, but the human gate's Verify step (running the six scenarios + one approval + one fail-closed simulation through the actual UI) has not yet been executed and should still happen per AGENTS.md.

## Reviewer verdict
Implementation matches both briefs and MASTER_SPEC.md non-negotiables. No fabricated evidence, no schema drift, no policy-logic leakage into Python, single source of truth for question text maintained, and test design is rigorous and field-backed. **Recommend approval pending a docker/OPA-backed test run and the manual UI verify step**, which this sandbox could not perform due to no Docker daemon and no network access to install OPA.
