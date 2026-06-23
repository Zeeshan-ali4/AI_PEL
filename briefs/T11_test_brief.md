# Test Brief — T11: Enforcement handler + approval queue (append-only)

## Spec references
- `MASTER_SPEC.md` §2: default-to-human; uncertainty escalates; fail closed; model/policy split preserved (no policy re-derivation in Python).
- `MASTER_SPEC.md` §5.5: append-only `EvidenceRecord` shape — `record_type` (`action_evaluation` | `approval_decision`), `references_hash`, `human_approver`, `approval_reason`, `executed`. Approval write-back never mutates the original record.
- `MASTER_SPEC.md` §6: precedence `fail_closed > block > escalate > require_evidence > modify > allow_with_logging > allow`; `block` is the PROHIBITED tier only and is a hard stop, never queueable.
- `MASTER_SPEC.md` §8: enforcement modes — shadow (always executes, surfaces "would have X", never queues), soft (enforce allow-listed controls as full, shadow the rest), full (apply real semantics per decision).
- `TASK_LEDGER.md` T11 Goal/Done-when/Verify: handler returns correct `executed`/`queued` per Decision+mode; block in full → not executed, nothing queued; escalate in full → not executed, queued; block in shadow → executed, "would have blocked".
- `briefs/T11_architect_brief.md`: full mode-by-mode semantics, queue item shape, append-only approval recording contract.

## Target test location
- Folder: `tests/T11_enforcement/`
- Suggested files:
  - `test_handler_modes.py` — covers handler behaviour across shadow/soft/full modes for each decision value.
  - `test_approval_queue.py` — covers enqueue, pending lookups, and append-only approval/rejection recording.

## Test cases

### test_block_full_not_executed_not_queued
- **Traces to:** MASTER_SPEC.md §6 prohibited tier; TASK_LEDGER.md T11 Verify step.
- **Input:** `Decision(decision="block", control_id="FIN-PAY-001", ...)` with `EnforcementMode.FULL`.
- **Expected outcome:** `executed is False`; `queued is False`; nothing appears in the approval queue afterward.
- **Notes:** Non-negotiable — block must never reach the queue, in any mode.

### test_escalate_full_not_executed_and_queued_with_role
- **Traces to:** MASTER_SPEC.md §6 escalate tier; TASK_LEDGER.md T11 Verify step.
- **Input:** `Decision(decision="escalate", control_id="FIN-PAY-002", required_approval_role="finance_supervisor", ...)` with `EnforcementMode.FULL`.
- **Expected outcome:** `executed is False`; `queued is True`; the resulting queue item carries `required_approval_role == "finance_supervisor"` and enough decision context (`control_id`, `reason`) to render later.
- **Notes:** Confirms escalation is the only path that reaches the human queue under full enforcement.

### test_block_shadow_executes_with_would_have_blocked_annotation
- **Traces to:** MASTER_SPEC.md §8 shadow mode; TASK_LEDGER.md T11 Verify step.
- **Input:** `Decision(decision="block", control_id="FIN-PAY-001", ...)` with `EnforcementMode.SHADOW`.
- **Expected outcome:** `executed is True`; `queued is False`; outcome carries a "would have blocked" (or equivalent) annotation referencing the underlying decision.
- **Notes:** Core shadow-mode acceptance case named explicitly in the ledger.

### test_escalate_shadow_executes_with_would_have_escalated_annotation_not_queued
- **Traces to:** MASTER_SPEC.md §8 shadow mode; architect brief non-negotiables.
- **Input:** `Decision(decision="escalate", control_id="COMM-EMAIL-001", required_approval_role="data_protection_approver", ...)` with `EnforcementMode.SHADOW`.
- **Expected outcome:** `executed is True`; `queued is False`; "would have escalated" annotation present; approval queue remains empty after the call.
- **Notes:** Shadow never queues, even for escalate.

### test_allow_full_executed_not_queued
- **Traces to:** MASTER_SPEC.md §6 allow path.
- **Input:** `Decision(decision="allow", control_id=None, ...)` with `EnforcementMode.FULL`.
- **Expected outcome:** `executed is True`; `queued is False`; no shadow annotation (annotation is null/None since mode is not shadow, or decision matches what would actually happen).
- **Notes:** Confirms baseline non-risk path is unaffected by handler logic.

### test_allow_with_logging_full_executed_not_queued
- **Traces to:** MASTER_SPEC.md §6 `allow_with_logging`.
- **Input:** `Decision(decision="allow_with_logging", control_id="COMM-EMAIL-003", ...)` with `EnforcementMode.FULL`.
- **Expected outcome:** `executed is True`; `queued is False`.
- **Notes:** Logging-only path executes normally; logging itself is out of scope for T11 (handled by audit store in T12/T13).

### test_fail_closed_full_not_executed_not_queued
- **Traces to:** MASTER_SPEC.md §2 fail closed; architect brief mode logic for `fail_closed`.
- **Input:** `Decision(decision="fail_closed", control_id=None, ...)` with `EnforcementMode.FULL`.
- **Expected outcome:** `executed is False`; `queued is False`.
- **Notes:** Safe default; not an escalation, must not appear in the queue.

### test_fail_closed_shadow_executes_with_would_have_failed_closed_annotation
- **Traces to:** MASTER_SPEC.md §8 shadow mode; architect brief shadow semantics ("any decision that would not have been allow/allow_with_logging under full").
- **Input:** `Decision(decision="fail_closed", ...)` with `EnforcementMode.SHADOW`.
- **Expected outcome:** `executed is True`; `queued is False`; shadow annotation present.
- **Notes:** Confirms shadow annotation logic generalises beyond block/escalate.

