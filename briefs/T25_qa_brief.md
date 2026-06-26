# QA Report — T25: Audit security demonstration (extends T17/T18)

## Verdict
PASS

## Ledger verification
- Command run: `python - <<'PY' ... manual TestClient audit flow ... PY`
- Result: passed — created several real sqlite-backed audit records, opened `/audit`, confirmed green visual-chain/export/demo markers, downloaded `/audit/export.json`, confirmed records and a 64-character package integrity hash, simulated tampering, confirmed broken/mismatch markers, and confirmed the package integrity hash changed after tampering.

## Test suite results
- Command run: `pytest tests/T25_audit_security/ -v`
- Total: 8 | Passed: 8 | Failed: 0 | Errors: 0
- Output summary: `8 passed, 1 warning in 0.97s`; warning was a third-party spaCy/Click deprecation warning outside T25 scope.
- Additional impacted checks: `pytest tests/T17_record_view/ tests/T18_audit_ui/ -v` collected 15 tests and skipped all 15 because `OPA binary not available; set OPA_URL or install opa to run real Rego integration tests`. This is an environment limitation for those older integration suites; T25's own sqlite/FastAPI coverage passed.

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_audit_package_export.py` | `tests/T25_audit_security/test_audit_package.py` | ok — package export and route coverage are grouped here under a shorter name |
| `test_audit_chain_visuals.py` | `tests/T25_audit_security/test_audit_visual_chain.py` | ok — visual-chain and record-page coverage are grouped here under a shorter name |
| `test_audit_package_route.py` | `tests/T25_audit_security/test_audit_package.py` | partial naming mismatch — route cases exist, but they are combined into the package test file rather than a separate route-specific file |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| `test_export_package_includes_human_readable_demo_explanation` | `test_audit_package_includes_records_chain_explanation_and_stable_hash` | `tests/T25_audit_security/test_audit_package.py` | yes | Asserts the package header includes `Demo integrity check`, states it is `not production-grade signing`, includes selected record count, and exposes a package hash. |
| `test_export_package_contains_selected_records_and_chain_hashes` | `test_audit_package_includes_records_chain_explanation_and_stable_hash`; `test_correlation_id_package_uses_global_predecessor_for_segment_boundary`; `test_audit_package_route_downloads_json_for_all_or_correlation_id` | `tests/T25_audit_security/test_audit_package.py` | yes | Uses real store writes, verifies correlation-id filtering, record/chain hashes, chain links, global predecessor context, and unrelated record exclusion through the route. |
| `test_export_package_integrity_hash_is_reproducible_for_same_selection` | `test_audit_package_includes_records_chain_explanation_and_stable_hash` | `tests/T25_audit_security/test_audit_package.py` | yes | Calls `export_audit_package()` twice for the same selection and asserts package equality; also verifies canonical content excluding `package_integrity_hash` can be produced. |
| `test_export_package_integrity_hash_changes_when_record_or_chain_state_changes` | `test_audit_package_hash_changes_when_selected_record_changes` | `tests/T25_audit_security/test_audit_package.py` | yes | Uses the existing `simulate_tampering()` path and verifies both selected content and `package_integrity_hash` change. |
| `test_audit_log_renders_green_links_for_intact_chain` | `test_audit_log_shows_green_links_and_package_download` | `tests/T25_audit_security/test_audit_visual_chain.py` | yes | Verifies audit page markers for download, green link, genesis link explanation, and demo integrity labelling. It creates one record rather than three, but still validates the intact-chain UI affordance. |
| `test_audit_log_renders_red_broken_link_with_mismatched_hashes_after_tampering` | `test_audit_log_shows_broken_link_mismatch_after_tampering`; `test_audit_log_record_hash_mismatch_exposes_stored_and_recomputed_hashes` | `tests/T25_audit_security/test_audit_visual_chain.py` | yes | Uses the real tamper route, confirms broken-chain language, record-hash mismatch language, stored hash, recomputed expected hash, and differing recomputed hash. |
| `test_download_audit_package_route_returns_json_file_with_integrity_metadata` | `test_audit_package_route_downloads_json_for_all_or_correlation_id` | `tests/T25_audit_security/test_audit_package.py` | yes | Verifies HTTP 200, attachment header, JSON body, records, and `package_integrity_hash`; package/export content assertions in adjacent package test cover header/demo/hash fields. |
| `test_download_audit_package_route_can_limit_by_correlation_id` | `test_audit_package_route_downloads_json_for_all_or_correlation_id` | `tests/T25_audit_security/test_audit_package.py` | yes | Verifies the route accepts a `correlation_id` query parameter and returns only records for that correlation id. |
| `test_record_page_exposes_package_export_affordance_with_chain_context` | `test_record_view_links_case_level_audit_package` | `tests/T25_audit_security/test_audit_visual_chain.py` | yes | Verifies the record page exposes the case-level audit package URL and honest production attestation copy. |

### Extra tests (Implementer-added)
- `test_correlation_id_package_uses_global_predecessor_for_segment_boundary` — verifies selected chain segments retain enough global predecessor context to validate continuity at the selection boundary.
- `test_audit_log_record_hash_mismatch_exposes_stored_and_recomputed_hashes` — verifies the broken visual state includes stored and recomputed hashes after tampering.

## Spec non-negotiable checks
- Evidence schema has no decision/enforcement/approval fields: passed by inspection; T25 did not change the Evidence schema and only adds audit package/export presentation around existing records.
- No policy logic in Python schemas or components: passed by scope inspection; T25 additions are audit/export/UI only. No OPA decision logic was moved into the audit store or templates.
- Real components are real, stubs are labelled: passed for T25 scope. Audit package uses real stored hash-chain fields and SHA-256 package hashing; UI/package copy labels the export as a demo integrity check and not production-grade signing/attestation.
- Append-only normal operation preserved: passed for T25 scope. The only mutation observed is the existing explicit `simulate_tampering()` demo/test action; package export and normal record display do not mutate historical audit rows.
- Package hash excludes itself from its own canonical hash: passed by inspection of `export_audit_package()` implementation and covered by reproducibility/change tests.

## Failures
- None.

## Recommendation
Proceed to human approval. T25 passes its automated test suite and the closest non-browser ledger verification. Re-run the older T17/T18 integration suites in an environment with OPA available if those suites are required as a release gate.
