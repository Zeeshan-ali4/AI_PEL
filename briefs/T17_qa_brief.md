# QA Report — T17: Evidence record view + export

## Verdict
PASS

## Ledger verification
- Command run: real-OPA-backed `docker compose run --rm app pytest tests/T17_record_view -q` could not be run because no Docker daemon is available in this sandbox (`/var/run/docker.sock` does not exist). As an equivalent, the `opa` binary was built locally via `go install github.com/open-policy-agent/opa@latest` (using the allow-listed `proxy.golang.org` module proxy) and pointed at via the existing `opa_url` session fixture, then the full task pytest suite was run directly against a real OPA server and real pipeline/audit-store objects (sqlite-backed), exactly as the `tests/T17_record_view/conftest.py` real-OPA pattern intends.
- Result: passed. All 7 tests in `tests/T17_record_view/` pass against real OPA, real Presidio/spaCy, and a real `AuditStore` (no mocked decision/hash-chain/serialization behaviour).
- Manual "open a record; export; open the exported file" check: inspected `app/web/routes.py` (`record_view`, `record_export_json`, `record_export_html`) directly — all three are read-only lookups via `_get_record_or_404` → `pipeline.audit_store.read_records()`; no write/update path exists in these handlers.

## Test suite results
- Command run: `pytest tests/T17_record_view/ -v` (real OPA via locally built binary, `OPA_URL` unset so the session fixture launched its own server)
- Total: 7 | Passed: 7 | Failed: 0 | Errors: 0
- Output summary:
```
tests/T17_record_view/test_record_exports.py::test_json_export_is_downloadable_valid_json_and_faithful_to_persisted_record PASSED
tests/T17_record_view/test_record_exports.py::test_human_readable_export_is_printable_and_non_technical PASSED
tests/T17_record_view/test_record_exports.py::test_record_view_links_or_buttons_offer_both_audit_exports PASSED
tests/T17_record_view/test_record_exports.py::test_exports_for_unknown_record_return_404 PASSED
tests/T17_record_view/test_record_view.py::test_action_evaluation_record_page_opens_with_required_assurance_fields PASSED
tests/T17_record_view/test_record_view.py::test_approval_decision_record_page_shows_approver_reason_execution_and_reference_hash PASSED
tests/T17_record_view/test_record_view.py::test_unknown_record_identifier_returns_clear_404 PASSED
7 passed, 1 warning in 1.15s
```
- Regression check: also ran `pytest tests/T14_dashboard tests/T15_scenarios_ui tests/T16_approvals_ui tests/T17_record_view -q` (real OPA) — **36 passed**, 0 failed. No regression to existing dashboard/scenario/approval routes.

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `__init__.py` | `tests/T17_record_view/__init__.py` | ok |
| `conftest.py` | `tests/T17_record_view/conftest.py` | ok |
| `test_record_view.py` | `tests/T17_record_view/test_record_view.py` | ok |
| `test_record_exports.py` | `tests/T17_record_view/test_record_exports.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| test_action_evaluation_record_page_opens_with_required_assurance_fields | `test_action_evaluation_record_page_opens_with_required_assurance_fields` | test_record_view.py | yes | Runs scenario via real pipeline, requests `GET /records/{record_hash}`, asserts 200 and presence of record_hash, prev_hash, execution status, correlation id, enforcement mode, decision, control id text. |
| test_approval_decision_record_page_shows_approver_reason_execution_and_reference_hash | `test_approval_decision_record_page_shows_approver_reason_execution_and_reference_hash` | test_record_view.py | yes | Creates linked approval_decision record referencing original via `references_hash`; asserts approver, reason, execution result, and "appended"/distinct-from-original framing are visible. |
| test_unknown_record_identifier_returns_clear_404 | `test_unknown_record_identifier_returns_clear_404` | test_record_view.py | yes | Requests a syntactically plausible nonexistent 64-hex record_hash; asserts 404, not 500. |
| test_json_export_is_downloadable_valid_json_and_faithful_to_persisted_record | `test_json_export_is_downloadable_valid_json_and_faithful_to_persisted_record` | test_record_exports.py | yes | Requests `/records/{record_hash}/export.json`; parses JSON; checks faithfulness against persisted record fields and absence of decision/allow/block fields in the exported evidence object. |
| test_human_readable_export_is_printable_and_non_technical | `test_human_readable_export_is_printable_and_non_technical` | test_record_exports.py | yes | Requests `/records/{record_hash}/export.html`; asserts labelled sections (Action / Context used / Evidence / Binding decision / Execution status / Hash chain) and that body is not merely a raw JSON dump. |
| test_record_view_links_or_buttons_offer_both_audit_exports | `test_record_view_links_or_buttons_offer_both_audit_exports` | test_record_exports.py | yes | Opens a record page and asserts links/forms pointing at both export.json and export.html for the same record_hash. |
| test_exports_for_unknown_record_return_404 | `test_exports_for_unknown_record_return_404` | test_record_exports.py | yes | Parameterized/covered for both export formats against a nonexistent record_hash; asserts 404. |

All seven Test Brief cases are present, named consistently with the brief, and pass with real dependencies (no mocked OPA/Presidio/audit serialization).

### Extra tests (Implementer-added)
- None beyond the seven specified in the Test Brief.

## Spec non-negotiable checks
- Evidence schema has no decision/enforcement/approval field: passed (`app/schemas/evidence.py` — fields limited to `evaluated`, `contains_personal_data`, `contains_special_category_data`, `sensitivity_level`, `detected_entities`, `evidence_spans`, `vulnerability_indicators`, `overall_confidence`, `sensor_versions`, `sensor_error`).
- No policy logic added in Python for this task: passed (`record_view`, `record_export_json`, `record_export_html` in `app/web/routes.py` are pure read lookups against already-persisted `EvidenceRecord` rows; no new decision computation).
- Append-only / no mutation of audit records: passed (`_get_record_or_404` / `_record_view_context` only call `pipeline.audit_store.read_records()`; no write or update call exists in any T17 route).
- Real components stay real / stubs stay labelled (in scope for this task — evidence rendering): passed (the nuance-stub "model stand-in" label and OPA-sourced decision/control_id/framework_mapping text are preserved in the record view, sourced from the persisted real `Decision`/`Evidence` objects, not re-derived).
- File scope respected: passed (only `app/web/routes.py`, `app/web/templates/record.html`, and `tests/T17_record_view/` were touched, matching the Architect Brief's allowed-files list).

## Failures
None.

## Recommendation
Proceed to human approval / Release Manager. All 7 Test Brief cases pass against real OPA, real Presidio/spaCy sensors, and the real append-only audit store (verified directly in this environment by building the `opa` binary from source via the allow-listed Go module proxy, since Docker was unavailable). No regressions found in T14–T16 UI test suites (36/36 passed). The prior Reviewer Brief's "not run" caveat for the Verify step is now resolved — the suite has been executed end-to-end with real dependencies, not just statically reviewed.
