# QA Report — T11: Enforcement handler + approval queue (append-only)

## Verdict
PASS

## Ledger verification
- Command run: unit-style check via `pytest tests/T11_enforcement/ -v` (no Docker required — T11 is pure in-memory logic per spec/test brief; no OPA/Presidio/Postgres dependency in scope).
- Result: passed. Confirmed manually that: block in full → not executed, nothing queued; escalate in full → not executed, queued with role; block in shadow → executed, "would have blocked" annotation present.

## Test suite results
- Command run: `python3 -m pytest tests/T11_enforcement/ -v`
- Total: 17 | Passed: 17 | Failed: 0 | Errors: 0
- Output summary:
```
tests/T11_enforcement/test_approval_queue.py::test_enqueue_creates_pending_item_with_required_fields PASSED
tests/T11_enforcement/test_approval_queue.py::test_pending_lookup_excludes_actioned_items PASSED
tests/T11_enforcement/test_approval_queue.py::test_approve_appends_linked_record_without_mutating_original PASSED
tests/T11_enforcement/test_approval_queue.py::test_reject_appends_linked_record_with_executed_false PASSED
tests/T11_enforcement/test_approval_queue.py::test_approval_record_carries_no_real_hash_placeholder PASSED
tests/T11_enforcement/test_handler_modes.py::test_block_full_not_executed_not_queued PASSED
tests/T11_enforcement/test_handler_modes.py::test_escalate_full_not_executed_and_queued_with_role PASSED
tests/T11_enforcement/test_handler_modes.py::test_block_shadow_executes_with_would_have_blocked_annotation PASSED
tests/T11_enforcement/test_handler_modes.py::test_escalate_shadow_executes_with_would_have_escalated_annotation_not_queued PASSED
tests/T11_enforcement/test_handler_modes.py::test_allow_full_executed_not_queued PASSED
tests/T11_enforcement/test_handler_modes.py::test_allow_with_logging_full_executed_not_queued PASSED
tests/T11_enforcement/test_handler_modes.py::test_fail_closed_full_not_executed_not_queued PASSED
tests/T11_enforcement/test_handler_modes.py::test_fail_closed_shadow_executes_with_would_have_failed_closed_annotation PASSED
tests/T11_enforcement/test_handler_modes.py::test_soft_mode_enforced_control_applies_full_semantics PASSED
tests/T11_enforcement/test_handler_modes.py::test_soft_mode_unenforced_control_falls_back_to_shadow_behaviour PASSED
tests/T11_enforcement/test_handler_modes.py::test_require_evidence_and_modify_full_default_to_not_executed_not_queued[require_evidence] PASSED
tests/T11_enforcement/test_handler_modes.py::test_require_evidence_and_modify_full_default_to_not_executed_not_queued[modify] PASSED
17 passed in 0.24s
```

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| test_handler_modes.py | tests/T11_enforcement/test_handler_modes.py | ok |
| test_approval_queue.py | tests/T11_enforcement/test_approval_queue.py | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| test_block_full_not_executed_not_queued | test_block_full_not_executed_not_queued | test_handler_modes.py | yes | Asserts executed/queued False and `queue.list_pending() == []` |
| test_escalate_full_not_executed_and_queued_with_role | test_escalate_full_not_executed_and_queued_with_role | test_handler_modes.py | yes | Asserts role, control_id, reason carried onto queue_item |
| test_block_shadow_executes_with_would_have_blocked_annotation | test_block_shadow_executes_with_would_have_blocked_annotation | test_handler_modes.py | yes | Annotation contains "block"; queue stays empty |
| test_escalate_shadow_executes_with_would_have_escalated_annotation_not_queued | test_escalate_shadow_executes_with_would_have_escalated_annotation_not_queued | test_handler_modes.py | yes | Confirms shadow never queues even for escalate |
| test_allow_full_executed_not_queued | test_allow_full_executed_not_queued | test_handler_modes.py | yes | `would_have is None` also asserted |
| test_allow_with_logging_full_executed_not_queued | test_allow_with_logging_full_executed_not_queued | test_handler_modes.py | yes | |
| test_fail_closed_full_not_executed_not_queued | test_fail_closed_full_not_executed_not_queued | test_handler_modes.py | yes | |
| test_fail_closed_shadow_executes_with_would_have_failed_closed_annotation | test_fail_closed_shadow_executes_with_would_have_failed_closed_annotation | test_handler_modes.py | yes | Annotation generalises beyond block/escalate, as required |
| test_soft_mode_enforced_control_applies_full_semantics | test_soft_mode_enforced_control_applies_full_semantics | test_handler_modes.py | yes | Allow-listed control in soft mode behaves as full |
| test_soft_mode_unenforced_control_falls_back_to_shadow_behaviour | test_soft_mode_unenforced_control_falls_back_to_shadow_behaviour | test_handler_modes.py | yes | Non-allow-listed control falls back to shadow-style annotation |
| test_require_evidence_and_modify_full_default_to_not_executed_not_queued | test_require_evidence_and_modify_full_default_to_not_executed_not_queued (parametrized, 2 cases) | test_handler_modes.py | yes | Brief explicitly allows combining both decision values into one test; parametrization covers both cleanly |
| test_enqueue_creates_pending_item_with_required_fields | test_enqueue_creates_pending_item_with_required_fields | test_approval_queue.py | yes | All input fields retrievable unchanged; item appears in `list_pending()` |
| test_pending_lookup_excludes_actioned_items | test_pending_lookup_excludes_actioned_items | test_approval_queue.py | yes | Actioned item excluded from pending, still retrievable via `get()` |
| test_approve_appends_linked_record_without_mutating_original | test_approve_appends_linked_record_without_mutating_original | test_approval_queue.py | yes | Uses deep-copy snapshot comparison to prove no mutation |
| test_reject_appends_linked_record_with_executed_false | test_reject_appends_linked_record_with_executed_false | test_approval_queue.py | yes | Mirrors approve case; `executed is False` |
| test_approval_record_carries_no_real_hash_placeholder | test_approval_record_carries_no_real_hash_placeholder | test_approval_queue.py | yes | `references_hash is None` asserted |

