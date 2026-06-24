# Test Brief — T16: Approval queue view

## Spec references
- `MASTER_SPEC.md` §5.5 Evidence Record: approval decisions must be append-only `approval_decision` records linked to the original `action_evaluation` by `correlation_id` and `references_hash`; the original audit record must not be mutated.
- `MASTER_SPEC.md` §7 Scenario table: Scenario 2 (`Payment £850`, `CUST-100`, no approval) must resolve to `escalate` for `finance_supervisor` under control `FIN-PAY-002`.
- `MASTER_SPEC.md` §8A item 4 Approval queue: pending escalations must show role, action summary, and evidence; Approve/Reject must require a reason; decisions append a new linked approval record.
- `MASTER_SPEC.md` §12 Acceptance criteria: approving an escalation appends a linked approval decision with approver and reason, and the audit chain remains verifiable.
- `TASK_LEDGER.md` T16 acceptance criteria: run #2 → see queue item → approve with reason → audit log shows two linked records, original intact.

## Target test location
- Folder: `tests/T16_approvals_ui/`
- Suggested files:
  - `test_approvals_ui.py` — covers approval queue rendering, mandatory reason validation, approve/reject append-only audit behaviour, and actioned state.

## Test cases

### test_scenario_2_escalation_appears_in_approval_queue
- **Traces to:** `MASTER_SPEC.md` §7 Scenario 2; §8A item 4; `TASK_LEDGER.md` T16 done condition.
- **Input:** Use the FastAPI test client to run Scenario 2 through the existing scenario run endpoint, then request `GET /approvals`.
- **Expected outcome:**
  - The Scenario 2 run response or redirect produces an `escalate` decision with `required_approval_role == "finance_supervisor"` and control `FIN-PAY-002`.
  - `GET /approvals` returns HTTP 200.
  - The rendered page includes a pending queue item for `finance_supervisor`.
  - The page includes a readable payment/action summary sufficient to identify Scenario 2, including payment amount `850` or `£850`, customer/resource context such as `CUST-100`, and the control/reason for `FIN-PAY-002`.
  - The page exposes Approve and Reject controls for the pending item.
- **Notes:** This should exercise the real in-process pipeline/approval queue path used by the UI, not a mocked queue. If the app's tests already use isolated temporary stores/settings, follow that pattern to avoid dependence on prior test data.

### test_approve_requires_non_empty_reason_and_does_not_append_when_blank
- **Traces to:** `MASTER_SPEC.md` §8A item 4; `TASK_LEDGER.md` T16 reviewer focus.
- **Input:** Run Scenario 2 to create a pending escalation, capture the audit record count and original `action_evaluation` record details, then submit the approval form with `decision=approve` and a blank or whitespace-only `reason`.
- **Expected outcome:**
  - The form submission returns a validation response appropriate to the existing UI convention, either HTTP 400/422 or HTTP 200 with a visible validation error.
  - The rendered response or follow-up `GET /approvals` clearly tells the user that a reason is required.
  - No new `approval_decision` record is appended.
  - The original `action_evaluation` record remains unchanged, including its original `record_hash`, `executed` value, `record_type`, `decision`, and `created_at`.
  - The pending item remains pending because no valid approval/rejection occurred.
- **Notes:** The assertion must check persisted audit records, not only the HTML response. Reason validation applies to both approval outcomes; this test covers the approval path and the separate reject test below covers rejection.

### test_approve_with_reason_appends_linked_approval_decision_and_marks_item_actioned
- **Traces to:** `MASTER_SPEC.md` §5.5 append-only approvals; §8A item 4; §12 acceptance criteria; `TASK_LEDGER.md` T16 verify step.
- **Input:** Run Scenario 2 to create a pending escalation. Submit the approval form with `decision=approve`, a non-empty reason such as `Customer remediation approved by finance supervisor`, and a human approver value if the implemented form accepts one.
- **Expected outcome:**
  - Exactly one new audit record of `record_type == "approval_decision"` is appended for the same `correlation_id` as the original Scenario 2 `action_evaluation`.
  - The approval record has `references_hash == original.record_hash`.
  - The approval record has `human_approver` populated, either from the submitted form or from the stable demo default.
  - The approval record has `approval_reason` exactly matching the submitted non-empty reason.
  - The approval record has `executed is true`.
  - The original `action_evaluation` record remains unchanged and still has `executed is false` in full/soft escalation mode.
  - The audit hash chain verifies as intact after the append.
  - A subsequent `GET /approvals` no longer lists the item as pending and shows an actioned/success state indicating the approval decision was recorded.
