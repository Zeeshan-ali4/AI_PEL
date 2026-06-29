# Architect Brief — T28: Evidence sufficiency checklist (record view)

## Task selected
- Task: T28 — Evidence sufficiency checklist (record view)
- Current status: To do
- Dependencies checked: pass — T28 depends on T17 and T26, and both are marked Done in `TASK_LEDGER.md`.

## Source-of-truth references
- MASTER_SPEC.md: §1 "What the demo proves" and §1A "Risk & Assurance buyer proof-points" establish that the demo must show reliable, complete, tamper-evident evidence for consequential AI-agent actions. §5 defines the existing Action, Context, Evidence, Decision, and EvidenceRecord field set and the prohibition on adding decision/enforcement fields to Evidence. §5.5 defines hash-chained evidence records, `record_type`, `record_hash`, `prev_hash`, `references_hash`, and append-only approval records. §8A item 5 defines the evidence record view as readable/printable and showing hashes, approver, reason, and execution status. §9 frames the auditable surface as consequential gated actions and binding decisions, not complete transcript logging.
- TASK_LEDGER.md: T28 task definition, including goal, dependencies, allowed files, key notes, done criteria, verify step, and reviewer focus. Phase 5 notes state T28 is presentational/content work over fields the pipeline already produces and should not add schema fields.
- AGENTS.md: Work exactly one task at a time; touch only the task's listed files plus the task test folder; do not change schemas, file layout, control IDs, scenario outcomes, policy logic, or acceptance criteria; every task must produce committed pytest tests under its task test folder.

## Allowed files
- `app/audit/sufficiency.py` — new pure function module: `EvidenceRecord -> list[SufficiencyItem]`, with no persistence and no schema changes.
- `app/web/templates/record.html` — extend the record view with a clearly-labelled sufficiency checklist section.
- `app/web/routes.py` — pass the sufficiency checklist into the record route's template context.
- `tests/T28_evidence_sufficiency/` — create the task test package and pytest tests for this task.

## Implementation objective
Add an evidence sufficiency checklist to the single-record view. The checklist must evaluate the record's existing fields against a small set of clearly-labelled, illustrative sufficiency criteria and render each criterion as `met`, `not-applicable`, or `missing`/`pending` as appropriate. The goal is to make the record visibly answer whether the evidence is sufficient for the demo's assurance narrative, without claiming certification or introducing any new schema, persistence, policy, or scenario behaviour.

## Non-negotiables
- Do not modify `MASTER_SPEC.md`, schemas, migrations, audit persistence, policy/Rego, scenario outcomes, control IDs, enforcement logic, or export behaviour for T28.
- The checklist is illustrative only. The record view must include an unmissable label equivalent to: "Illustrative sufficiency check, not a compliance certification." Use the same honesty/framing pattern as existing illustrative framework-mapping language.
- `app/audit/sufficiency.py` must be a pure evaluation module over already-loaded record data. It must not query the database, mutate records, write audit rows, call OPA, call the semantic layer, or special-case scenario numbers.
- Criteria must be derived from fields that already exist on the record and linked approval records available to the record route. Do not add an `EvidenceRecord` field; T29 is the only Phase 5 task reserved for a schema addition.
- Include at least five checklist items. Required minimum criteria:
  - pre-execution interception evidenced — based on `executed` and `enforcement_mode` presence/meaning;
  - decision rationale recorded — based on non-empty `decision.reason`;
  - framework/control mapping present — based on existing framework mapping/control fields, with correct not-applicable handling when no mapping is required by record shape;
  - tamper-evident chain position recorded — based on `record_hash` and `prev_hash` being present, with genesis/first-record handling if applicable;
  - human oversight evidenced where required — for `escalate` action-evaluation records, met only when a linked `approval_decision` record exists; pending/missing when not yet approved; not-applicable for decisions that do not require human oversight.
- Handle `record_type` correctly. `action_evaluation` records and `approval_decision` records have different shapes; approval records should not be penalised for action-only fields when their own approver/reason/executed/reference fields provide the relevant evidence.
- Handle `fail_closed` sensibly. A fail-closed record should be assessed from its actual fields and should not be treated as a certification failure merely because the policy engine failed; the checklist should make missing/available evidence explicit.
- Preserve the T26 regulator-question mapping. Do not remove or weaken the existing regulator-questions panel in `record.html`; the T28 checklist should complement it.
- Payment records must continue to reflect that the semantic layer was not invoked where not needed. Do not introduce criteria that require semantic evidence for every action type.
- Tests must be real pytest tests in `tests/T28_evidence_sufficiency/`; include `__init__.py` and at least one `test_*.py` file. The PM/BA Test Brief will specify the exact target test file path.

## Verify step
Manual verification from `TASK_LEDGER.md`:

Run all six scenarios, view each record, and confirm the checklist renders sensibly. Run Scenario 2, view its record before approving (human-oversight item should show pending/missing), approve it, and view the record again (human-oversight item should show met).

Required automated checks for this task:

- Run the T28 pytest folder, for example: `docker compose run --rm app pytest -q tests/T28_evidence_sufficiency/`.
- Tests should cover the pure sufficiency function for representative record shapes: normal allow/logging or modify/block record, pending escalation, approved escalation with linked `approval_decision`, approval record, and fail-closed or deliberately incomplete record.
- Tests should cover the record route/template context enough to prove the checklist and illustrative/non-certification label render on the record view.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T28_architect_brief.md` and `briefs/T28_test_brief.md`. Implement exactly T28. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
