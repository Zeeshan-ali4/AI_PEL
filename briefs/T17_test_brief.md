# Test Brief — T17: Evidence record view + export

## Spec references
- MASTER_SPEC.md: §1 and §1A (evidential reliability, exportable record, human oversight); §5.5 Evidence Record schema and append-only approval semantics; §8A item 5 Evidence record view; §12 acceptance criterion for "Export for audit".
- TASK_LEDGER.md: T17 Goal, Files, Done when, Verify, and Reviewer focus: full single-record readable/printable view showing `record_hash`, `prev_hash`, approver, reason, execution status; exports JSON plus a human-readable file that a non-technical risk reviewer can read.
- Architect Brief: T17 route scope is read-only single-record display/export only; record lookup should return a clear 404 for missing identifiers; record view/export must handle both `action_evaluation` and `approval_decision` rows; JSON export must faithfully serialize the persisted record; human-readable export must use clear labels and sections rather than a raw dump.

## Target test location
- Folder: `tests/T17_record_view/`
- Suggested files:
  - `__init__.py` — package marker for the T17 test folder.
  - `conftest.py` — shared FastAPI test-client setup and deterministic audit-record fixtures, following the existing UI test pattern where practical.
  - `test_record_view.py` — covers opening single records, missing-record handling, and rendering of required hash/execution/approval fields.
  - `test_record_exports.py` — covers JSON export fidelity and human-readable export readability/download behaviour.

## Test cases

### test_action_evaluation_record_page_opens_with_required_assurance_fields
- **Traces to:** MASTER_SPEC.md §5.5 Evidence Record schema; §8A item 5; TASK_LEDGER T17 Done when and Verify.
- **Input:** Create or run a scenario that writes one `action_evaluation` audit record, then request the single-record page for that record using its stable identifier, preferably `GET /records/{record_hash}` if implemented per the Architect Brief.
- **Expected outcome:** Response status is `200`; page includes the exact `record_hash`, exact `prev_hash`, `record_type`/plain-English equivalent for action evaluation, execution status, correlation ID, created timestamp, enforcement mode, decision value, control ID or "None" when absent, and framework mapping text where present.
- **Notes:** This is a functional UI test. It should assert user-visible text, not implementation helper functions. The rendered content must be readable and sectioned, not merely a raw JSON blob.

### test_approval_decision_record_page_shows_approver_reason_execution_and_reference_hash
- **Traces to:** MASTER_SPEC.md §5.5 append-only approvals; §8A item 5; TASK_LEDGER T17 Goal.
- **Input:** Arrange an original `action_evaluation` record and append a linked `approval_decision` record with `human_approver`, `approval_reason`, `executed`, and `references_hash` set to the original record hash. Request the single-record page for the approval record.
- **Expected outcome:** Response status is `200`; page displays the approval record hash, previous hash, reference/original record hash, human approver, approval reason, and execution result. The page must make clear that this is an appended approval decision record, not a mutation of the original evaluation record.
- **Notes:** The test should verify both approve (`executed=true`) and reject (`executed=false`) wording if cheaply parameterized; at minimum it must cover one linked approval decision record with a non-empty reason.

### test_unknown_record_identifier_returns_clear_404
- **Traces to:** Architect Brief non-negotiable: missing/unknown identifiers return a clear 404, not a server error.
- **Input:** Request the record page for a syntactically plausible but nonexistent record hash such as `GET /records/` plus 64 hex characters that are not present in the test audit store.
- **Expected outcome:** Response status is `404`; response contains a clear not-found message or FastAPI detail. It must not return `500` or an unhandled template/storage exception.
- **Notes:** Keep this scoped to T17 routes only; do not require a chronological audit-log page from T18.