- **Notes:** This is the primary acceptance test. It must use the real `AuditStore.write_record` append path and real chain verification, not a mocked audit store.

### test_reject_with_reason_appends_linked_rejection_decision_without_execution
- **Traces to:** `MASTER_SPEC.md` §5.5; §8A item 4; append-only approval/rejection rule.
- **Input:** Run Scenario 2 to create a pending escalation. Submit the approval form with `decision=reject` and a non-empty reason such as `Insufficient supporting evidence for payment`.
- **Expected outcome:**
  - Exactly one new `approval_decision` record is appended for the same `correlation_id` as the original action evaluation.
  - The rejection record has `references_hash == original.record_hash`.
  - The rejection record has `approval_reason` exactly matching the submitted reason.
  - The rejection record has `executed is false`.
  - The original `action_evaluation` record remains unchanged.
  - The pending item is removed from the pending list or shown only in an actioned/rejected state, not as still awaiting approval.
  - The audit hash chain verifies as intact after the append.
- **Notes:** This verifies that rejection is also an append-only human decision and that rejected escalations do not execute.

### test_reject_requires_non_empty_reason_and_preserves_pending_item
- **Traces to:** `MASTER_SPEC.md` §8A item 4; `TASK_LEDGER.md` T16 reviewer focus.
- **Input:** Run Scenario 2 to create a pending escalation, then submit the rejection form with a blank or whitespace-only `reason`.
- **Expected outcome:**
  - The response communicates that a reason is required.
  - No `approval_decision` record is appended.
  - The original action evaluation record is unchanged.
  - The escalation remains visible as pending in `GET /approvals`.
- **Notes:** This is the rejection-specific mandatory reason coverage.

### test_approval_view_does_not_invoke_or_reclassify_semantic_evidence_for_payment
- **Traces to:** `MASTER_SPEC.md` §3 semantic layer runs only where needed; §5.3 Evidence; non-negotiable product rule that payment scenarios must not invoke semantic layer.
- **Input:** Run Scenario 2, open `/approvals`, then approve or reject with a valid reason.
- **Expected outcome:**
  - The original action evaluation evidence for Scenario 2 has `evaluated is false`.
  - The approval view may display evidence/context, but it does not add decision/approval/enforcement fields into the Evidence object.
  - The appended `approval_decision` record preserves the Evidence schema shape without adding allow/block/decision/approval fields to evidence.
  - No semantic-evidence result is newly generated for the payment action while rendering or actioning the approval page.
- **Notes:** This test should inspect stored records before and after the approval action. It protects the spec boundary that evidence is only evidence and payment paths skip semantic analysis.

## Coverage checklist
- [x] Happy path covered: Scenario 2 pending escalation renders and approval with reason appends a linked record.
- [x] Error/edge cases covered: blank reasons for Approve and Reject do not append records and keep the item pending.
- [x] Spec non-negotiables verified: append-only audit records, original record unchanged, correlation/reference linkage, evidence schema remains decision-free, payment semantic layer not invoked.
- [x] Real dependencies flagged (no mocks where forbidden): tests should use the real in-process pipeline/approval queue and real audit append/hash-chain verification path; no mocked approval queue or mocked audit writes for acceptance assertions.

## Gaps or ambiguities
- `TASK_LEDGER.md` and the Architect Brief do not mandate the exact approval form route names, HTTP status codes for validation errors, or whether the approver is user-entered versus a stable demo default. Tests should assert behaviour through the implemented UI contract while requiring that `human_approver` is populated and blank reasons cannot append records.
- The acceptance criteria say approving "updates `executed`" while §5.5 forbids mutating the original record. The test expectation resolves this per `MASTER_SPEC.md`: the appended `approval_decision` carries the resulting `executed` state; the original `action_evaluation` remains unchanged.