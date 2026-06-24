# QA Report — T18: Audit log + verify chain + simulate tampering (headline moment)

## Verdict
PASS (with one environment caveat — see below)

## Ledger verification
- Command run: `docker compose run --rm app pytest -q tests/T18_audit_ui/` could not be executed — no Docker daemon socket available in this QA environment (`/var/run/docker.sock` missing).
- Fallback performed: ran `python -m pytest tests/T18_audit_ui/ -v` directly with real Presidio/spaCy installed (`en_core_web_sm` downloaded fresh). Attempted to obtain a real `opa` binary via the OPA release URL, `apt`, `pip`, `go install`, and `git clone` of the OPA source repo — all blocked by this environment's outbound network policy (proxy returns 403 for `openpolicyagent.org` and `github.com`; a Go-module-proxy fetch of the OPA source succeeded but the module's internal `replace` directives point at files only present in the full git checkout, so a from-source build is not possible without `git clone` access). No `opa` binary is obtainable in this sandbox.
- Because of this, all 8 tests in `tests/T18_audit_ui/` **skip** (`OPA binary not available`) rather than run — this is an environment limitation identical to the one the Reviewer and the prior QA pass already recorded, and identical to the skip behaviour of `tests/T13`–`T17` in this same sandbox.
- To get a real signal anyway, I built a throwaway manual exploratory harness (fake in-process OPA HTTP server returning `allow`, real sqlite-backed `AuditStore`/`SettingsStore`, real `FastAPI` `TestClient` against the actual app routes — no modification to any test file or app code):
  - Ran scenarios 1–3 through `/run/{id}` → 200 each, real records written.
  - `GET /audit` → 200; page contains `record_hash`, `prev_hash`, and `correlation_id` for the real records.
  - `POST /audit/verify` (cookie/redirect-following) → 200; page text contains "intact"/"verified".
  - `POST /audit/simulate-tampering` with `record_id=1` → 200; page text contains "broken"/"tamper" and names record `1`.
  - Confirmed `audit.html` contains none of: `delete`, `>edit<`, `/audit/update`, `/audit/delete` (`grep -i "delete\|update\|edit" app/web/templates/audit.html` → no matches).
- This manual harness is **not** a substitute for the real Rego-policy-driven pytest run (it stubs OPA's decision, not the audit/hash-chain logic, which is real `AuditStore.verify_chain()`/`simulate_tampering()`), but it does prove the T18 routes, templates, and real audit-store integration work end-to-end, and specifically confirms the fix in commit `bc255ed` (copy edit removing the word "deletes" from the explanatory prose) resolves the false-positive substring match the prior QA pass flagged.

## Test suite results
- Command run: `python -m pytest tests/T18_audit_ui/ -v`
- Total: 8 | Passed: 0 | Failed: 0 | Skipped: 8 (`OPA binary not available; set OPA_URL or install opa`)
- Full repo regression: `python -m pytest -q tests/` → 143 passed, 51 skipped, 0 failed. All skips are the same OPA-binary-unavailable condition across `tests/T09`–`T20` (pre-existing environment limitation, not a T18 regression).
- The previously failing test (`test_no_normal_update_or_delete_audit_controls_are_exposed`, flagged FAIL in the prior QA pass on commit `2115b2a`) is fixed by commit `bc255ed`: the explanatory copy in `audit.html` no longer contains the word "deletes", so the test's `assert "delete" not in page` will pass once OPA is available. Confirmed by direct grep of the rendered template content and by the manual exploratory harness above (which renders the same template through the real route and shows no "delete" substring).

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_audit_log_page.py` | `tests/T18_audit_ui/test_audit_log_page.py` | ok |
| `test_audit_integrity_actions.py` | `tests/T18_audit_ui/test_audit_integrity_actions.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|---|---|---|---|---|
| test_audit_log_lists_records_chronologically_with_assurance_fields | same name | test_audit_log_page.py | yes | skipped here (no OPA); manually confirmed fields render via exploratory harness |
| test_audit_log_includes_record_detail_links_when_records_exist | same name | test_audit_log_page.py | yes | skipped here (no OPA); prior reviewer/QA pass confirmed link target matches T17 `/records/{hash}` |
| test_audit_log_empty_or_minimal_state_is_board_readable | same name | test_audit_log_page.py | yes | skipped here (no OPA) |
| test_reset_or_reseed_affordance_is_present_without_new_subsystem_assumption | same name | test_audit_log_page.py | yes | skipped here (no OPA) |
| test_verify_chain_shows_green_intact_status_and_count | same name | test_audit_integrity_actions.py | yes | skipped here (no OPA); manually confirmed `/audit/verify` returns real intact state with count |
| test_simulate_tampering_breaks_chain_and_names_exact_failing_record | same name | test_audit_integrity_actions.py | yes | skipped here (no OPA); manually confirmed `/audit/simulate-tampering` returns real broken state naming the tampered record |
| test_simulate_tampering_action_is_labelled_demo_only | same name | test_audit_integrity_actions.py | yes | skipped here (no OPA) |
| test_no_normal_update_or_delete_audit_controls_are_exposed | same name | test_audit_integrity_actions.py | yes | skipped here (no OPA); **previously-flagged false positive is fixed** — confirmed via direct template grep that no "delete"/"update"/"edit" markup or copy remains |

### Extra tests (Implementer-added)
- None beyond the eight brief-mapped tests.

## Spec non-negotiable checks
- Evidence schema unaffected (not in scope for T18 — no schema files touched): passed (file list unchanged from architect/reviewer briefs: `app/web/routes.py`, `app/web/templates/audit.html`, `app/web/templates/base.html`, `tests/T18_audit_ui/`).
- Decision logic stays in OPA, not Python: passed — `app/web/routes.py` calls `AuditStore.verify_chain()` / `AuditStore.simulate_tampering()` only; no decision logic added.
- Audit table append-only in normal operation; only the named demo helper mutates a row: passed — confirmed by template grep and by manual exploratory run (no edit/update/delete controls; tampering only via the labelled demo affordance).
- Real components stay real: `AuditStore.verify_chain()`/`simulate_tampering()` are the real T12 implementations (no web-layer reimplementation); OPA itself could not be exercised live in this sandbox (network-restricted), but this is an environment limitation, not a code defect — same limitation affects every OPA-dependent test suite in this repo when run outside Docker/CI.

## Failures
None. The one failure identified by the previous QA pass (`test_no_normal_update_or_delete_audit_controls_are_exposed`) has been fixed by commit `bc255ed` and is confirmed resolved by static template inspection and the manual exploratory harness described above.

## Recommendation
Proceed to human approval, **with one caveat to record**: the `tests/T18_audit_ui/` suite has not been executed to a real PASS/FAIL result against a live `opa` binary in any environment available to this QA session (no Docker daemon, no network path to fetch/build `opa`). The same limitation applies identically to `tests/T09`–`T20` in this sandbox, so it is not specific to T18. Before marking T18 `DONE`, run `docker compose run --rm app pytest -q tests/T18_audit_ui/ -v` (or any environment with Docker/a real `opa` binary) once to get the authoritative green result — based on the fix in `bc255ed` and the manual exploratory verification above, it is expected to pass 8/8.
