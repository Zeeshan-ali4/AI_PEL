# Architect Brief — T11: Enforcement handler + approval queue (append-only)

## Task selected
- Task: T11 — Enforcement handler + approval queue (append-only)
- Current status: To do
- Dependencies checked: pass — T11 depends on T10, and `TASK_LEDGER.md` marks T10 as Done. Current build state says current task is T11 and last completed task is T10.

## Source-of-truth references
- `MASTER_SPEC.md` §2: default-to-human; uncertainty escalates; fail closed; the model/policy split is preserved (this task touches no Evidence fields).
- `MASTER_SPEC.md` §5.5: append-only `EvidenceRecord` shape — `record_type` (`action_evaluation` | `approval_decision`), `references_hash` (approval rows point back at the original record's hash via `correlation_id` + `references_hash`), `human_approver`, `approval_reason`, `executed`. "Append-only approvals: an escalation writes an `action_evaluation` record with `executed=false`. When a human approves/rejects, append a new `approval_decision` record... Never update the original row."
- `MASTER_SPEC.md` §6: precedence — `fail_closed > block > escalate > require_evidence > modify > allow_with_logging > allow`. `block` is the PROHIBITED tier only (FIN-PAY-001) and is a hard stop, not a queueable item.
- `MASTER_SPEC.md` §8: enforcement modes —
  - **shadow**: evaluate fully, write the record, but **always execute**; surface "would have blocked/escalated/etc." rather than actually enforcing.
  - **soft**: enforce only controls on an allow-list (from settings/config); shadow the rest.
  - **full**: enforce all controls per their decision.
- `TASK_LEDGER.md` T11: "Apply a Decision under a mode... determine `executed`; route `escalate` to an in-app approval queue with the `required_approval_role`. Approve/Reject appends a linked `approval_decision` record (no mutation)." The actual record-writing/persistence is T12 — T11 defines the interfaces and the executed/queued logic only; approval write-back is wired to the real store in T13.
- `TASK_LEDGER.md` T11 Done when / Verify: "given each Decision + mode, handler returns correct `executed` and queue state; shadow forces execution with a 'would have X' flag." Unit checks: block in full → not executed + nothing queued; escalate in full → not executed + queued; block in shadow → executed + "would have blocked".
- `TASK_LEDGER.md` T11 Reviewer focus: prohibited `block` does **not** go to the human approval queue (hard stop, distinct from escalation); escalations do go to the queue; shadow logic is correct.
- `AGENTS.md`: work on exactly one task; touch only the files listed below plus the PM/BA-specified test file under `tests/`; audit records are append-only and human approvals append a new `approval_decision` record — never mutate; do not change schemas, file layout, control IDs, scenario outcomes, or policy logic.

## Allowed files
- `app/enforcement/handler.py`
- `app/enforcement/approval_queue.py`
- `tests/T11_enforcement/`

Implementer must not edit files outside this T11 allowed list plus the target test file specified by the PM/BA Test Brief. No new top-level packages, no edits to `app/schemas/*`, `opa/*`, or `app/policy/opa_client.py`.

## Implementation objective

Build the enforcement layer that sits between the OPA `Decision` (T10) and the audit store (T12, not yet wired). T11 defines **interfaces and logic only** — there is no real persistence yet; the approval queue and handler operate on in-memory/returned data structures that T13 will later back with the real audit store.

### `app/enforcement/handler.py`
- Expose a function/class (e.g. `enforce(decision: Decision, enforcement_mode: EnforcementMode, ...) -> EnforcementOutcome`) that takes a `Decision` (from `app.schemas.decision`) and an `EnforcementMode` (from `app.schemas.action`) and returns a small result object capturing:
  - `executed: bool`
  - `queued: bool` (whether this decision was routed to the approval queue)
  - `would_have` / shadow annotation describing what *would* have happened if enforcement were live (used only in `shadow` mode; null/None otherwise)
  - enough of the original decision context to hand to `approval_queue` when `queued=True` (e.g. `control_id`, `required_approval_role`, `reason`)
- Mode logic (exact, per §8 and the ledger's Verify step):
  - **shadow**: `executed = True` always. If the underlying decision would have blocked/escalated/modified/required-evidence in `full` mode, attach a "would have {decision}" annotation. Never enqueues to the approval queue (nothing is actually escalated in shadow — it is observed only).
  - **soft**: enforce only controls present in an allow-list (read from the per-control mode config consumed elsewhere — accept it as a parameter, e.g. `control_modes: dict[str, EnforcementMode]` or similar, keyed by `decision.control_id`/`triggered_controls`); for controls not on the allow-list, fall back to shadow-style behaviour (execute + "would have X", no queueing). For controls on the allow-list, apply `full` semantics below.
  - **full**: apply real semantics per decision value:
    - `decision == "block"` → `executed = False`, `queued = False` (hard stop; this is **not** an escalation, so it must never appear in the approval queue).
    - `decision == "escalate"` → `executed = False`, `queued = True`, hand off to `approval_queue` with `required_approval_role`.
    - `decision == "require_evidence"` / `"modify"` → treat as not-executed pending further handling (no queueing required by this task unless trivially natural — do not invent new queue semantics beyond what the Done-when/Verify step requires; if ambiguous, default to `executed=False, queued=False` and document the rationale in code, since the ledger's acceptance checks only cover block/escalate/shadow-block).
    - `decision == "allow_with_logging"` / `"allow"` → `executed = True`, `queued = False`.
    - `decision == "fail_closed"` → `executed = False`, `queued = False` (safe default; not an escalation).
- Do not write to any store. Do not import or call anything from T12 (audit store does not exist yet) or T13 (pipeline does not exist yet).
- Keep all decision/precedence logic exactly as OPA already produced it — this handler reacts to `decision.decision`, it does not re-derive policy.

### `app/enforcement/approval_queue.py`
- An in-memory append-only queue abstraction (a real persistent backing comes later; do not anticipate the DB schema beyond what's needed to satisfy the interface). Define:
  - A queue item shape carrying at least: `correlation_id`, `control_id`, `required_approval_role`, `reason`, `decision` (or enough decision fields to render later), `created_at`, and a stable identifier for the queued item.
  - `enqueue(...)` — adds a new pending item. Append-only: queued items are never mutated in place.
  - A way to record an approval/rejection that **appends** a new linked record rather than mutating the original queued item — e.g. `record_approval_decision(item_id, approved: bool, human_approver: str, reason: str) -> <approval record>`. This returned record should carry enough fields to map cleanly onto the future `EvidenceRecord` with `record_type="approval_decision"`, `references_hash=None` for now (T11 has no real hash yet — that's T12), and the resulting `executed` state.
  - List/lookup helpers for "pending" items (i.e. items with no linked approval/rejection yet) — needed by the future approvals UI (T16) but only the minimal in-memory contract here.
  - Do not implement a database table, SQLAlchemy model, or hash chaining here — that is T12's job. Keep this an in-process structure (e.g. a list/dict) that later tasks will replace or wrap with real storage.

## Non-negotiables
- The prohibited `block` decision must never reach the approval queue under any mode. It is a hard stop, distinct from `escalate`.
- `escalate` must always route to the queue under `full` (and under `soft` when the triggered control is enforced).
- `shadow` mode always executes, never queues, and must surface a clear "would have X" signal for any decision that would not have been `allow`/`allow_with_logging` under full enforcement.
- Approval write-back is append-only: approving/rejecting a queued item must create a **new** linked record, never mutate the original queued/decision data.
- No policy/precedence logic may be re-implemented or second-guessed in Python — this handler trusts `decision.decision` as already resolved by OPA (T10).
- Do not touch `app/schemas/*`, `opa/*`, `app/policy/opa_client.py`, or any file outside the T11 allowed list.
- No real persistence, audit hash chaining, or DB models in T11 — those belong to T12/T13.

## Verify step
Per the ledger:
- Block in `full` → `executed=False`, `queued=False`.
- Escalate in `full` → `executed=False`, `queued=True`, queue item carries `required_approval_role`.
- Block in `shadow` → `executed=True`, with a "would have blocked" annotation, and `queued=False`.

Implementer should support these as concrete unit-style pytest cases in `tests/T11_enforcement/`, plus: escalate in `shadow` (`executed=True`, "would have escalated", not queued); allow/allow_with_logging in `full` (`executed=True`, `queued=False`); approving a queued item appends a new approval record without mutating the original queue entry; rejecting likewise appends a new record with `executed=False`.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T11_architect_brief.md` and `briefs/T11_test_brief.md`. Implement exactly T11. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.