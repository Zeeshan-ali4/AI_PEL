# QA Report — T18: Audit log + verify chain + simulate tampering (headline moment)

## Verdict
FAIL (one test failure — minor copy/test wording mismatch, not a behavioural defect)

## Ledger verification
- Command run: manual exercise via `TestClient` against a real `opa` binary (downloaded for this sandbox, no Docker daemon available) and real sqlite-backed `AuditStore`/`SettingsStore` (mirrors the `wired_pipeline` fixture pattern already used by T15–T17).
- Steps performed: ran scenarios 1–3 through `/run/{id}`, then `GET /audit`, then `POST /audit/verify`, then `POST /audit/simulate-tampering` with a real `record_id`.
- Result: **passed.**
  - `/audit` → 200, lists records.
  - `/audit/verify` → 200, page text contains "intact" and "verified" with a real count.
  - `/audit/simulate-tampering` (record_id=1) → 200, page shows a red "Chain broken — tampering detected" panel naming the exact failing record (`id 1`) and reason (`record_hash mismatch`), with a "Verified 0 records before the break" count — all values came from the real `AuditStore.verify_chain()` / `simulate_tampering()` calls, not hard-coded copy.
- `docker compose up` itself could not be run — no Docker daemon socket available in this execution environment (`/var/run/docker.sock` missing). Used direct Python/pytest execution with a real `opa` binary and real sqlite/Postgres-capable stores instead, which exercises the same code paths the architect brief's verify step requires (real `verify_chain`/`simulate_tampering`, no Docker-specific behaviour in scope for T18).

## Test suite results
- Command run: `python -m pytest tests/T18_audit_ui/ -v` (real `opa` binary on PATH, real Presidio/spaCy installed, sqlite-backed stores per the existing `wired_pipeline` fixture — no mocks).
- Total: 8 | Passed: 7 | Failed: 1 | Errors: 0
- Full repo regression check: `python -m pytest -q tests/` → 191 passed, 1 failed (the same T18 failure), 2 skipped (pre-existing, unrelated to T18). No other regressions introduced.
- Failure:
  - `test_no_normal_update_or_delete_audit_controls_are_exposed` fails on `assert "delete" not in page`. The word "delete" appears in **explanatory prose**, not a control:
    > "...Nothing in normal operation edits or **deletes** a row — each record links to the one before it by hash..."
    This is copy describing append-only behaviour (the correct message), not an actual delete button/link/form. No `/audit/update`, `/audit/delete`, or `>edit<` control exists on the page (those three assertions in the same test all pass). This is a substring-matching test that doesn't distinguish prose from controls.

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_audit_log_page.py` | `tests/T18_audit_ui/test_audit_log_page.py` | ok |
| `test_audit_integrity_actions.py` | `tests/T18_audit_ui/test_audit_integrity_actions.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|---|---|---|---|---|
| test_audit_log_lists_records_chronologically_with_assurance_fields | `test_audit_log_lists_records_chronologically_with_assurance_fields` | test_audit_log_page.py | yes | passes; checks id, created time, record_type, correlation_id, decision, executed, record_hash, prev_hash |
| test_audit_log_includes_record_detail_links_when_records_exist | `test_audit_log_includes_record_detail_links_when_records_exist` | test_audit_log_page.py | yes | passes; links resolve to existing T17 `/records/{hash}` view |
| test_audit_log_empty_or_minimal_state_is_board_readable | `test_audit_log_empty_or_minimal_state_is_board_readable` | test_audit_log_page.py | yes | passes |
| test_reset_or_reseed_affordance_is_present_without_new_subsystem_assumption | `test_reset_or_reseed_affordance_is_present_without_new_subsystem_assumption` | test_audit_log_page.py | yes | passes; reuses existing `/scenarios` workflow guidance, no new subsystem |
| test_verify_chain_shows_green_intact_status_and_count | `test_verify_chain_shows_green_intact_status_and_count` | test_audit_integrity_actions.py | yes | passes; uses real `verify_chain()` |
| test_simulate_tampering_breaks_chain_and_names_exact_failing_record | `test_simulate_tampering_breaks_chain_and_names_exact_failing_record` | test_audit_integrity_actions.py | yes | passes; uses real `simulate_tampering()`, names exact `broken_record_id` |
| test_simulate_tampering_action_is_labelled_demo_only | `test_simulate_tampering_action_is_labelled_demo_only` | test_audit_integrity_actions.py | yes | passes |
| test_no_normal_update_or_delete_audit_controls_are_exposed | `test_no_normal_update_or_delete_audit_controls_are_exposed` | test_audit_integrity_actions.py | partial | **fails** — false-positive substring match on the word "deletes" inside append-only explanatory copy; the underlying behavioural requirement (no edit/delete controls) is otherwise satisfied (`/audit/update`, `/audit/delete`, `>edit<` all absent) |

### Extra tests (Implementer-added)
- None beyond the seven scenarios mapped above plus the one additional case — all eight test brief cases have a 1:1 corresponding test function; no brief case was skipped or silently merged.

## Spec non-negotiable checks
- Real `verify_chain()`/`simulate_tampering()` used (no web-layer reimplementation of hashing): **passed** — confirmed by manual route exercise above and by reading `app/web/routes.py`, which calls `AuditStore.verify_chain()` / `AuditStore.simulate_tampering()` directly.
- Audit table remains append-only in normal operation; only the named demo helper mutates a row: **passed** — no generic edit/update/delete route exists; only `/audit/simulate-tampering` mutates, and it is visibly labelled demo-only ("Chain broken — tampering detected" panel, explanatory copy distinguishing it from normal operation).
- Integrity result visually unambiguous (green/intact with count, or red/broken naming the exact failing record): **passed** — confirmed live: intact state shows verified count; broken state names `id 1` and reason `record_hash mismatch`.
- No schema/policy/scenario drift: **passed** — T18 touched only `app/web/routes.py`, `app/web/templates/audit.html`, `app/web/templates/base.html` (nav link), and `tests/T18_audit_ui/`, matching the allowed file list exactly.
- Stubs labelled / real components real: **passed** — OPA and the hash chain are exercised for real in this QA run (no mocks); Presidio/spaCy installed and used by the broader suite without failures.

## Failures
- `tests/T18_audit_ui/test_audit_integrity_actions.py::test_no_normal_update_or_delete_audit_controls_are_exposed` fails because the page's explanatory copy uses the word "deletes" in a sentence describing append-only behaviour, which trips the test's blunt `"delete" not in page` substring check. This is a test-assertion specificity issue, not a product defect — no actual delete control exists on the page. Per QA role constraints, I have not modified code or tests. Recommend either (a) the PM/BA narrows this assertion to look for delete-control markup specifically (e.g. `>delete<`, `/audit/delete`, `name="delete"`) rather than the bare substring "delete", or (b) the Implementer rewords the explanatory copy to avoid the word "deletes" — either fix keeps the non-negotiable (no real delete control) intact.

## Recommendation
Fix required before this task can be marked `DONE`. The implementation itself satisfies every architect-brief non-negotiable and 7 of 8 test-brief cases on real dependencies (real OPA, real hash chain, real sqlite-backed audit store, no mocks), including the headline tamper-detection moment, which I verified manually end-to-end. The one failure is a test-wording false positive against safe, accurate copy — route back to PM/BA or Implementer to adjust either the assertion or the copy, then re-run `pytest tests/T18_audit_ui/ -v` for a clean pass before proceeding to human approval.
