# Architect Brief — T20: Test suite

## Task selected
- Task: T20 — Test suite
- Current status: To do
- Dependencies checked: pass — T20 directly depends on T13, which is marked Done. The ledger also shows T14 through T19 are Done, with current task T20 and last completed task T19, so the full demo surface is available for regression coverage.

## Source-of-truth references
- MASTER_SPEC.md: §2 principles (model is not the judge; fail closed; payment path skips semantics), §5 canonical schemas, §6 control library and decision precedence, §7 six narrative scenario outcomes, §10 canonical file layout, §11 pipeline order, §12 acceptance criteria, §13 scope fences.
- TASK_LEDGER.md: T20 task block in Phase 4; earlier T04/T06/T10/T12 verify notes where these four regression tests were deferred/anticipated; golden rules for preserving schemas, OPA authority, real Presidio, and append-only audit records.
- AGENTS.md: work on exactly one task; touch only the files listed for the current task; every task must produce committed pytest tests; do not broaden scope or change schemas/policy outcomes/file layout without updating MASTER_SPEC.md first.

## Allowed files
- `briefs/T20_architect_brief.md` (this Architect handoff only)
- `tests/test_normaliser.py`
- `tests/test_presidio_sensor.py`
- `tests/test_policy_decisions.py`
- `tests/test_audit_chain.py`

## Implementation objective
Create the Phase 4 regression test suite specified by T20. These tests should consolidate the core demo guarantees into four root-level pytest files: normaliser mapping, real Presidio detection on planted email bodies, OPA policy decisions for all six MASTER_SPEC §7 scenarios, and audit hash-chain integrity/tamper detection. The suite must be runnable with the ledger verify command and must protect the demo from silent drift in scenario outcomes, policy precedence, semantic evidence, and audit integrity.

## Non-negotiables
- Do not implement product code in T20. If tests reveal a product defect requiring changes outside the four allowed test files, stop and report the defect for a later/human-approved task rather than editing application, policy, schema, or UI files.
- Keep decisions aligned exactly with MASTER_SPEC §7: #1 `allow`; #2 `escalate` with `finance_supervisor`; #3 `block`; #4 `escalate` with `data_protection_approver`; #5 `escalate` with `vulnerable_customer_team`; #6 `allow_with_logging`.
- `tests/test_policy_decisions.py` must be the regression guard for the full §7 decision table. It must assert both decision and control identity/approval role where applicable, not just “request succeeded.”
- Preserve the policy architecture: OPA/Rego is the judge. Tests may build inputs and invoke existing OPA client/pipeline helpers, but must not duplicate/reimplement decision logic in Python beyond expected assertions.
- Preserve semantic architecture: payment scenarios must assert or otherwise protect that semantic evidence is not evaluated (`Evidence.evaluated == false`) where the tested path exposes it.
- Presidio tests must exercise the real sensor against the planted scenario bodies; do not hardcode fake detections as a substitute for the sensor. Scenario #4 should prove detection of the NHS number/health-special-category evidence. Scenario #6 should remain personal-data-only/no special-category evidence.
- Audit-chain tests must prove: multiple appended records verify intact; tampering a historical row breaks verification; the reported broken record is the tampered record.
- Evidence schema must remain evidence-only. Do not add allow/block/decision/enforcement fields to evidence fixtures or assertions.
- Do not create additional test files, helper files, fixtures files, or subdirectories unless the human updates the task scope. Reuse existing code helpers/imports from the repository.
- Tests should be deterministic and suitable for `docker compose run --rm app pytest -q`.

## Verify step
Run exactly the ledger verification command:

```bash
docker compose run --rm app pytest -q
```

Task-specific checks within the suite:
- Normaliser maps all six raw scenario tool calls to canonical `Action` objects with expected `action_type`, environment, enforcement mode propagation, IDs/correlation IDs, and payment/email fields.
- Presidio sensor detects planted PII/special-category indicators in scenario #4 and does not mark scenario #6 as special-category/vulnerable evidence.
- Policy decision tests assert the complete MASTER_SPEC §7 expected table, including control IDs and required approval roles for escalations.
- Audit-chain tests assert intact verification before tampering and exact broken-record identification after tampering.

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T20_architect_brief.md and briefs/T20_test_brief.md. Implement exactly T20. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.