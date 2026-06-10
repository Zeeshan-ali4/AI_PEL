# AGENTS.md

## Project source of truth

This repo is built from two control documents:

- `MASTER_SPEC.md` is the source of truth for product behaviour, schemas, architecture, file layout, control logic, scenarios, UI requirements, and acceptance criteria.
- `TASK_LEDGER.md` is the implementation order.

If there is a conflict, `MASTER_SPEC.md` wins.

Do not deviate from schemas, file layout, control logic, scenario decisions, or acceptance criteria without updating `MASTER_SPEC.md` first.

---

## Build workflow

Work on exactly one task from `TASK_LEDGER.md` at a time.

Before coding:

1. Read `MASTER_SPEC.md`.
2. Read the current task in `TASK_LEDGER.md`.
3. Confirm all dependencies for the task are marked `DONE`.
4. Confirm the exact files allowed for the task.

During coding:

1. Touch only the files listed for the current task.
2. Do not create extra files unless the task explicitly allows them.
3. Do not start the next task.
4. Do not silently change schemas, directory layout, control IDs, scenario outcomes, or policy logic.
5. If a task appears to require a file outside the allowed list, stop and ask.

After coding:

1. Run the task’s `Verify` step from `TASK_LEDGER.md`.
2. Report what changed.
3. Report the verification result.
4. Do not mark the task `DONE` unless verification passes.

---

## Task status values

Use these status values in `TASK_LEDGER.md`:

- `TODO`
- `IN_PROGRESS`
- `REVIEW`
- `DONE`
- `BLOCKED`

Only mark a task `DONE` after the Verify step passes.

---

## Non-negotiable product rules

- The model is not the judge.
- The policy engine is the judge.
- Evidence is only evidence.
- The Evidence schema must not contain any allow, block, decision, approval, or enforcement field.
- OPA/Rego makes binding policy decisions.
- Python may only return `fail_closed` when OPA is unreachable or required context/sensors fail.
- Presidio, OPA, and the audit hash chain must be real.
- Stubs must be visibly labelled as stubs.
- Audit records are append-only.
- Human approvals append a new `approval_decision` record.
- Never mutate an existing audit record in normal operation.
- Payment scenarios must not invoke the semantic layer.
- Scenario outcomes must match `MASTER_SPEC.md` section 7 exactly.

---

## Git workflow

Use one branch per task:

```bash
git checkout main
git pull
git checkout -b task/T01-scaffold