### test_json_export_is_downloadable_valid_json_and_faithful_to_persisted_record
- **Traces to:** MASTER_SPEC.md §5.5 Evidence Record schema; §8A item 5; TASK_LEDGER T17 Goal "Export for audit" producing JSON.
- **Input:** Create or run a scenario to generate an `action_evaluation` record, then request its JSON export route, preferably `GET /records/{record_hash}/export.json`.
- **Expected outcome:** Response status is `200`; content type is JSON or a JSON download; `Content-Disposition` indicates an attachment/download if implemented; parsed JSON contains faithful persisted values for `record_hash`, `prev_hash`, `correlation_id`, `record_type`, `executed`, `enforcement_mode`, `action`, `context_used`, `evidence`, `decision`, and `created_at`. The exported evidence object must not contain any decision/approval/enforcement field.
- **Notes:** This must check persisted schema fidelity rather than a lossy summary. It should not mock the audit record serialization if the existing app can create real records through the pipeline/test fixtures.

### test_human_readable_export_is_printable_and_non_technical
- **Traces to:** MASTER_SPEC.md §1A evidential reliability; §8A item 5; TASK_LEDGER T17 Done when and Reviewer focus.
- **Input:** Generate an audit record and request the human-readable export route, preferably `GET /records/{record_hash}/export.html`.
- **Expected outcome:** Response status is `200`; content type is HTML or another agreed human-readable file type; `Content-Disposition` indicates an attachment/download if implemented. Body includes clear labels/sections such as "Evidence record", "Action", "Context used", "Evidence", "Binding decision", "Execution status", and "Hash chain" or equivalent. Body includes the record hash and previous hash. The export must not be only raw JSON/preformatted dump.
- **Notes:** HTML is acceptable and preferred for this task; do not require PDF generation. Assertions should focus on reviewer-readable labels and printable/downloadable behaviour.

### test_record_view_links_or_buttons_offer_both_audit_exports
- **Traces to:** MASTER_SPEC.md §8A item 5; TASK_LEDGER T17 Goal "Export for audit" producing JSON + human-readable file.
- **Input:** Open any existing single-record page.
- **Expected outcome:** Page presents user-visible export affordances for both JSON and human-readable export. Link targets or form actions point to the implemented export routes for the same record identifier.
- **Notes:** This verifies the user can discover exports from the record view without relying on undocumented URLs.

### test_exports_for_unknown_record_return_404
- **Traces to:** Architect Brief non-negotiable: missing/unknown record identifiers should return clear 404s.
- **Input:** Request JSON and human-readable export routes for a nonexistent record hash.
- **Expected outcome:** Each response status is `404` and no file content is generated.
- **Notes:** Parameterize across export formats where convenient.

## Coverage checklist
- [x] Happy path covered: action-evaluation record opens; JSON export and human-readable export succeed.
- [x] Error/edge cases covered: unknown record page/export returns 404; approval-decision records are handled distinctly from action-evaluation records.
- [x] Spec non-negotiables verified: evidence remains evidence-only in exported JSON; approval decisions are displayed as appended linked records; hash fields and execution status are visible; no T18 audit-log/verify-chain/tamper UI is required.
- [x] Real dependencies flagged (no mocks where forbidden): use the existing real app/pipeline/audit-store fixtures where practical. Do not mock Presidio, OPA, or hash-chain behaviour if the test generates records via the pipeline; if a lightweight test audit store fixture is used, it must still create real `EvidenceRecord` schema/store objects with real hashes rather than hand-written response bodies.

## Gaps or ambiguities
- The ledger requires JSON plus a human-readable file but does not mandate exact route names, file names, or content-disposition text. The Architect Brief recommends `/records/{record_hash}`, `/records/{record_hash}/export.json`, and `/records/{record_hash}/export.html`; tests should prefer these routes if implemented, or align to the implementer's chosen route shape while preserving the same behaviours.
- The ledger says "open the exported file" but programmatic tests cannot literally open a downloaded file in a browser. The acceptance equivalent is to request the export endpoint, validate status/content type/download metadata, parse JSON for the JSON export, and assert readable labelled sections for the human-readable export.
