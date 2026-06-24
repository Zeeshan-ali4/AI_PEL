# Reviewer Brief — T18: Audit log + verify chain + simulate tampering (headline moment)

## Scope checked
- `app/web/routes.py` (new `/audit`, `/audit/verify`, `/audit/simulate-tampering` routes only)
- `app/web/templates/audit.html` (new)
- `app/web/templates/base.html` (nav link only)
- `tests/T18_audit_ui/` (`conftest.py`, `test_audit_log_page.py`, `test_audit_integrity_actions.py`)

No files outside the T18 allowed list were touched.

## Findings

### Non-negotiables — pass
- `verify_audit_chain()` and `simulate_audit_tampering()` call the real `AuditStore.verify_chain()` / `AuditStore.simulate_tampering()` from T12 — no web-layer reimplementation of hashing or verification (`app/web/routes.py:577`, `app/web/routes.py:594`).
- The only mutation path is the named `simulate_tampering` helper; `AuditStore` exposes no other update/delete method, and the audit page exposes no generic edit/delete controls — only the labelled demo form.
- Integrity result is unambiguous: green "Chain intact" panel with `verified_count`, or red "Chain broken — tampering detected" panel naming `broken_record_id` and `broken_reason` (`audit.html:18-42`). The count/record id are templated from the real `ChainVerificationResult`, not hard-coded copy.
- Chronological table exposes id, created time, record type, correlation id, decision, executed, full `record_hash`/`prev_hash` (shortened visually, full value in `title` attribute — satisfies the test brief's "preserve full value" requirement) and a link to the existing T17 `/records/{hash}` view (`audit.html:104-137`).
- Tamper action is visibly labelled demo-only with explanatory copy distinguishing it from normal operation (`audit.html:60-66`).
- No new reset subsystem was invented; the empty/post-tamper state directs the user back to the existing `/scenarios` demo workflow, satisfying the brief's fallback guidance.

### Code quality
- `_build_audit_rows` cleanly separates presentation shaping from the route handler.
- Redirect-based verify/tamper flow (303 + query params) keeps state out of session/global mutable storage and is simple to test.
- `base.html` nav change is a one-line, additive diff — no risk to existing T14–T17 pages.

### Tests
- Test files target the right folder (`tests/T18_audit_ui/`) and use the same real-OPA `wired_pipeline` fixture pattern already established in T15–T17, rather than mocking the audit store or verifier — matches the test brief's "no mocks" requirement.
- Coverage maps 1:1 onto every test brief scenario: chronological listing + fields, record-detail link, empty-state copy, green intact, red broken naming the exact record, demo-only labelling, no edit/delete controls, reset/reseed guidance.
- Ran locally: `python -m pytest -q tests/T18_audit_ui/` → all 8 collected, all skip with "OPA binary not available" (no `opa` binary or `OPA_URL` in this environment). Confirmed this is an environment limitation, not a regression — `tests/T15_scenarios_ui`, `tests/T16_approvals_ui`, `tests/T17_record_view` skip identically here for the same reason. `python -m py_compile app/web/routes.py` and Jinja2 template parsing of `audit.html`/`base.html` both succeed.

## Outstanding before QA/Done
- These tests have not actually executed against a live OPA process in this review session (sandbox has no `opa` binary, no network access to fetch one). QA must run `tests/T18_audit_ui/` with a real `opa` binary (or `docker compose run --rm app pytest -q tests/T18_audit_ui/`) to get a true pass/fail signal, per the Architect Brief's verify step.
- Manual UI walkthrough (run scenarios → `/audit` → Verify Chain → Simulate Tampering → Verify Chain again) should also be done in an environment with the full stack (`docker compose up`) to visually confirm the green/red panels render as intended.

## Verdict
Implementation matches the architect and test briefs; no spec/schema/policy drift found. **Recommend approval pending QA's live-OPA test run** (could not be executed in this review sandbox due to missing OPA binary/network access).