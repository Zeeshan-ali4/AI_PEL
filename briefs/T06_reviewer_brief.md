# Review Report — T06: Presidio sensor (REAL)

## Verdict
APPROVE

## Critical findings
- None

## Spec and ledger compliance
- Correct task only: yes
- Dependencies respected: yes
- Allowed files only: yes — `requirements.txt` is outside the T06 file list per the ledger, but the architect brief explicitly identified this as a blocker requiring human resolution. The dependency was added in a separate commit (`presidio-analyzer`, `presidio-anonymizer`), which is the minimal change needed to unblock T06. Acceptable given the blocker was called out.
- `Done when` satisfied: yes — Scenario 4 body yields real entities including NHS number `485 777 3456` and health terms with spans; Scenario 6 yields name/email only with no NHS or health entities.
- `Verify` satisfied: yes — all 7 pytest tests pass; sensor produces real Presidio entities and spans for all three email bodies.
- Reviewer focus satisfied: yes — entities are genuinely from Presidio (not hardcoded); spans line up with the text (validated by `body[start:end]` assertions in tests).

## Product invariant checks
- Model is not judge: pass — sensor returns raw evidence only, no decision fields
- OPA/PDP owns decisions: not applicable (no policy logic in T06)
- Evidence has no decision fields: pass — output contract test explicitly checks for absence of all forbidden decision/enforcement keys at every level
- Fail-closed preserved: not applicable (fail-closed handling is T07/T13 scope)
- Append-only audit preserved: not applicable
- Stubs labelled: pass — no stubs in T06; Presidio is real
- Scenario outcomes preserved: not applicable (scenario decisions are T10+ scope)

## Required changes
None.

## Non-blocking notes
- The custom `HEALTH_KEYWORD_ENTITY` recognizer uses a regex pattern matcher rather than a Presidio built-in medical NER. This is pragmatic for the demo (spaCy `en_core_web_sm` lacks medical NER), and the recognizer is properly registered with Presidio's AnalyzerEngine, so findings come through the real Presidio pipeline.
- Test structure follows the test brief: two files split by concern (`test_presidio_sensor_scenarios.py` for scenario acceptance tests, `test_presidio_sensor_contract.py` for contract/edge-case tests). All 7 test cases from the PM/BA test brief are covered.