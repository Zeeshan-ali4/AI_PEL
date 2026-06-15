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
5. Read `briefs/T<XX>_architect_brief.md` and `briefs/T<XX>_test_brief.md` for the current task.

During coding:

1. Touch only the files listed for the current task.
2. Do not create extra files unless the task explicitly allows them.
3. Do not start the next task.
4. Do not silently change schemas, directory layout, control IDs, scenario outcomes, or policy logic.
5. If a task appears to require a file outside the allowed list, stop and ask.

Agent pipeline:

Architect → PM/BA → Implementer → Reviewer → QA → Release Manager → Human

### Role prompts

Each agent in the pipeline has a detailed role prompt in `agent_prompts/`:

| Role | Prompt file |
|------|-------------|
| Architect | [`agent_prompts/architect.md`](agent_prompts/architect.md) |
| PM / BA | [`agent_prompts/pm_ba.md`](agent_prompts/pm_ba.md) |
| Spec Guardian | [`agent_prompts/spec_guardian.md`](agent_prompts/spec_guardian.md) |
| Implementer | [`agent_prompts/implementer.md`](agent_prompts/implementer.md) |
| Reviewer | [`agent_prompts/reviewer.md`](agent_prompts/reviewer.md) |
| QA | [`agent_prompts/qa.md`](agent_prompts/qa.md) |
| Release Manager | [`agent_prompts/release_manager.md`](agent_prompts/release_manager.md) |
| Demo Reviewer | [`agent_prompts/demo_reviewer.md`](agent_prompts/demo_reviewer.md) |

When starting a pipeline stage, read the corresponding prompt file for that role's full instructions.

The PM/BA Agent reads the Architect Brief and produces a Test Brief defining the QA test cases for the task. The PM/BA **must always specify a target test file** — never defer testing to inline checks or say "no test file in scope." The Implementer writes both feature code and test code from these briefs. The `tests/` directory is always an allowed location for test files regardless of a task's file list. Every task must produce a committed test file with passing pytest tests. The QA agent validates that implemented tests cover the PM/BA Test Brief during verification.

After coding:

1. Run the task’s `Verify` step from `TASK_LEDGER.md`.
2. Report what changed.
3. Report the verification result.
4. Do not mark the task `DONE` unless verification passes.


## Agent briefs

Agent briefs are written to the `briefs/` directory and committed to the repo so downstream agents can read them across sessions.

Naming convention:
- `briefs/T<XX>_architect_brief.md` — produced by the Architect agent
- `briefs/T<XX>_test_brief.md` — produced by the PM/BA agent
- `briefs/T<XX>_reviewer_brief.md` — produced by the Reviewer agent
- `briefs/T<XX>_qa_brief.md` — produced by the QA agent
- `briefs/T<XX>_release_brief.md` — produced by the Release Manager agent

The pipeline order is:

1. **Architect** — selects the task, writes `briefs/T<XX>_architect_brief.md`
2. **PM/BA** — reads the Architect Brief, writes `briefs/T<XX>_test_brief.md` with functional/acceptance test scenarios
3. **Implementer** — reads both briefs, writes feature code and test code
4. **Reviewer** — reviews code and tests against briefs and spec, writes `briefs/T<XX>_reviewer_brief.md`
5. **QA** — runs tests, validates coverage against the Test Brief, writes `briefs/T<XX>_qa_brief.md`
6. **Release Manager** — reads all briefs, synthesises a release decision, writes `briefs/T<XX>_release_brief.md`
7. **Human** — final verification and marks task `DONE`

## Test responsibilities

Each task's test subfolder (`tests/T<XX>_<feature>/`) is listed in the task's Files in `TASK_LEDGER.md`. The Implementer creates an `__init__.py` and one or more `test_*.py` files inside it. The PM/BA Test Brief must reference the task's test subfolder as the target location.

| Test type | Defined by | Written by | Verified by |
|-----------|-----------|------------|-------------|
| Functional/acceptance tests | PM/BA (test brief) | Implementer | QA |
| Unit tests | Implementer (own judgement) | Implementer | Reviewer |

**Every task produces tests.** The PM/BA must specify a target test file path. The Implementer must create that file with real pytest tests. The `tests/` directory is always allowed. A task without a committed test file is incomplete.

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
```

After the task passes verification:

```bash
git status
git diff --stat
git diff
git add .
git commit -m "T01 scaffold app services and health check"
```

Then merge back only after review