All 16 named brief test cases are present (the require_evidence/modify case is one parametrized brief entry implemented as 2 test instances — matches the brief's own framing of it as a single case covering two inputs). Total test functions: 17 (16 brief cases + 1 extra parametrize instance counted separately by pytest).

### Extra tests (Implementer-added)
- None beyond the parametrization of the require_evidence/modify case (which is brief-specified, not an addition).

## Spec non-negotiable checks
- Evidence schema has no decision/enforcement/approval fields: passed (not touched by T11; grep of `app/schemas/evidence.py` for decision/allow/block/escalate returns no matches).
- No policy logic in Python — handler only branches on `decision.decision` already resolved by OPA, does not re-derive policy: passed (confirmed by reading `app/enforcement/handler.py`; no OPA/audit-store imports).
- Real components stay real / stubs labelled: not applicable to T11 — pure in-memory logic, no real-component dependency (per test brief's own coverage checklist, which states "none required").
- Append-only approvals, no mutation of original record: passed (`test_approve_appends_linked_record_without_mutating_original` and `test_reject_appends_linked_record_with_executed_false` confirm `record_approval_decision` only appends to `_approval_records`, never writes back into `_items`).
- `block` never reaches the human queue under any mode: passed (`test_block_full_not_executed_not_queued`, `test_block_shadow_executes_with_would_have_blocked_annotation`, `test_soft_mode_unenforced_control_falls_back_to_shadow_behaviour` all confirm block is absent from queueing path).
- `references_hash=None` not fabricated ahead of T12: passed (`test_approval_record_carries_no_real_hash_placeholder`).

## Failures
- None.

## Recommendation
Proceed to human approval. All 17 tests pass, every test-brief case is covered with matching inputs/assertions, file structure matches the brief's suggested split, and the spec non-negotiables relevant to T11's scope (append-only approvals, block never queued, no policy re-derivation in Python, no Evidence-schema decision leakage) are verified. Reviewer brief (`briefs/T11_reviewer_brief.md`) independently reached PASS with consistent findings.