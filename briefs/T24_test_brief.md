# Test Brief — T24: Escalation dashboard polish (extends T16)

## Spec references
- MASTER_SPEC.md: §5.5 Evidence Record / append-only approvals; §6 decision precedence and required approval roles; §7 canonical scenario outcomes, especially Scenario #2; §8A item 4 Approval queue; §11 runtime flow; §12 demo acceptance criteria for human oversight and auditability.
- TASK_LEDGER.md: T24 goal, files, key notes, Done when criteria 1–5, Verify step, and Reviewer focus. T16 acceptance remains in force for mandatory reasons and append-only `approval_decision` records. T22 acceptance remains in force for trace linkage by `correlation_id`.

## Target test location
- Folder: `tests/T24_escalation_polish/`
- Suggested files:
  - `__init__.py` — package marker for the T24 acceptance tests.
  - `test_nav_pending_badge.py` — covers pending-count badge visibility and count changes after an approval decision.
  - `test_approvals_dashboard.py` — covers enriched queue item content and server-side role filtering.
  - `test_trace_link_and_append_only.py` — covers `correlation_id` trace linkage and regression coverage for the existing append-only approval workflow.

## Test cases

### test_nav_badge_counts_pending_escalations_on_all_pages
- **Traces to:** TASK_LEDGER.md T24 Done when #1; T24 Key note “Pending badge”; Architect Brief non-negotiable that the badge count is derived from persisted audit/approval state.
- **Input:** Start from a clean demo data state. Run Scenario #2 through the real pipeline so it creates a pending `escalate` evaluation for `finance_supervisor`. Request at least these rendered pages with the FastAPI test client: `/`, `/scenarios`, `/events`, `/approvals`, `/audit`, and `/settings`.
- **Expected outcome:** Each rendered page includes the global Approvals nav link with a visible pending badge/count of `1`. The assertion should verify both the count and that it is associated with the Approvals navigation, not merely present elsewhere in the page.
- **Notes:** Do not use an in-memory counter or a mocked count provider in the test setup. The pending count must be produced from the same persisted audit/approval state the UI uses.

### test_nav_badge_decrements_after_approval_decision
- **Traces to:** TASK_LEDGER.md T24 Done when #5 and Verify step; MASTER_SPEC.md §5.5 append-only approvals.
- **Input:** From a clean state, run Scenario #2 to create one pending escalation. Load `/approvals`, identify the pending approval item, then submit `POST /approvals/{item_id}/decide` with `decision=approve`, a non-empty `reason`, and an explicit `human_approver`. Follow or re-request a normal page after the redirect.
- **Expected outcome:** The Approvals nav badge count changes from `1` to `0` after page navigation. The original `action_evaluation` row remains present, and a separate `approval_decision` row is appended with `references_hash` equal to the original record hash.
- **Notes:** This is functional regression coverage for T16 while validating the T24 badge behaviour. The test should inspect persisted records, not only HTML.

### test_approvals_queue_item_shows_operational_context
- **Traces to:** TASK_LEDGER.md T24 Done when #2; T24 Key note “Queue item enrichment”; MASTER_SPEC.md §8A item 4.
- **Input:** Run Scenario #2 through the real pipeline. Request `GET /approvals`.
- **Expected outcome:** The pending queue item for Scenario #2 shows all required dashboard context:
  - escalation timestamp or created-at time in a human-readable form;
  - action summary including the payment amount `£850` and target/customer `CUST-100`;
  - triggering control ID `FIN-PAY-002`;
  - decision reason explaining the missing approval/high-value payment;
  - required approval role `finance_supervisor`;
  - an affordance labelled `View trace`.
- **Notes:** The test should assert rendered HTML text/hrefs because this task is UI polish. It should not require any schema changes.

### test_role_filter_finance_supervisor_hides_unrelated_roles
- **Traces to:** TASK_LEDGER.md T24 Done when #3; T24 Key note “Role filter”; Architect Brief role-filter requirement.
- **Input:** From a clean state, create at least two pending escalations through real scenario/pipeline execution: Scenario #2 for `finance_supervisor` and an email escalation that uses the implemented data-protection role (`data_protection_officer` per T24 ledger, or the actual role emitted by the existing control if it differs). Request `GET /approvals` with no role filter, then request the server-side finance filter, e.g. `GET /approvals?role=finance_supervisor` or the exact query parameter implemented for T24.
- **Expected outcome:** The unfiltered page shows both pending escalations and exposes role-filter options for `All`, `finance_supervisor`, and the data-protection role. The finance-filtered page shows the Scenario #2/`finance_supervisor` item and hides the unrelated data-protection item.
- **Notes:** This must be a server-side filtering test. Do not rely on client-side JavaScript or CSS-hidden rows. If the existing control role differs from `data_protection_officer`, assert the implemented role consistently while preserving the ledger’s requirement that the finance filter hides DPO/data-protection escalations.

