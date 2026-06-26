# Architect Brief — T24: Escalation dashboard polish (extends T16)

## Task selected
- Task: T24 — Escalation dashboard polish (extends T16)
- Current status: To do
- Dependencies checked: pass — `TASK_LEDGER.md` marks T16 and T22 as Done, and T24 depends only on T16 and T22.

## Source-of-truth references
- MASTER_SPEC.md: §5.5 Evidence Record / append-only approvals; §8A item 4 Approval queue (human oversight, visible); §10 file layout; §11 runtime flow; §12 demo acceptance criteria for approvals.
- TASK_LEDGER.md: T24 task definition, allowed files, key notes, Done when, Verify step, and Reviewer focus; T16 for the existing approval workflow that must not regress; T22 for pipeline trace linkage by `correlation_id`.
- AGENTS.md: Work on exactly one task; touch only files listed for the task plus the test file specified by the PM/BA Test Brief; do not create extra files unless explicitly allowed; preserve append-only approvals; do not mark the task DONE unless verification passes.

## Allowed files
- `app/web/templates/base.html`
- `app/web/templates/approvals.html`
- `app/web/routes.py`
- `tests/T24_escalation_polish/`
- `briefs/T24_architect_brief.md`

## Implementation objective
Enhance the existing approval queue into an operational escalation dashboard without changing the underlying approval semantics. The implementer should add a server-rendered pending escalation badge to the global navigation, enrich each approval queue item with operational context, support server-side filtering by required approval role, and provide a trace link for each escalation using the record's `correlation_id` and the trace view introduced in T22.

The goal is presentation and discoverability only: risk users should immediately see how many human decisions are waiting, which role owns each escalation, why the escalation happened, when it happened, and how to inspect the pipeline trace that produced it.

## Non-negotiables
- Do not change approval decision semantics: approve/reject must still require a reason and must still append a new `approval_decision` record linked to the original escalation; never mutate the original `action_evaluation` record.
- The pending badge count must be derived from persisted audit/approval state: count escalated `action_evaluation` records that do not have a linked `approval_decision` record. Do not maintain an in-memory counter.
- The badge may be server-rendered on page load. Do not add live-update infrastructure, background workers, notifications, email alerts, SLA timers, or assignment logic.
- Queue enrichment must use existing record fields and decision/action/context data. Do not add new schemas or alter existing schema fields.
- The trace link must be based on `correlation_id` and should route to the existing T22 trace view/route. Do not invent a separate tracing architecture.
- Role filtering must be server-side and limited to the current required approval roles present in the queue. At minimum, support `All`, `finance_supervisor`, and the data-protection role used by the implemented controls.
- Preserve the calm assurance-dashboard tone: readable timestamps, concise action summaries, clear control ID/reason, clear required role, and obvious trace affordance.
- Tests must be real pytest tests under `tests/T24_escalation_polish/` as specified by the PM/BA Test Brief.

## Verify step
Manual verification from `TASK_LEDGER.md`:
1. Run scenario #2 so it escalates.
2. Confirm the nav bar shows a pending escalation count badge on page navigation.
3. Open the approvals page and confirm the queue item shows timestamp, action summary, triggering control/reason, and required role.
4. Apply a role filter and confirm `finance_supervisor` items are shown while unrelated roles are hidden.
5. Click `View trace` and confirm it opens the T22 pipeline trace for the same evaluation/correlation.
6. Approve with a required reason and confirm the badge count decrements while the append-only approval workflow remains intact.

Programmatic checks expected after implementation:
- Run the T24 pytest file(s) specified by the PM/BA Test Brief.
- Run any existing T16 approval UI tests if practical, to guard against approval workflow regression.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T24_architect_brief.md` and `briefs/T24_test_brief.md`. Implement exactly T24. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
