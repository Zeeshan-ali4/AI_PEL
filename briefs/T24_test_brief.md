# Test Brief — T24: Escalation dashboard polish (extends T16)

## Spec references
- `MASTER_SPEC.md` §8A item 4 (extended): pending escalations visible with role, summary, evidence; approve/reject unchanged.
- `MASTER_SPEC.md` §5.5: append-only approvals; pending count must derive from persisted audit/approval state, not an in-memory counter.
- `TASK_LEDGER.md` T24 Done when / Verify.

## Target test location
- Folder: `tests/T24_escalation_polish/`
- File: `test_escalation_polish.py`

## Test cases

### test_nav_badge_shows_pending_escalation_count_on_any_page
- Run Scenario 2 (escalates). Request `GET /` (dashboard, an unrelated page).
- Expect HTTP 200 and the rendered HTML to contain a visible pending-count indicator of `1` near the Approvals nav link.

### test_nav_badge_absent_or_zero_when_no_pending_escalations
- With no scenarios run (fresh store), request `GET /`.
- Expect no pending badge value greater than 0 rendered in the nav.

### test_approvals_queue_item_shows_timestamp_control_and_role
- Run Scenario 2. `GET /approvals`.
- Expect the pending item to show: a timestamp, the action summary (£850 / CUST-100), control id `FIN-PAY-002`, and required role `finance_supervisor`.

### test_role_filter_hides_other_roles
- Run Scenario 2 (finance_supervisor) and Scenario 4 (data_protection_approver).
- `GET /approvals?role=finance_supervisor` shows the Scenario 2 item and hides the Scenario 4 item.
- `GET /approvals?role=All` (or no param) shows both.

### test_view_trace_link_points_to_event_feed_for_triggering_scenario
- Run Scenario 2. `GET /approvals`.
- Expect a trace link present pointing to `/events/2` (the existing T22 live-feed route for the scenario that produced the escalation).

### test_badge_count_decrements_after_approval
- Run Scenario 2. Confirm badge count is `1` on `GET /`.
- Approve with a non-empty reason via `POST /approvals/{item_id}/decide`.
- Confirm badge count is `0` on a subsequent `GET /`, and the existing append-only approval workflow still appends a linked `approval_decision` record without mutating the original.

## Coverage checklist
- [x] Badge presence/accuracy across pages.
- [x] Queue item enrichment (timestamp, control, role, summary).
- [x] Role filter behaviour.
- [x] Trace link correctness.
- [x] No regression to append-only approve/reject workflow.
