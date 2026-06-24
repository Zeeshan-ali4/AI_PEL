# Architect Brief — T16: Approval queue view

## Task selected
- Task: T16 — Approval queue view
- Current status: TODO / To do
- Dependencies checked: PASS — T16 depends on T15, and T15 is marked Done in `TASK_LEDGER.md`. The ledger current task is T16 and the last completed task is T15, with no known blockers.

## Source-of-truth references
- `MASTER_SPEC.md` §5.5 Evidence Record: approval decisions are append-only `approval_decision` rows, linked to the original `action_evaluation` by `correlation_id` and `references_hash`; the original audit row must never be mutated.
- `MASTER_SPEC.md` §7 scenario table: Scenario 2 (`Payment £850`, `CUST-100`, no approval) must resolve to `escalate` → `finance_supervisor` with control `FIN-PAY-002`.
- `MASTER_SPEC.md` §8A item 4: Approval queue must show pending escalations with role, action summary, and evidence; Approve / Reject must require a reason; human approval/rejection appends a new linked `approval_decision` record carrying approver, reason, and resulting `executed` state.
- `MASTER_SPEC.md` acceptance criteria: approving an escalation appends a linked `approval_decision` record with approver + reason, sets `executed` accordingly, and leaves the original record unchanged.
- `TASK_LEDGER.md` T16: Goal, file scope, done condition, verify step, and reviewer focus for the approval queue view.
- `AGENTS.md`: Work on exactly one task; touch only task files plus the test location; do not change schemas, policy decisions, scenario outcomes, or file layout; every task must produce committed pytest tests under the task test subfolder.

## Allowed files
- `app/web/templates/approvals.html`
- `app/web/routes.py`
- `tests/T16_approvals_ui/__init__.py`
- `tests/T16_approvals_ui/test_approvals_ui.py`

## Implementation objective
Implement the server-rendered approval queue page and its form actions for exactly T16. The page should make human oversight visible by listing pending escalations from prior pipeline runs, including the required approval role, readable action summary, policy reason/control, and relevant evidence/context details. Approve and Reject submissions must require a non-empty reason and append a new hash-chained audit record of type `approval_decision`; they must not mutate the original `action_evaluation` record.

Use the existing process-local `PolicyPipeline` and `ApprovalQueue` created by `get_pipeline()` as the bridge from a T15 scenario run to the approval UI. When Scenario 2 is run in a mode that queues escalations, `/approvals` must show a pending item for `finance_supervisor`. The approval/rejection handler should resolve the original `action_evaluation` record by queue item correlation/control linkage, write a new audit row with:

- same `correlation_id` as the original action evaluation,
- `record_type="approval_decision"`,
- `references_hash` equal to the original record's `record_hash`,
- `human_approver` populated from the form or a stable demo default,
- `approval_reason` equal to the required submitted reason,
- `executed=true` for Approve and `executed=false` for Reject.

After actioning, the queue item should no longer be listed as pending (the existing in-memory queue's appended approval decision can be used for pending/actioned state), and the page should show an actioned state or success message that makes the appended record visible enough for the demo and tests.

## Non-negotiables
- Do not mutate the original `action_evaluation` audit record. No update helper should be used for approvals; only append via `AuditStore.write_record`.
- Reason is mandatory for both Approve and Reject. Blank/whitespace-only reasons must not append an audit record.
- Preserve the current Evidence schema: do not add approval, decision, enforcement, allow, or block fields to `Evidence`.
- Do not add new product files beyond the allowed files and the T16 test subfolder files above.
- Do not change OPA/Rego policy, scenario data, schema definitions, audit-store hashing semantics, or enforcement-mode semantics.
- Keep all UI copy consistent with the assurance message: the model/evidence is a sensor, the policy decision has already been made by OPA, and the human is deciding the escalated action.
- Payment scenarios must continue to show/use unevaluated semantic evidence (`evidence.evaluated=false`); do not invoke the semantic layer from the approval view.

## Verify step
Ledger manual verify: run Scenario 2, confirm it appears in the approval queue for `finance_supervisor`, approve with a reason, then check the audit log/store shows two linked records and the original is intact.

Programmatic checks for this task:

```bash
pytest tests/T16_approvals_ui
```

Recommended manual smoke path with the app running:

```bash
# Ensure a mode that queues escalations is active if needed by existing settings.
curl -X POST http://localhost:8080/scenarios/2/run
# Open http://localhost:8080/approvals and confirm the pending finance_supervisor item.
# Submit Approve with a non-empty reason.
# Inspect audit records via test/helper code or a Python shell and confirm:
# - one original action_evaluation for the Scenario 2 correlation_id,
# - one linked approval_decision with references_hash == original.record_hash,
# - original.executed remains false,
# - approval_decision.executed is true.
```

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T16_architect_brief.md` and `briefs/T16_test_brief.md`. Implement exactly T16. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.