### test_soft_mode_enforced_control_applies_full_semantics
- **Traces to:** MASTER_SPEC.md §8 soft mode; architect brief soft-mode definition.
- **Input:** `Decision(decision="escalate", control_id="FIN-PAY-002", required_approval_role="finance_supervisor", ...)` with `EnforcementMode.SOFT` and a `control_modes` mapping where `FIN-PAY-002` is on the allow-list (treated as full).
- **Expected outcome:** `executed is False`; `queued is True`, matching full-mode escalate behaviour for this control.
- **Notes:** Verifies soft mode honours per-control allow-listing, not a single global mode.

### test_soft_mode_unenforced_control_falls_back_to_shadow_behaviour
- **Traces to:** MASTER_SPEC.md §8 soft mode; architect brief soft-mode definition.
- **Input:** `Decision(decision="block", control_id="FIN-PAY-001", ...)` with `EnforcementMode.SOFT` and a `control_modes` mapping where `FIN-PAY-001` is **not** on the allow-list.
- **Expected outcome:** `executed is True`; `queued is False`; a "would have blocked" annotation is present (shadow-style fallback).
- **Notes:** Confirms soft mode's per-control fallback to shadow semantics for controls not explicitly enforced.

### test_require_evidence_and_modify_full_default_to_not_executed_not_queued
- **Traces to:** architect brief non-negotiables on `require_evidence`/`modify` (no invented queue semantics).
- **Input:** `Decision(decision="require_evidence", ...)` and separately `Decision(decision="modify", ...)`, both with `EnforcementMode.FULL`.
- **Expected outcome:** For each, `executed is False`; `queued is False`.
- **Notes:** Documents the conservative default chosen by the architect brief rather than inventing new queue behaviour.

### test_enqueue_creates_pending_item_with_required_fields
- **Traces to:** MASTER_SPEC.md §5.5; architect brief approval_queue interface.
- **Input:** Call `approval_queue.enqueue(...)` directly with a `correlation_id`, `control_id`, `required_approval_role`, `reason`, and decision context.
- **Expected outcome:** Returns/stores an item with a stable identifier; the item appears in the "pending" listing; all input fields are retrievable from the stored item unchanged.
- **Notes:** Unit-level check of the queue's own contract, independent of the handler.

### test_pending_lookup_excludes_actioned_items
- **Traces to:** architect brief — "list/lookup helpers for pending items (i.e. items with no linked approval/rejection yet)".
- **Input:** Enqueue two items; record an approval decision against one via `record_approval_decision(...)`.
- **Expected outcome:** The "pending" listing afterward contains only the un-actioned item; the actioned item is excluded from pending but still retrievable in full history/lookup.
- **Notes:** Confirms append-only semantics are reflected in queue query helpers, not just storage.

### test_approve_appends_linked_record_without_mutating_original
- **Traces to:** MASTER_SPEC.md §5.5 append-only approvals; TASK_LEDGER.md golden rule 5.
- **Input:** Enqueue an escalation item; capture its original state (deep copy/snapshot); call `record_approval_decision(item_id, approved=True, human_approver="alice", reason="verified with customer")`.
- **Expected outcome:** A new record is returned/stored distinct from the original queue item; it carries `human_approver="alice"`, `approval_reason="verified with customer"`, and `executed` reflecting approval (True); the original queued item's stored fields are unchanged (no in-place field mutation) when re-fetched/compared to the snapshot.
- **Notes:** This is the core non-negotiable for T11's queue half — no mutation of the original record under any circumstance.

### test_reject_appends_linked_record_with_executed_false
- **Traces to:** MASTER_SPEC.md §5.5; architect brief approval_queue interface.
- **Input:** Enqueue an escalation item; call `record_approval_decision(item_id, approved=False, human_approver="bob", reason="insufficient justification")`.
- **Expected outcome:** A new linked record is created with `human_approver="bob"`, `approval_reason="insufficient justification"`, and `executed is False`; original item remains unchanged.
- **Notes:** Mirrors the approve case for the rejection path.

### test_approval_record_carries_no_real_hash_placeholder
- **Traces to:** architect brief — "`references_hash=None` for now (T11 has no real hash yet — that's T12)".
- **Input:** Any `record_approval_decision(...)` call.
- **Expected outcome:** The returned record's `references_hash` (or equivalent field) is `None`/absent — T11 must not fabricate a hash value.
- **Notes:** Guards against premature/incorrect hash logic leaking into T11 ahead of T12.

## Coverage checklist
- [ ] Happy path covered: allow / allow_with_logging execute cleanly in full mode; escalate queues correctly.
- [ ] Error/edge cases covered: block (hard stop) never queued in any mode; fail_closed, require_evidence, modify defaults; soft-mode per-control allow-listing both branches.
- [ ] Spec non-negotiables verified: block never reaches queue; escalate always queues under enforcing modes; shadow never queues and always executes; approval write-back is append-only with no mutation.
- [ ] Real dependencies flagged: none required — T11 is pure in-memory logic; no OPA/Presidio/Postgres calls. Tests must construct `Decision`/`EnforcementMode` objects directly via the real Pydantic schemas from `app.schemas.decision` and `app.schemas.action` (not mocked schema substitutes).

## Gaps or ambiguities
- The architect brief leaves the exact shape of the handler's "would have X" annotation and the queue item's identifier scheme to the Implementer's discretion. Tests should assert on the presence and semantic content of these fields (e.g., that the annotation names the underlying decision value) rather than an exact string format, unless the Implementer documents one.
- `require_evidence` and `modify` handling is explicitly conservative/under-specified per the architect brief; tests lock in the documented default (`executed=False, queued=False`) rather than inventing additional queue behaviour. If the Implementer deviates, QA should flag for spec clarification rather than silently accepting a new contract.