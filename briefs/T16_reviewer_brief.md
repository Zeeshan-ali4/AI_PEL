# Reviewer Brief — T16: Approval queue view

## Scope reviewed
- `app/web/templates/approvals.html`
- `app/web/routes.py` (approvals-related routes: `approvals_page`, `decide_approval`, and supporting helpers `_find_action_evaluation_record`, `_action_summary`, `_build_pending_rows`, `_build_actioned_rows`)
- `tests/T16_approvals_ui/test_approvals_ui.py`, `tests/T16_approvals_ui/conftest.py`

## Spec/brief conformance
- Append-only: `decide_approval` only ever calls `pipeline.audit_store.write_record(...)` with `record_type=RecordType.APPROVAL_DECISION`. No update/mutate path exists for the original `action_evaluation` row. Confirmed in code and by test (`refreshed_original.record_hash == original.record_hash` after approve/reject).
- Linkage: appended record carries `correlation_id=original.correlation_id` and `references_hash=original.record_hash`, matching §5.5.
- Mandatory reason: both Approve and Reject forms `required` the `reason` textarea client-side, and `decide_approval` independently strips and rejects blank/whitespace-only reasons server-side (redirect with `error=...`, no audit write). Verified server-side enforcement is real, not just HTML `required`.
- `executed` semantics: `executed=True` for approve, `False` for reject, set on the **appended** record only; original stays `executed=False`. Matches the brief's resolution of the §5.5 vs. acceptance-criteria tension.
- Human approver: falls back to `DEFAULT_HUMAN_APPROVER` demo identity when the form field is blank; otherwise uses submitted value. Matches brief.
- Payment/semantic boundary: approvals view never touches `app/semantic/*`; it only reads the original Evidence off the stored record and copies it onto the appended approval record. `evidence.evaluated` stays `False` for the payment path; no allow/block/decision field exists on `Evidence` (schema untouched).
- File-scope discipline: changes are confined to the three allowed files plus the T16 test subfolder. No schema, OPA/Rego, or settings-store changes.
- UI tone: copy in `approvals.html` correctly frames the human as the decision-maker and the append as a new linked record, consistent with §1A/§8A.

## Defect found and fixed
`tests/T16_approvals_ui/test_approvals_ui.py::test_approval_view_does_not_invoke_or_reclassify_semantic_evidence_for_payment` called `_action_evaluation_records(records)` where `records` was an undefined name at that point (a leftover from an earlier draft) — it should have been `wired_pipeline.audit_store`, and a later line referenced `records` again without it being defined either. This caused an `AttributeError: 'list' object has no attribute 'read_records'` (the helper expects a store with `.read_records()`, not a list). This is a test-code bug, not an implementation bug — the route/audit/queue logic under test was correct.

Fixed by replacing both bad call sites with `wired_pipeline.audit_store`, re-deriving `records` from the store where the test still needs the raw list (for the `approval_decision` lookup). No production code (`routes.py`, `approvals.html`) needed any change.

## Verification performed
- Could not run the OPA binary or Docker in this environment (no network access to fetch the `opa` binary, no Docker daemon available), so the project's standard `pytest tests/T16_approvals_ui` (which needs a live OPA per the existing T15-style fixture pattern) could not be exercised against the *real* Rego policies here.
- To still exercise the real route → pipeline → real append-only `AuditStore`/`ApprovalQueue` code paths (the actual subject of T16), I stood up a minimal local HTTP stand-in for OPA's `/v1/data/policy/gate/decision` endpoint that returns the same Decision shape OPA would for a >£500 payment (`escalate` / `FIN-PAY-002` / `finance_supervisor`), pointed `OPA_URL` at it, and ran the full T16 suite.
- Result after the test fix: **6 passed, 0 failed** (`tests/T16_approvals_ui`).
- This validates: pending queue rendering with the correct role/control/amount/customer; blank-reason rejection for both approve and reject (no audit write, item stays pending, original record byte-for-byte unchanged including `record_hash`/`created_at`); valid approve/reject appends exactly one linked `approval_decision` record with correct `references_hash`, `human_approver`, `approval_reason`, `executed`; `verify_chain()` stays intact after the append; the original record's Evidence is never mutated and the appended record's Evidence carries no allow/block/decision/approval attributes.
- I did **not** run the project's full `tests/` suite against real OPA (not available here); a handful of unrelated T13/T14/T15 tests fail against my OPA stand-in only because that stand-in implements just the scenario-2-shaped payment logic, not the full six-scenario policy table — this is an artefact of my verification substitute, not a regression in this codebase. Whoever runs this with a real `opa` binary or via `docker compose run --rm app pytest` should re-run the full suite as the actual gate.

## Reviewer focus items from the ledger — verdict
- "Original record is not mutated": **Confirmed** (hash/executed/created_at unchanged across approve, reject, and blank-reason attempts).
- "Reason is mandatory": **Confirmed**, enforced server-side independent of the HTML `required` attribute.
- "Correlation/reference linkage correct": **Confirmed** (`correlation_id` matches original; `references_hash` equals original's `record_hash`).

## Recommendation
**Pass — mark T16 `DONE`** once a human/QA run with a real OPA instance (`docker compose run --rm app pytest tests/T16_approvals_ui`) reproduces the same green result, per the ledger's verify step. The implementation matches the architect and test briefs; the only issue found was in the test file and has been corrected in place.
