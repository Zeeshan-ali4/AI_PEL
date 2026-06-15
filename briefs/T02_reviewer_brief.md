# Review Report — T02: Pydantic v2 schemas (all five)

## Verdict
APPROVE

## Critical findings
- None

## Spec and ledger compliance
- Correct task only: yes
- Dependencies respected: yes (T01 is DONE)
- Allowed files only: yes — `app/schemas/{action,context,evidence,decision,audit}.py`, `app/schemas/__init__.py`, and `tests/T02_schemas/` only
- `Done when` satisfied: yes — all five models import cleanly, validate hand-built examples, and Evidence has no allow/block/decision field
- `Verify` satisfied: yes — all 30 pytest tests pass; imports succeed without side effects
- Reviewer focus satisfied: yes — field names match §5 verbatim; Evidence cannot express a decision

## Product invariant checks
- Model is not judge: pass
- OPA/PDP owns decisions: pass (no policy logic in schemas)
- Evidence has no decision fields: pass (verified by `test_evidence_model_has_no_decision_or_enforcement_fields` asserting exact field set and checking forbidden substrings)
- Fail-closed preserved: not applicable (no runtime logic in T02)
- Append-only audit preserved: not applicable (no DB in T02)
- Stubs labelled: not applicable
- Scenario outcomes preserved: not applicable

## Required changes
1. None

## Non-blocking notes
- `DetectedEntity.score` has no `ge=0, le=1` constraint, unlike `overall_confidence` and `vulnerability_indicators.confidence`. Presidio scores are 0–1 but this is a minor gap — could be added later if needed.
- All fields use `Field(...)` (required). This is strict but correct per the architect brief's guidance on not hiding required fields behind defaults. Downstream tasks will need to supply all fields explicitly, which is the right trade-off for contract clarity.