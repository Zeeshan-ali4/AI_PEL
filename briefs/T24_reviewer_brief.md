# Reviewer Brief — T24: Escalation dashboard polish (extends T16)

## Scope checked
- `app/web/routes.py`, `app/web/templates/approvals.html`, `app/web/templates/base.html`
- `tests/T24_escalation_polish/` (`conftest.py`, `test_escalation_polish.py`)
- Against `briefs/T24_architect_brief.md`, `briefs/T24_test_brief.md`, `MASTER_SPEC.md` §5.5/§8A item 4, `TASK_LEDGER.md` T24.

## File-list compliance
Only the allowed files were touched (plus the test folder, which is always allowed). No schema or other-task files were modified. Good.

## What works
1. **Pending badge** (`_pending_escalation_count`, `base.html`): correctly derived from persisted state — counts `action_evaluation` records with `decision == ESCALATE` whose `record_hash` has no matching `approval_decision.references_hash`. No in-memory counter. Rendered via a Jinja global so it appears on every page without per-route plumbing. Matches the non-negotiable.
2. **Queue enrichment** (`approvals.html`): each pending item now shows `created_at` (escalation timestamp), control ID, reason, required role, and the existing action summary. Satisfies Done-when #2.
3. **Role filter**: server-side (`role` query param, validated against `APPROVAL_ROLE_FILTER_OPTIONS`), filters `pipeline.approval_queue.list_pending()` before rendering. No client-side hiding. Satisfies Done-when #3.
4. **Approval semantics unchanged**: `_build_pending_rows`/`_build_actioned_rows` and the `/approvals/{id}/decide` flow are untouched apart from threading the role filter through; append-only behavior (new `approval_decision` record, original record untouched) is preserved per the diff.
5. Test suite collects cleanly (verified with a local venv; spaCy model installed). All 6 tests are written against the real pipeline/OPA fixture pattern (no mocked audit/approval state) — correctly skip when no `opa` binary is present in this sandboox, which is expected, not a defect.

## Gap — trace linkage does not meet the non-negotiable
The architect brief states: *"The trace link must be based on `correlation_id` and should route to the existing T22 trace view/route... Do not invent a separate tracing architecture."* The PM/BA test brief is more explicit: *"The test should fail if the link is built from the approval item ID, record hash, or scenario number alone. The business requirement is traceability from human decision to the exact pipeline evaluation that caused the escalation."*

The implementation (`_trace_link_for_control` in `app/web/routes.py:528-543`) builds the link **purely from a control→scenario-number lookup** (`_CONTROL_TO_SCENARIO_NUMBER`), then appends `correlation_id` as an inert query string. The target route, `GET /events/{scenario_id}` (`app/web/routes.py:282-298`), never reads a `correlation_id` query parameter — it only pre-arms the live-feed UI to **re-run scenario N from scratch**, producing a brand-new evaluation/correlation each time. So "View trace" does not open the trace for *that* escalation; it opens a generic scenario runner that happens to match by scenario number. This is exactly the failure mode the test brief calls out by name.

The implementer's own test, `test_view_trace_link_points_to_event_feed_for_triggering_scenario`, only asserts `href="/events/2"` — it does not check that the `correlation_id` query parameter is present, let alone that the page actually resolves to the original evaluation. It passes despite the underlying gap, which means it isn't testing the actual non-negotiable.

**Recommendation:** either (a) extend the T22 `/events/{scenario_id}` route (or add a small `/events/{scenario_id}?correlation_id=...` handling branch) to look up the stored trace for that correlation_id and render it instead of re-running the scenario, or (b) if rendering the literal stored trace is out of scope for T24, say so explicitly in the brief/ledger as a known limitation rather than letting the code comment quietly declare it "out of T24 scope" while the architect brief's non-negotiable goes unmet. As written, this should not be signed off as fully meeting Done-when #4 / the Verify step ("confirm it opens the T22 pipeline trace for the same evaluation/correlation").

## Other coverage gaps vs. the PM/BA Test Brief
The brief specified seven test cases across three files; the implementer consolidated into one file with six tests, dropping or weakening:
- **`test_reason_remains_required_for_approve_and_reject`** — not implemented at all. This is explicit regression coverage that empty/whitespace reasons are rejected; it's missing from `test_escalation_polish.py`. (T16 may cover this already — confirm before treating as a hard blocker — but T24's own brief asked for it here too.)
- **Nav badge across all six pages** — the test brief asks for assertions on `/`, `/scenarios`, `/events`, `/approvals`, `/audit`, `/settings`; the implemented test only checks `/`. Lower risk since the badge is a single Jinja global shared by `base.html`, but unverified by test.
- **Two-way role filter** — only finance-hides-DPO is tested; the reverse (DPO filter hides finance) from `test_data_protection_role_filter_shows_only_data_protection_items` is not separately covered (partially implied by the existing test's `all_roles` check, but not as a dedicated DPO-filter assertion).

These are lower severity than the trace-link gap but worth tightening, especially the missing reason-required test given how central "append-only, reason mandatory" is to the product's non-negotiables.

## Verdict
**Not ready to mark DONE as specified.** The badge, enrichment, and role-filter work meet the brief. The trace-link requirement — called out as a non-negotiable in the architect brief and tested explicitly in the PM/BA test brief — is not actually satisfied: the link resolves by scenario number, not by the originating evaluation/correlation, and would show a fresh re-run rather than the trace that caused the escalation. Recommend sending back to the Implementer to either wire `/events/{scenario_id}` to honor `correlation_id` and render the matching stored trace, or to get an explicit spec amendment if a generic scenario link is judged sufficient for the demo. Also recommend adding the missing reason-required regression test before sign-off.
