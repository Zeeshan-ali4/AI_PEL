# Reviewer Brief — T11: Enforcement handler + approval queue (append-only)

## Files reviewed
- `app/enforcement/handler.py`
- `app/enforcement/approval_queue.py`
- `tests/T11_enforcement/test_handler_modes.py`
- `tests/T11_enforcement/test_approval_queue.py`

## Verification performed
Ran `python -m pytest tests/T11_enforcement/ -v`: **17/17 passed.**

## Against the architect brief
- File scope respected: only `app/enforcement/handler.py`, `app/enforcement/approval_queue.py`, and `tests/T11_enforcement/` were touched. No edits to `app/schemas/*`, `opa/*`, or `app/policy/opa_client.py`.
- `enforce()` takes a `Decision` (`app.schemas.decision`) and `EnforcementMode` (`app.schemas.action`) and returns an `EnforcementOutcome` carrying `executed`, `queued`, `would_have`, `decision`, `control_id`, `required_approval_role`, `reason`, `queue_item` — matches the brief's required fields.
- No re-derivation of policy: the handler only branches on `decision.decision` as already resolved by OPA (T10). No persistence, no OPA/audit-store imports.

## Mode semantics — verified correct
- **shadow** (`_apply_shadow_semantics`): always `executed=True`, `queued=False`; annotates `"would have {decision}"` for block/escalate/require_evidence/modify/fail_closed, `None` for allow/allow_with_logging. Matches §8 and the ledger's Verify step exactly.
- **soft** (`enforce`, SOFT branch): consults `control_modes` keyed by `control_id`; only `EnforcementMode.FULL` for that control applies real (full) semantics, everything else falls back to shadow-style behaviour. Matches the brief's per-control allow-list definition.
- **full** (`_apply_full_semantics`):
  - `block` → `executed=False, queued=False`, never enqueued. **Confirmed non-negotiable**: prohibited tier is a hard stop, distinct from escalation, never reaches the queue.
  - `escalate` → `executed=False, queued=True`, enqueues via `approval_queue.enqueue(...)` carrying `required_approval_role`, `control_id`, `reason`, and the full `Decision`.
  - `require_evidence` / `modify` / `fail_closed` → conservative default `executed=False, queued=False`, with an inline comment documenting the rationale, as the architect brief required when ambiguous.
  - `allow` / `allow_with_logging` → `executed=True, queued=False`.

## Approval queue — verified correct
- `ApprovalQueue` is in-memory (`dict[str, QueueItem]` + `dict[str, list[ApprovalDecisionRecord]]`), no DB model, no hash chaining — correctly deferred to T12/T13.
- `enqueue()` only ever adds; nothing mutates a stored `QueueItem`.
- `record_approval_decision()` **appends** a new `ApprovalDecisionRecord` to a list keyed by `item_id` rather than mutating the original item — confirmed by `test_approve_appends_linked_record_without_mutating_original` and the rejection mirror test.
- `list_pending()` excludes any `item_id` with at least one linked approval record — correct append-only "pending" semantics.
- `references_hash=None` on every `ApprovalDecisionRecord` — correctly deferred to T12, not fabricated early (`test_approval_record_carries_no_real_hash_placeholder` passes).

## Against MASTER_SPEC.md
- §5.5 append-only approvals: satisfied — approval/rejection always appends, original `QueueItem` never mutated.
- §6 precedence / prohibited tier: `block` is a hard stop, never queued, in any mode — satisfied.
- §8 enforcement modes (shadow/soft/full): all three implemented per spec wording, including soft's per-control allow-list and shadow's "would have X" UI signal groundwork.
- Non-negotiables in `AGENTS.md` (no Evidence-schema fields touched, no policy re-derivation in Python, audit append-only, human approvals append a new record) — all respected; this task introduces no Evidence schema or persistence code at all.

## Test coverage vs. PM/BA test brief
All 16 named test cases in `briefs/T11_test_brief.md` are present and passing, plus the brief's parametrized `require_evidence`/`modify` case is implemented as a single parametrized test (2 cases) — 17 total test functions. No gaps found relative to the brief's coverage checklist.

## Issues found
None blocking. Two minor, non-blocking observations for future tasks (no action required for T11):
1. `EnforcementOutcome` is a `pydantic.BaseModel`; this is consistent with the rest of the codebase's schema style and fine to keep.
2. The `would_have` annotation string format (`"would have {decision.value}"`) is implementation-chosen, as the architect brief explicitly left this to the Implementer's discretion — acceptable.

## Reviewer focus items (from TASK_LEDGER.md) — all satisfied
- Prohibited `block` does not go to the human queue: **confirmed** (`test_block_full_not_executed_not_queued`, plus block is absent from `_NON_EXECUTING_DECISIONS` queueing path entirely).
- Escalations do go to the queue: **confirmed** (`test_escalate_full_not_executed_and_queued_with_role`).
- Shadow logic correct: **confirmed** across block/escalate/fail_closed shadow tests.

## Verdict
**PASS.** Recommend QA proceed to validate test-brief coverage and run the full Verify step from `TASK_LEDGER.md`.