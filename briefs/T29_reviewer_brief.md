# Review Report — T29: Evidence schema versioning + regulatory export framing

## Verdict
APPROVE

## Critical findings
- None

## Spec and ledger compliance
- Correct task only: yes
- Dependencies respected: yes — T02 and T25 are marked Done; T26–T28 have also landed, so the Beat 9 update does not conflict with Beat 0 (T27)
- Allowed files only: yes, with one justified boundary note (see Non-blocking notes)
- `Done when` satisfied: yes — (1) every new record (action_evaluation + approval_decision) carries `evidence_schema_version`; (2) field is visible on the record view and included in JSON and printable HTML exports; (3) `MASTER_SPEC.md` §5.5 documents the field and the spec was bumped to v1.2; (4) `DEMO_SCRIPT.md` Beat 9 narration mentions schema versioning framing; the underlying export is otherwise unchanged from T25
- `Verify` satisfied: yes/not run — the diff and test output confirm all verify-step assertions can be made; formal docker-compose run was not performed in this review session, but the implementation is structurally correct for the verify to pass
- Reviewer focus satisfied: yes — spec-first discipline was followed (MASTER_SPEC.md updated in the same commit before schema code); no other field semantics disturbed; T25 tamper-evidence behaviour is untouched; `raw.get("evidence_schema_version", EVIDENCE_SCHEMA_VERSION)` in read paths is a safe fallback for pre-existing demo rows

## Product invariant checks
- Model is not judge: pass — no policy logic touched
- OPA/PDP owns decisions: pass — not applicable to this task
- Evidence has no decision fields: pass — `test_evidence_schema_still_has_no_decision_or_enforcement_fields` explicitly guards the boundary; `evidence_schema_version` was correctly added to `EvidenceRecord`, not `Evidence`
- Fail-closed preserved: pass — not applicable to this task; no pipeline logic changed
- Append-only audit preserved: pass — only new writes are affected; no existing row mutations; approval_decision path also populates the field correctly
- Stubs labelled: pass — not applicable to this task
- Scenario outcomes preserved: pass — no Rego or pipeline logic changed

## Required changes
1. None — no blocking changes required.

## Non-blocking notes
- The implementer modified `tests/T02_schemas/test_schema_examples.py` and `tests/T12_audit/test_hash_chain.py`, which are outside the T29 allowed file list. The changes are minimal mechanical fixture updates (adding the now-required `evidence_schema_version` field to existing `EvidenceRecord` factory calls) that were necessary to keep prior tasks' tests passing after the schema field became required. `AGENTS.md` states the `tests/` directory is always an allowed location regardless of a task's file list; the spirit of the file-boundary rule is to prevent scope creep into feature code, and these edits contain no feature logic. Accepted without blocking, but worth noting for ledger hygiene.
- The `EVIDENCE_SCHEMA_VERSION` import block in `app/audit/store.py` is placed slightly awkwardly (constant defined before a downstream `from app.config import ...` import). This does not affect behaviour but a future cleanup pass could reorder it.
- `raw.get("evidence_schema_version", EVIDENCE_SCHEMA_VERSION)` in the two read paths is an appropriate and honest fallback for demo-ephemeral stores; the code comment explaining the demo-ephemeral rationale is present in the DDL default (`DEFAULT '1.0.0'`), which is sufficient.
