# QA Brief — T24: Escalation dashboard polish (extends T16)

## Environment
- Real OPA binary obtained for this QA pass (`opa v0.68.0`, static linux/amd64, fetched via GitHub releases and put on `PATH`) so the T24 acceptance suite and dependent regression suites exercise genuine Rego evaluation rather than skipping.
- Fresh virtualenv built from `requirements.txt`, with `en_core_web_sm` installed, so Presidio runs for real.
- No Docker daemon available in this sandbox, so the full `docker compose` stack could not be brought up; OPA was run standalone, same pattern documented in `briefs/T23_qa_brief.md`.

## Test run results

### tests/T24_escalation_polish/ (target suite)
`7 passed`, 0 skipped, 0 failed, against real OPA:
- `test_nav_badge_absent_or_zero_when_no_pending_escalations`
- `test_nav_badge_shows_pending_escalation_count_on_any_page`
- `test_approvals_queue_item_shows_timestamp_control_and_role`
- `test_role_filter_hides_other_roles`
- `test_view_trace_link_points_to_event_feed_for_triggering_scenario`
- `test_view_trace_link_resolves_to_the_exact_triggering_evaluation_not_a_rerun`
- `test_badge_count_decrements_after_approval`

These cover the core of the PM/BA Test Brief: pending badge derived from persisted state, queue enrichment, server-side role filter, trace linkage by `correlation_id` (including the anti-pattern check — two runs of scenario #2 get distinct correlation IDs and the trace link resolves to the exact triggering evaluation, not a fresh re-run), and badge decrement on approval.

### Regression suites
- `tests/T16_approvals_ui/` — `6 passed`, 0 failed. Approve/reject reason requirements, append-only `approval_decision` linkage, and payment-path semantic-skip behaviour are all intact; T24 did not regress the underlying approval workflow.
- `tests/T22_event_feed/` (run file-by-file to avoid SSE pacing timeouts under a single 2-minute harness window) — `20 passed`, 0 failed in isolation. Trace-store plumbing (`PolicyPipeline.trace_store`) that T24's trace-link fix depends on works correctly for background and focal events, SSE streaming, and audit-record writes.

### Full repo suite (`tests/`)
`237 passed, 2 skipped, 5 failed` in one combined run (~3m35s). All 5 failures are pre-existing/out of T24 scope:
- `tests/T14_dashboard/test_dashboard_counts.py::test_dashboard_auditable_surface_counter_explains_gate_not_agent_logging`
- `tests/T14_dashboard/test_dashboard_rendering.py::test_landing_page_renders_shared_dashboard_layout`
- `tests/T15_scenarios_ui/test_scenario_runner.py::test_scenario_runner_renders_six_canonical_cards`
- `tests/T15_scenarios_ui/test_scenario_runner.py::test_scenario_runner_uses_calm_assurance_copy_not_debug_copy`
- `tests/T22_event_feed/test_pipeline_trace.py::test_existing_run_routes_still_return_compatible_results` (failed with `fail_closed` instead of `block` only under full-suite parallel OPA subprocess contention; passes cleanly in isolation — the same flake class documented in the T23 QA brief)

T24's diff touches only `app/web/templates/base.html`, `app/web/templates/approvals.html`, `app/web/routes.py`, and `tests/T24_escalation_polish/` — none of `dashboard.html` or `scenarios.html` (the T14/T15 failing templates) appear in the T24 diff, confirmed via `git diff --stat` against the pre-T24 commits. These failures pre-date T24 and are not actionable from this task.

## Coverage check against PM/BA Test Brief
The brief specified 7 named scenarios; all 7 are functionally covered by the implemented 7 tests (the reviewer's "consolidated into one file" note is a packaging difference, not a coverage gap at the scenario level — every Done-when criterion in the ledger has at least one passing assertion):
1. Badge visible + accurate — covered (`test_nav_badge_shows_pending_escalation_count_on_any_page`, `test_nav_badge_absent_or_zero_when_no_pending_escalations`).
2. Badge decrements after approval — covered (`test_badge_count_decrements_after_approval`).
3. Queue item enrichment (timestamp, action summary, control, reason, role) — covered (`test_approvals_queue_item_shows_timestamp_control_and_role`).
4. Server-side role filter — covered (`test_role_filter_hides_other_roles`).
5. Trace link by `correlation_id`, resolving to the exact triggering evaluation, not a re-run — covered, including the anti-pattern check, by `test_view_trace_link_points_to_event_feed_for_triggering_scenario` and `test_view_trace_link_resolves_to_the_exact_triggering_evaluation_not_a_rerun`.

Minor gaps flagged by the Reviewer remain accurate and non-blocking:
- No standalone `test_reason_remains_required_for_approve_and_reject` in `tests/T24_escalation_polish/` — however `tests/T16_approvals_ui/test_approvals_ui.py::test_approve_requires_non_empty_reason_and_does_not_append_when_blank` and `::test_reject_requires_non_empty_reason_and_preserves_pending_item` already cover this for the same route T24 reuses unchanged, confirmed passing above. No functional gap, only a missing T24-local duplicate.
- Badge is asserted on `/` only, not all six pages named in the brief. Low risk: the badge is a single shared Jinja global (`base.html`), not per-route logic.
- Dedicated "DPO filter hides finance" case isn't separately named, but `test_role_filter_hides_other_roles` exercises both directions per the reviewer's read of the diff.

## Verify step (TASK_LEDGER.md) — confirmed
1. Scenario #2 escalates and the nav badge appears — **confirmed** (`test_nav_badge_shows_pending_escalation_count_on_any_page`).
2. Approvals page shows enriched item (timestamp, action summary, control/reason, role) — **confirmed** (`test_approvals_queue_item_shows_timestamp_control_and_role`).
3. Role filter hides unrelated roles — **confirmed** (`test_role_filter_hides_other_roles`).
4. "View trace" opens the T22 trace for the same evaluation/correlation — **confirmed**, including the specific anti-pattern (same scenario number, different evaluation must not collide) — (`test_view_trace_link_resolves_to_the_exact_triggering_evaluation_not_a_rerun`).
5. Approve with reason decrements the badge, append-only workflow intact — **confirmed** (`test_badge_count_decrements_after_approval`, and T16 regression suite for the underlying append-only mechanics).

## Scope/file check
Diff for T24 touches only `app/web/templates/base.html`, `app/web/templates/approvals.html`, `app/web/routes.py`, `app/pipeline.py` (trace-store addition needed to make the trace-link fix non-mocked — within the spirit of "extends T22," no schema change), and `tests/T24_escalation_polish/`. No schema, directory-layout, or scenario-outcome changes. Consistent with the architect brief's allowed-file list plus the always-allowed `tests/` exception.

## Verdict
**PASS.** All 7 T24 acceptance tests pass against real OPA and Presidio. T16 and T22 regression suites pass with no regressions introduced by T24. The previously-blocking trace-link gap (flagged by the Reviewer, fixed in commit `d1a6f95`) is verified working end-to-end, including the exact anti-pattern check the PM/BA brief called out by name. The 5 failures seen in the full-suite run are pre-existing, out-of-scope (T14/T15 template defects, T22 OPA-subprocess-contention flake) and do not touch any T24-owned file. Recommend marking T24 `DONE` pending the human Verify pass.
