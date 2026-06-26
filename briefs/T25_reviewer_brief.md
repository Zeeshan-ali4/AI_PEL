# Review Report — T25: Audit security demonstration (extends T17/T18)

## Verdict
APPROVE

## Critical findings
- None

## Spec and ledger compliance
- Correct task only: yes
- Dependencies respected: yes
- Allowed files only: yes
- `Done when` satisfied: yes
- `Verify` satisfied: yes
- Reviewer focus satisfied: yes

## Product invariant checks
- Model is not judge: not applicable
- OPA/PDP owns decisions: not applicable
- Evidence has no decision fields: not applicable
- Fail-closed preserved: not applicable
- Append-only audit preserved: pass
- Stubs labelled: not applicable
- Scenario outcomes preserved: not applicable

## Required changes
1. None

## Non-blocking notes
- The audit-package export supports all-record and correlation-id scoped packages, but not date-range scoped packages. This is acceptable for T25 because the ledger phrases date range as optional (`correlation_id` or date range), and the delivered correlation-id path satisfies the required selection/export story.
- I verified the reviewer focus with route/template tests rather than a browser session: the audit page renders green links for intact records, exposes stored-vs-recomputed hashes after simulated tampering, and labels the export as a demo integrity check rather than production-grade signing.
