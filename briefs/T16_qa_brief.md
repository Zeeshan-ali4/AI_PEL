# QA Report — T16: Approval queue view

## Verdict
PASS

## Ledger verification
- Command run: `pytest tests/T16_approvals_ui` (real `opa` binary v1.17.1 started against `opa/`, real Presidio/spaCy, real sqlite-backed `AuditStore` — no Docker/Postgres daemon was available in this environment, so the project's literal `docker compose run --rm app pytest ...` could not be invoked verbatim; the equivalent real-dependency path was exercised directly via a local Python venv + a downloaded `opa` static binary).
- Result: passed — 6/6 tests passed.
- Manual smoke (`curl /scenarios/2/run` then `/approvals` against a running `uvicorn` instance) failed with `psycopg.OperationalError` because the app's `AuditStore` resolves Postgres connection settings unconditionally outside of test fixtures, and no Postgres service is reachable in this environment. This is an environment limitation (no Docker daemon, no Postgres), not a defect in T16 — the equivalent flow (run Scenario 2 → escalation queued → approve/reject → append-only verification) is exercised end-to-end by the automated test suite against a real sqlite-backed `AuditStore` and real OPA, per the T15-established test pattern.

## Test suite results
- Command run: `pytest tests/T16_approvals_ui/ -v` (and full `pytest tests/ -q` for regression)
- Total: 6 | Passed: 6 | Failed: 0 | Errors: 0
- Full repo suite: 177 passed, 2 skipped, 0 failed.
- Output summary:
```
tests/T16_approvals_ui/test_approvals_ui.py::test_scenario_2_escalation_appears_in_approval_queue PASSED
tests/T16_approvals_ui/test_approvals_ui.py::test_approve_requires_non_empty_reason_and_does_not_append_when_blank PASSED
tests/T16_approvals_ui/test_approvals_ui.py::test_approve_with_reason_appends_linked_approval_decision_and_marks_item_actioned PASSED
tests/T16_approvals_ui/test_approvals_ui.py::test_reject_with_reason_appends_linked_rejection_decision_without_execution PASSED
tests/T16_approvals_ui/test_approvals_ui.py::test_reject_requires_non_empty_reason_and_preserves_pending_item PASSED
tests/T16_approvals_ui/test_approvals_ui.py::test_approval_view_does_not_invoke_or_reclassify_semantic_evidence_for_payment PASSED
6 passed, 1 warning in 0.90s
```

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_approvals_ui.py` | `tests/T16_approvals_ui/test_approvals_ui.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| test_scenario_2_escalation_appears_in_approval_queue | `test_scenario_2_escalation_appears_in_approval_queue` | test_approvals_ui.py | yes | Confirms escalate/FIN-PAY-002/finance_supervisor, £850/CUST-100 visible, Approve/Reject controls present. |
| test_approve_requires_non_empty_reason_and_does_not_append_when_blank | `test_approve_requires_non_empty_reason_and_does_not_append_when_blank` | test_approvals_ui.py | yes | Verifies no audit write and original record byte-for-byte unchanged on blank reason. |
| test_approve_with_reason_appends_linked_approval_decision_and_marks_item_actioned | `test_approve_with_reason_appends_linked_approval_decision_and_marks_item_actioned` | test_approvals_ui.py | yes | Verifies exactly one new `approval_decision` row, `references_hash`, `human_approver`, `approval_reason`, `executed=true`, chain stays intact, item no longer pending. |
| test_reject_with_reason_appends_linked_rejection_decision_without_execution | `test_reject_with_reason_appends_linked_rejection_decision_without_execution` | test_approvals_ui.py | yes | Verifies append-only rejection, `executed=false`, original unchanged, chain intact. |
| test_reject_requires_non_empty_reason_and_preserves_pending_item | `test_reject_requires_non_empty_reason_and_preserves_pending_item` | test_approvals_ui.py | yes | Verifies blank-reason reject leaves item pending and appends nothing. |
| test_approval_view_does_not_invoke_or_reclassify_semantic_evidence_for_payment | `test_approval_view_does_not_invoke_or_reclassify_semantic_evidence_for_payment` | test_approvals_ui.py | yes | Confirms `evidence.evaluated is False` preserved on both original and appended records; no decision/approval fields added to Evidence. |

### Extra tests (Implementer-added)
- None beyond the six brief-specified cases.

## Spec non-negotiable checks
- Evidence schema has no allow/block/decision/approval field (unchanged in this task; spot-checked `app/schemas/evidence.py` not modified by the T16 diff): passed.
- No OPA/Rego, schema, or settings-store files touched by T16 diff (`git diff --stat` against pre-T16 HEAD shows only `app/web/routes.py`, `app/web/templates/approvals.html`, and the `tests/T16_approvals_ui/` files): passed.
- Append-only audit behaviour: original `action_evaluation` record (`record_hash`, `executed`, `created_at`) is unchanged after approve/reject in all four scenarios tested (valid approve, valid reject, blank-reason approve, blank-reason reject): passed.
- `references_hash` linkage and shared `correlation_id` between appended `approval_decision` and original `action_evaluation`: passed.
- Hash chain verifies as intact after append (`verify_chain()` checked post-approval in test): passed.
- Reason is mandatory server-side (not just HTML `required`) for both Approve and Reject: passed.
- Payment scenario never invokes the semantic layer; `evidence.evaluated=false` preserved through the approval flow: passed.
- File scope discipline: implementation touched only the three allowed files (`app/web/routes.py`, `app/web/templates/approvals.html`) plus the T16 test subfolder — no extra files created: passed.

## Failures
None.

## Recommendation
Proceed to human approval. Automated verification (real OPA binary, real Presidio/spaCy, real sqlite-backed append-only `AuditStore`) is green for all 6 T16 acceptance tests and the full 177-test repo regression suite. The literal ledger verify command (`docker compose run --rm app pytest tests/T16_approvals_ui`) could not be executed in this environment because no Docker daemon was available; the human gate should re-run that exact command once Docker is available to close out the formality, but no functional risk was found — the equivalent real-dependency path was exercised directly.
