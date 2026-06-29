# Architect Brief — T29: Evidence schema versioning + regulatory export framing

## Task selected
- Task: T29 — Evidence schema versioning + regulatory export framing
- Current status: To do
- Dependencies checked: pass — T29 depends on T02 and T25; both are marked `Done` in `TASK_LEDGER.md`. T26, T27, and T28 have also landed, so the Beat 9 narration update should not conflict with the Phase 5 demo-script framing order.

## Source-of-truth references
- MASTER_SPEC.md: §0 change log/status and §5.5 Evidence Record are directly in scope because this task intentionally changes the EvidenceRecord schema; §5.3 remains a non-negotiable boundary because Evidence itself must continue to contain no decision/enforcement fields; §8A.5 record/export UI and §9 assurance framing are relevant to how the schema version is presented to risk/regulatory reviewers.
- TASK_LEDGER.md: Golden rule 6 requires schema/file-layout changes to update the spec first; T29 defines the exact goal, allowed files, done criteria, verify step, and reviewer focus.
- AGENTS.md: `MASTER_SPEC.md` is the source of truth; work exactly one task; touch only allowed files; do not silently change schemas, policy decisions, scenario outcomes, or policy logic; every task must produce tests under the task test folder.

## Allowed files
- `MASTER_SPEC.md`
- `app/schemas/audit.py`
- `app/audit/store.py`
- `app/web/templates/record.html`
- `app/web/templates/audit.html`
- `DEMO_SCRIPT.md`
- `tests/T29_evidence_schema_version/`

## Implementation objective
Add one governed schema-version marker to every audit evidence record and make that marker visible wherever T29 requires it. The implementer must first update `MASTER_SPEC.md` so §5.5 documents `evidence_schema_version` on `EvidenceRecord` and the spec version/status at the top is bumped. Only after the spec reflects the new field should code be changed to add `evidence_schema_version: str` to the EvidenceRecord schema, populate it on every new audit write, display it on the record view, mention/show it in the audit log or audit-package export description, and update `DEMO_SCRIPT.md` Beat 9 narration to frame the existing audit package as a regulatory-reporting artefact. Add pytest coverage in `tests/T29_evidence_schema_version/` proving the field is populated for both action evaluation and approval decision records and appears in export/rendered output where practical.

## Non-negotiables
- Spec-first discipline is mandatory: update `MASTER_SPEC.md` §5.5 and the spec version/status before changing `app/schemas/audit.py` or persistence/template code.
- This task adds exactly one EvidenceRecord field: `evidence_schema_version`. Do not add fields to Evidence, Action, Context, Decision, audit package schemas, policy inputs, or OPA outputs.
- The Evidence schema must still contain no allow/block/decision/approval/enforcement field.
- Do not change policy decision semantics, scenario outcomes, Rego logic, control IDs, framework mappings, threshold behaviour, or fail-closed behaviour.
- Do not change T25 audit-package mechanics beyond explanatory framing and inclusion/visibility of the already persisted record field. Preserve the existing tamper-evidence/package-integrity behaviour.
- A simple module-level constant such as `EVIDENCE_SCHEMA_VERSION = "1.0.0"` is sufficient; do not build migrations, version negotiation, or historical backfill tooling for this demo.
- Populate the version for every new record type written by the store, including both `action_evaluation` and `approval_decision` rows.
- `DEMO_SCRIPT.md` changes are narration-only for Beat 9; do not rewrite unrelated beats.
- Tests must live under `tests/T29_evidence_schema_version/` and be real pytest tests, not inline/manual-only checks.

## Verify step
Run the ledger verify for T29: run a scenario, view the record, confirm the version field is present; export JSON and printable HTML, confirm it is included in both; diff `MASTER_SPEC.md` to confirm the schema update is present. In addition, run the task test folder with:

```bash
pytest tests/T29_evidence_schema_version/
```

If the broader project test suite is practical in the environment, also run it to confirm no existing audit/schema/export behaviour regressed.

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T29_architect_brief.md and briefs/T29_test_brief.md. Implement exactly T29. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
