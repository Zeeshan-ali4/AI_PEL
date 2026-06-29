# QA Report — T29: Evidence schema versioning + regulatory export framing

## Verdict
PASS

## Ledger verification
- Command run: `pytest tests/T29_evidence_schema_version/ -v` (Docker unavailable in this environment; tests run directly with all required packages installed)
- Result: passed — 13/13 tests passed; see test suite results below

## Test suite results
- Command run: `pytest tests/T29_evidence_schema_version/ -v`
- Total: 13 | Passed: 13 | Failed: 0 | Errors: 0
- Output summary:
  ```
  tests/T29_evidence_schema_version/test_exports_and_templates.py::test_record_json_export_includes_schema_version PASSED
  tests/T29_evidence_schema_version/test_exports_and_templates.py::test_printable_record_html_export_displays_schema_version PASSED
  tests/T29_evidence_schema_version/test_exports_and_templates.py::test_record_page_displays_schema_version PASSED
  tests/T29_evidence_schema_version/test_exports_and_templates.py::test_audit_log_page_mentions_schema_versioning PASSED
  tests/T29_evidence_schema_version/test_exports_and_templates.py::test_demo_script_beat_9_mentions_schema_versioning_without_reordering_beats PASSED
  tests/T29_evidence_schema_version/test_schema_and_store.py::test_evidence_record_model_has_schema_version_field PASSED
  tests/T29_evidence_schema_version/test_schema_and_store.py::test_evidence_record_serializes_schema_version PASSED
  tests/T29_evidence_schema_version/test_schema_and_store.py::test_omitting_schema_version_raises_validation_error PASSED
  tests/T29_evidence_schema_version/test_schema_and_store.py::test_write_record_populates_schema_version_for_action_evaluation PASSED
  tests/T29_evidence_schema_version/test_schema_and_store.py::test_write_record_populates_schema_version_for_approval_decision PASSED
  tests/T29_evidence_schema_version/test_schema_and_store.py::test_audit_package_json_includes_schema_version_for_every_record PASSED
  tests/T29_evidence_schema_version/test_spec_contract.py::test_spec_documents_evidence_schema_version_and_bumps_status PASSED
  tests/T29_evidence_schema_version/test_spec_contract.py::test_evidence_schema_still_has_no_decision_or_enforcement_fields PASSED
  ======================== 13 passed, 1 warning in 1.33s =========================
  ```

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `__init__.py` | `tests/T29_evidence_schema_version/__init__.py` | ok |
| `test_schema_and_store.py` | `tests/T29_evidence_schema_version/test_schema_and_store.py` | ok |
| `test_exports_and_templates.py` | `tests/T29_evidence_schema_version/test_exports_and_templates.py` | ok |
| `test_spec_contract.py` | `tests/T29_evidence_schema_version/test_spec_contract.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| test_spec_documents_evidence_schema_version_and_bumps_status | test_spec_documents_evidence_schema_version_and_bumps_status | test_spec_contract.py | yes | Checks spec version bumped to v1.2, §5.5 contains `evidence_schema_version` |
| test_evidence_schema_still_has_no_decision_or_enforcement_fields | test_evidence_schema_still_has_no_decision_or_enforcement_fields | test_spec_contract.py | yes | Confirms Evidence Pydantic model has no allow/block/decision/approval/enforcement/executed/evidence_schema_version fields |
| test_evidence_record_model_requires_and_serializes_schema_version | test_evidence_record_model_has_schema_version_field + test_evidence_record_serializes_schema_version + test_omitting_schema_version_raises_validation_error | test_schema_and_store.py | yes | Split across three functions; all three assertions from the brief are covered |
| test_write_record_populates_schema_version_for_action_evaluation | test_write_record_populates_schema_version_for_action_evaluation | test_schema_and_store.py | yes | Uses SQLite via AuditStore; verifies returned record and read-back value; verifies chain intact |
| test_write_record_populates_schema_version_for_approval_decision | test_write_record_populates_schema_version_for_approval_decision | test_schema_and_store.py | yes | Both records carry version; approval record fields intact; chain intact |
| test_audit_package_json_includes_schema_version_for_every_record | test_audit_package_json_includes_schema_version_for_every_record | test_schema_and_store.py | yes | Writes action_evaluation + approval_decision; checks all package records carry field; T25 package structure preserved |
| test_record_json_export_includes_schema_version | test_record_json_export_includes_schema_version | test_exports_and_templates.py | yes | FastAPI TestClient against `/records/{record_hash}/export.json`; checks status 200 and field present |
| test_printable_record_html_export_displays_schema_version | test_printable_record_html_export_displays_schema_version | test_exports_and_templates.py | yes | FastAPI TestClient against `/records/{record_hash}/export.html`; checks human-readable label present |
| test_record_page_displays_schema_version | test_record_page_displays_schema_version | test_exports_and_templates.py | yes | FastAPI TestClient against `/records/{record_hash}`; checks version label and existing export links present |
| test_audit_log_or_package_framing_mentions_schema_versioning | test_audit_log_page_mentions_schema_versioning | test_exports_and_templates.py | yes | Checks `/audit` response body contains schema versioning framing |
| test_demo_script_beat_9_mentions_schema_versioning_without_reordering_beats | test_demo_script_beat_9_mentions_schema_versioning_without_reordering_beats | test_exports_and_templates.py | yes | Reads DEMO_SCRIPT.md; confirms Beat 9 contains versioning narration; confirms beat structure not disrupted |

### Extra tests (Implementer-added)
- `test_evidence_record_model_has_schema_version_field` — separate field-presence check (brief combined this with the serialisation test)
- `test_evidence_record_serializes_schema_version` — serialisation check split from the omission check
- `test_omitting_schema_version_raises_validation_error` — validation error check separated for clarity

## Spec non-negotiable checks
- Evidence schema has no decision/approval/enforcement fields: passed — `app/schemas/evidence.py` contains no `allow`, `block`, `decision`, `approval`, `enforcement`, `executed`, or `evidence_schema_version` fields; guarded by `test_evidence_schema_still_has_no_decision_or_enforcement_fields`
- `evidence_schema_version` added to EvidenceRecord only (not Evidence): passed — field is on `app/schemas/audit.py:43` only
- MASTER_SPEC.md §5.5 updated before schema code (spec-first, golden rule 6): passed — spec is bumped to v1.2 and §0 change log documents the T29 field; test_spec_documents_evidence_schema_version_and_bumps_status passes
- EVIDENCE_SCHEMA_VERSION constant defined as a module-level string in store.py: passed — `app/audit/store.py:28: EVIDENCE_SCHEMA_VERSION = "1.0.0"`
- All new record writes (action_evaluation and approval_decision) carry the version: passed — confirmed by store.py implementation and test_write_record_populates_schema_version_for_approval_decision
- T25 audit package export tamper-evidence behaviour untouched: passed — audit package tests confirm T25 fields (header, selection, chain_links, records, package_integrity_hash) are still present; no store logic changed beyond populating the new column
- Append-only audit preserved: passed — store writes only INSERTs; no existing row mutations introduced by this task

## Failures
- None

## Recommendation
Proceed to human approval