### test_data_protection_role_filter_shows_only_data_protection_items
- **Traces to:** TASK_LEDGER.md T24 Key note “Role filter”; MASTER_SPEC.md §6 `COMM-EMAIL-001`; §8A item 4.
- **Input:** Create one pending finance escalation and one pending data-protection email escalation through the real pipeline. Request the data-protection role filter page.
- **Expected outcome:** The data-protection filtered page shows only the email/data-protection escalation and hides the `finance_supervisor` item. The selected filter state is visible in the rendered page so a user can tell which queue they are viewing.
- **Notes:** This complements the finance-filter test and guards against filters that only special-case `finance_supervisor`.

### test_view_trace_link_uses_same_correlation_id
- **Traces to:** TASK_LEDGER.md T24 Done when #4; T24 Key note “Queue item enrichment”; Architect Brief non-negotiable trace linkage by `correlation_id`; T22 trace view contract.
- **Input:** Run Scenario #2 through the real pipeline. Request `/approvals`, extract the pending row’s `View trace` link, and compare it with the original escalation record’s `correlation_id`.
- **Expected outcome:** The `View trace` href targets the existing T22 trace/live-feed trace route and includes or otherwise resolves by the same `correlation_id` as the original `action_evaluation` record. Following the link returns HTTP 200 and renders the pipeline trace for that evaluation/correlation rather than a generic scenario page.
- **Notes:** The test should fail if the link is built from the approval item ID, record hash, or scenario number alone. The business requirement is traceability from human decision to the exact pipeline evaluation that caused the escalation.

### test_reason_remains_required_for_approve_and_reject
- **Traces to:** TASK_LEDGER.md T24 Done when #5; T16 Done when; MASTER_SPEC.md §5.5 append-only approvals and §8A item 4 human oversight.
- **Input:** Run Scenario #2 to create a pending escalation. Submit approval and rejection decisions with an empty or whitespace-only `reason`.
- **Expected outcome:** Each submission redirects or renders an error stating that a reason is required. No `approval_decision` row is appended, the original escalation remains pending, and the pending nav badge count remains unchanged.
- **Notes:** This is explicit regression coverage: T24 must polish the dashboard without weakening the existing human-approval control.

### test_approval_appends_linked_record_without_mutating_original
- **Traces to:** MASTER_SPEC.md §5.5 append-only approvals; TASK_LEDGER.md T24 Done when #5; Architect Brief non-negotiable approval semantics.
- **Input:** Run Scenario #2, capture the original `action_evaluation` record fields (`record_hash`, `executed`, `decision`, `created_at`, and `correlation_id`), then approve with a valid reason.
- **Expected outcome:** A new `approval_decision` record is appended with the same `correlation_id`, `references_hash` equal to the original `record_hash`, populated `human_approver` and `approval_reason`, and `executed=true`. The original record is still an `action_evaluation`, still has the same hash and decision, and is not updated in place.
- **Notes:** This test should use the real audit store/hash-chain implementation already present in the app. Do not mock audit writes.

## Coverage checklist
- [ ] Happy path covered: Scenario #2 creates a visible finance escalation, the enriched queue renders, trace link opens, and a valid approval decrements the badge.
- [ ] Error/edge cases covered: empty approval/rejection reasons are rejected; role filters hide unrelated roles; badge count reaches zero after actioning.
- [ ] Spec non-negotiables verified: model/policy decision semantics unchanged; approval decisions are append-only; original audit records are not mutated; traceability uses `correlation_id`; pending counts come from persisted state.
- [ ] Real dependencies flagged (no mocks where forbidden): scenario execution should use the real pipeline, real OPA policy decisions, real audit store/hash-chain code, and the existing approval queue/store. Tests may use the project’s normal isolated test database/store fixture, but must not mock policy decisions, audit writes, or approval state.

## Gaps or ambiguities
- The T24 ledger names the data-protection role filter as `data_protection_officer`, while MASTER_SPEC.md §6 lists `COMM-EMAIL-001` as escalating to `data_protection_approver`. The implementer should not change policy semantics for T24; tests should assert the actual role emitted by the implemented control while still proving that the finance filter hides data-protection escalations.
- The exact T22 route shape for opening a trace by `correlation_id` is implementation-dependent. The acceptance requirement is not ambiguous: the Approvals `View trace` link must resolve to the exact pipeline evaluation/correlation that caused the escalation, not merely to a scenario runner or generic live-feed page.
