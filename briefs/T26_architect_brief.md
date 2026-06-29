# Architect Brief — T26: "If a regulator asked..." evidence mapping

## Task selected
- Task: T26 — "If a regulator asked..." evidence mapping
- Current status: To do
- Dependencies checked: pass — TASK_LEDGER.md states T26 depends on T17 and T19, and both T17 (Evidence record detail view/export) and T19 (Runtime settings UI) are marked Done.

## Source-of-truth references
- MASTER_SPEC.md: §1 assurance proof points (human oversight, evidential reliability, demonstrable control operation); §2 golden rule that evidence is not the decision and the policy engine is the judge; §5.1–§5.5 canonical Action, Context, Evidence, Decision, and EvidenceRecord fields; §5.5 append-only approval records and hash-chain integrity; §6 control decisions and illustrative framework mappings; §7 scenario outcomes; §8A decision view, approval queue, evidence record view, and audit integrity UI requirements; §9 auditable-surface narrative.
- TASK_LEDGER.md: T26 goal, file list, key notes, done criteria, verify step, and reviewer focus; dependency note that T26 depends on T17/T19 and can run independently of T20/T21.
- AGENTS.md: work on exactly one task; touch only files listed for the current task plus tests; do not change schemas, directory layout, control IDs, scenario outcomes, or policy logic; every task must produce committed pytest tests in the task test folder; do not mark the task DONE unless verification passes.

## Allowed files
- `app/web/templates/_regulator_questions.html` — new shared partial.
- `app/web/templates/decision.html` — include the shared partial only; do not duplicate mapping strings here.
- `app/web/templates/record.html` — include the shared partial only; do not duplicate mapping strings here.
- `app/web/routes.py` — thread regulator-question rows into the decision-view and record-view template contexts.
- `app/web/regulator_questions.py` — new pure mapping module and the single source of truth for question text, field labels, and field-backed answer values.
- `tests/T26_regulator_questions/` — create `__init__.py` and pytest coverage required by the PM/BA Test Brief.

## Implementation objective
Add a reusable "If a regulator asked..." panel to both the post-run decision page and persisted record view. The panel must present at least six regulator/internal-auditor questions and answer each by pointing to existing fields already present on the current `EvidenceRecord` and its nested `Action`, `Context`, `Evidence`, and `Decision` objects. This is an index into the existing evidence and binding-decision sections, not a new decisioning or summarisation layer.

The implementation should introduce `app/web/regulator_questions.py` with a pure function, for example `build_regulator_question_rows(record: EvidenceRecord) -> list[dict[str, Any]]`, returning ordered row dictionaries compatible with the ledger shape `{question, answer_field_label, answer_value}`. If the implementer needs minor extra keys for display, keep them derived and presentational only; do not move question definitions into templates.

The route layer should pass these rows as a template variable (for example `regulator_question_rows`) from both `_build_decision_view_context(...)` and `_record_view_context(...)`. The decision-view route already has `result.record`; use that record rather than recomputing values from separate objects. The record-view/export context should use the persisted `EvidenceRecord`, so the same panel appears in normal record view and printable HTML export unless tests or UX reveal a specific reason to hide it.

Suggested minimum question coverage:
1. Was the action intercepted before execution? Use `record.executed`, `record.enforcement_mode`, `record.action.action_type`, and optionally the decision outcome to frame shadow/full behaviour.
2. What policy/control was applied, and what does it map to? Use `record.decision.control_id`, `record.decision.triggered_controls`, and `record.decision.framework_mappings`.
3. What evidence and context informed the decision? Use `record.context_used.*` plus `record.evidence.*` fields. For payment records where `record.evidence.evaluated` is false, explicitly answer that the semantic layer was not invoked because it was not needed for the payment action type.
4. Who or what made the decision — model or policy engine? Use `record.decision.decision`, `record.decision.reason`, `record.decision.policy_version`, and `record.evidence.sensor_versions` to state that OPA/policy made the binding decision and sensors supplied evidence only. For `fail_closed`, answer that required policy/context/sensor operation failed and the gate stopped by fail-closed policy.
5. Was a human involved where judgement was required, and is that decision itself evidenced? Use `record.decision.required_approval_role`, `record.record_type`, `record.references_hash`, `record.human_approver`, and `record.approval_reason`. For `approval_decision` records, show the approver/reason and referenced original hash. For non-escalation records, say no human approval was required by the binding decision.
6. Can this record be shown to have not been altered after the fact? Use `record.record_hash`, `record.prev_hash`, and `record.references_hash` where present.

## Non-negotiables
- Do not add or change schema fields. T26 maps existing data only; T29 is the only Phase 5 task allowed to add an evidence schema field.
- Do not change policy logic, OPA/Rego, control IDs, scenario outcomes, enforcement semantics, approval semantics, or audit hash-chain behaviour.
- Do not let the model/evidence appear to be the judge. Copy must preserve the product rule: evidence/sensors inform; the deterministic policy engine makes the binding decision.
- Do not fabricate answers. Every `answer_value` must come from fields on the current record or a conservative rendering of field absence, such as `control_id is None` or `evidence.evaluated is False`.
- Do not duplicate the existing Evidence or Binding decision panels. The new panel is a concise question-to-field index; the detailed evidence and decision sections remain the source for expanded reading.
- Keep question definitions in `app/web/regulator_questions.py` only. Templates should iterate rows and render labels/values without embedding duplicated question text.
- Preserve the ledger edge cases: `fail_closed`, payment records with `evidence.evaluated=false`, all major decisions (`allow`, `allow_with_logging`, `escalate`, `block`), `action_evaluation`, and `approval_decision`.
- Keep framework mapping labels consistent with existing UI: mappings are illustrative and must not imply certification or formal compliance.
- Touch only the allowed files above plus the test file(s) created inside `tests/T26_regulator_questions/`.

## Verify step
Ledger verify step: run each of the six scenarios plus one approval and one fail-closed simulation. Open the decision page and the record view for each. Confirm the regulator-questions panel renders sensible, field-backed answers for every case, including the two edge cases (`fail_closed`, `approval_decision`).

Programmatic checks expected from the implementer/QA:
- `docker compose run --rm app pytest -q tests/T26_regulator_questions/`
- If feasible in the current environment, `docker compose run --rm app pytest -q` to confirm existing behaviour is not regressed.

Task-specific checks to encode in pytest where practical:
- The mapping function returns at least six rows, each with `question`, `answer_field_label`, and `answer_value`.
- The decision page and record page render the heading "If a regulator asked..." and the mapping rows.
- Payment records render a semantic-layer answer based on `evidence.evaluated=false` rather than pretending semantic evidence exists.
- Email records render semantic evidence/sensor-backed answers using existing evidence fields.
- `fail_closed` records render a policy-engine/fail-closed explanation rather than blank control/evidence text.
- `approval_decision` records render `human_approver`, `approval_reason`, and `references_hash`-backed oversight answers.
- Tests assert question text is sourced through `app/web/regulator_questions.py`, not hardcoded independently in both templates.

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T26_architect_brief.md and briefs/T26_test_brief.md. Implement exactly T26. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
