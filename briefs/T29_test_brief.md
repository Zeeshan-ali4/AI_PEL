# Test Brief — T29: Evidence schema versioning + regulatory export framing

## Spec references
- `MASTER_SPEC.md`: §0 spec version/status and change log; §5 canonical schemas; §5.3 Evidence boundary (Evidence remains evidence-only with no allow/block/decision/approval/enforcement fields); §5.5 Evidence Record hash-chained audit row; §8A.5 audit/evidence record UI and export expectations; §9 assurance narrative and regulatory-reporting framing.
- `TASK_LEDGER.md`: T29 goal, allowed files, key notes, Done when criteria, Verify step, and reviewer focus. Dependencies T02 and T25 are marked done, so T29 may proceed.
- `briefs/T29_architect_brief.md`: add exactly one `EvidenceRecord` field, populate it for all new writes, surface it in record views and exports, update Beat 9 narration only, and preserve existing T25 tamper-evident audit-package mechanics.

## Target test location
- Folder: `tests/T29_evidence_schema_version/`
- Suggested files:
  - `__init__.py` — package marker for the T29 test folder.
  - `test_schema_and_store.py` — covers schema-field presence, write-time population for `action_evaluation`, write-time population for `approval_decision`, JSON audit package inclusion, and hash-chain preservation.
  - `test_exports_and_templates.py` — covers record JSON export inclusion, printable HTML export inclusion, record view visibility, audit log/package-framing visibility, and Beat 9 narration text.
  - `test_spec_contract.py` — covers spec-first contract assertions in `MASTER_SPEC.md` and guards the Evidence schema boundary.

## Test cases

### test_spec_documents_evidence_schema_version_and_bumps_status
- **Traces to:** `TASK_LEDGER.md` T29 Done when #3; architect brief spec-first discipline; `MASTER_SPEC.md` §0 and §5.5.
- **Input:** Read `MASTER_SPEC.md` as text.
- **Expected outcome:**
  - The status line is bumped from the current pre-T29 `v1.1` to a later explicit version.
  - The change log/status area mentions evidence schema versioning or equivalent T29 schema-version governance wording.
  - §5.5 `Evidence Record` JSON includes exactly one new top-level field named `evidence_schema_version`.
- **Notes:** This is a contract test against the source of truth. It should not attempt to infer commit ordering, but it must fail if the spec omits the field or leaves the version unchanged.

### test_evidence_schema_still_has_no_decision_or_enforcement_fields
- **Traces to:** Non-negotiable product rule; `MASTER_SPEC.md` §5.3; `TASK_LEDGER.md` golden rule 4; architect brief non-negotiables.
- **Input:** Inspect the Pydantic `Evidence` model fields and/or `MASTER_SPEC.md` §5.3 Evidence JSON block.
- **Expected outcome:** Evidence still has no `allow`, `block`, `decision`, `approval`, `approved`, `enforcement`, `executed`, or `evidence_schema_version` field.
- **Notes:** T29 adds schema versioning to `EvidenceRecord` only. This test protects against accidentally putting governance/decision metadata into the Evidence sensor schema.

### test_evidence_record_model_requires_and_serializes_schema_version
- **Traces to:** `MASTER_SPEC.md` §5.5; `TASK_LEDGER.md` T29 Done when #1 and #3.
- **Input:** Build a valid `EvidenceRecord` example using existing T02-style hand-built `Action`, `Context`, `Evidence`, and `Decision` objects, with `evidence_schema_version` set to the store constant value.
- **Expected outcome:**
  - `EvidenceRecord.model_fields` contains `evidence_schema_version` with type `str`.
  - A valid model instance accepts the version value and `model_dump(mode="json")` contains `evidence_schema_version` at the record top level.
  - Omitting `evidence_schema_version` from direct model construction raises a Pydantic validation error.
- **Notes:** This verifies the schema contract directly; it should not assert implementation internals beyond the public constant value if exposed.

### test_write_record_populates_schema_version_for_action_evaluation
- **Traces to:** `TASK_LEDGER.md` T29 Done when #1; architect brief implementation objective.
- **Input:** Use `AuditStore(database_url="sqlite:///<tmp_path>/audit.db")` and write a normal `action_evaluation` record with valid `Action`, `Context`, `Evidence`, and `Decision` fixtures.
- **Expected outcome:**
  - The returned `EvidenceRecord.evidence_schema_version` is a non-empty string matching the configured evidence schema version constant.
  - `store.read_records()[0].evidence_schema_version` matches the returned value.
  - `store.verify_chain().intact` remains `True`.
- **Notes:** SQLite is acceptable here because the existing store intentionally supports it for real persistence semantics in tests. Do not mock the audit store.

### test_write_record_populates_schema_version_for_approval_decision
- **Traces to:** `MASTER_SPEC.md` §5.5 append-only approvals; `TASK_LEDGER.md` T29 Done when #1.
- **Input:** Write an initial `action_evaluation` record, then write a second `approval_decision` record with the same `correlation_id`, `references_hash` equal to the first record's `record_hash`, `human_approver`, `approval_reason`, and an approval/rejection execution result.
- **Expected outcome:**
  - Both records carry the same non-empty `evidence_schema_version` value.
  - The approval record preserves `record_type == "approval_decision"`, `references_hash == original.record_hash`, approver, reason, and executed state.
  - `store.verify_chain().intact` remains `True`.
- **Notes:** This guards the often-missed secondary write path and the append-only approval rule.

### test_audit_package_json_includes_schema_version_for_every_record
- **Traces to:** `TASK_LEDGER.md` T29 Done when #2; T25 audit package export contract; architect brief preserve package integrity behaviour.
- **Input:** Write at least two records, including an `approval_decision`, then call `AuditStore.export_audit_package(correlation_id=<case correlation id>)`.
- **Expected outcome:**
  - Every item in `package["records"]` contains a top-level `evidence_schema_version` equal to the configured value.
  - The package still contains T25 fields: `header`, `selection`, `chain_links`, `records`, and `package_integrity_hash`.
  - At least one chain link remains marked intact for the selected records, and recomputing or repeated export of unchanged data remains stable under the existing T25 expectations.
- **Notes:** This verifies inclusion in the JSON audit package without changing the T25 export mechanism.

### test_record_json_export_includes_schema_version
- **Traces to:** `TASK_LEDGER.md` T29 Done when #2 and Verify step; record export routes from T17/T25.
- **Input:** Use the FastAPI `TestClient` with a real test audit store dependency override or existing project helper to create one record, then request `/records/{record_hash}/export.json`.
- **Expected outcome:**
  - HTTP status is `200`.
  - The response JSON includes top-level `evidence_schema_version` equal to the configured value.
  - Existing JSON export fields such as `record_hash`, `prev_hash`, `action`, `evidence`, and `decision` are still present.
- **Notes:** This is the per-record JSON export, distinct from the audit package JSON export.

### test_printable_record_html_export_displays_schema_version
- **Traces to:** `TASK_LEDGER.md` T29 Done when #2 and Verify step; `MASTER_SPEC.md` §8A.5 assurance UI/export requirements.
- **Input:** Create one record and request `/records/{record_hash}/export.html`.
- **Expected outcome:**
  - HTTP status is `200`.
  - Response body contains a human-readable label such as `Evidence schema version` and the version value.
  - Printable export wording still includes offline audit/printing context and does not remove hash-chain fields.
- **Notes:** This verifies the printable HTML export specifically, not just the interactive record page.

### test_record_page_displays_schema_version
- **Traces to:** `TASK_LEDGER.md` T29 Done when #2; `MASTER_SPEC.md` §8A.5.
- **Input:** Create one record and request `/records/{record_hash}`.
- **Expected outcome:**
  - HTTP status is `200`.
  - Response body contains `Evidence schema version` and the version value.
  - Existing record actions/links remain visible, including JSON export, printable HTML export, and audit package download links.
- **Notes:** This is the primary buyer-facing record view required by T29.

### test_audit_log_or_package_framing_mentions_schema_versioning
- **Traces to:** `TASK_LEDGER.md` T29 Done when #2; architect brief requirement to mention/show it in the audit log or audit-package export description.
- **Input:** Request `/audit` after writing a record, and/or inspect the audit package header returned by `export_audit_package` or `/audit/export.json`.
- **Expected outcome:** At least one buyer-facing audit-log/package-framing surface includes clear wording that audit packages/records carry an evidence schema version so reviewers can see the definition of captured evidence is governed.
- **Notes:** The ledger allows the field to be included in the audit log table or package export description. Prefer asserting both if implemented, but the minimum functional acceptance is one of those surfaces plus the JSON record data.

### test_demo_script_beat_9_mentions_schema_versioning_without_reordering_beats
- **Traces to:** `TASK_LEDGER.md` T29 Done when #4; architect brief narration-only constraint.
- **Input:** Read `DEMO_SCRIPT.md` as text.
- **Expected outcome:**
  - Beat 9 contains schema-versioning narration similar in meaning to the ledger example: the audit package shows not only what was captured, but that the definition of captured evidence was controlled/versioned.
  - Beat 9 still covers audit integrity, chain verification/tamper detection, and package export.
  - No unrelated beat headings are removed or reordered.
- **Notes:** This is a content acceptance test. It should avoid overfitting to exact prose, but must catch absence of schema-versioning framing.

## Coverage checklist
- [x] Happy path covered: new action-evaluation records carry and export the schema version.
- [x] Error/edge cases covered: direct model omission fails validation; approval-decision secondary write path is covered; Evidence schema boundary is guarded.
- [x] Spec non-negotiables verified: Evidence remains decision/enforcement-free; OPA/policy decision semantics are not part of this task; append-only approval records remain intact.
- [x] Real dependencies flagged: audit-store tests must use a real persisted store path (SQLite test mode or Postgres), not mocks; UI/export tests must exercise FastAPI/Jinja rendering or exported package functions directly. OPA and Presidio are not required for these T29 acceptance tests unless the implementer chooses an end-to-end scenario test in addition to the specified coverage.

## Gaps or ambiguities
- The ledger says printable HTML export must include the field. Existing code has per-record printable HTML export and JSON audit-package export; it does not currently show a separate printable HTML audit-package export path in the inspected routes. The tests should therefore target `/records/{record_hash}/export.html` for printable HTML inclusion unless the implementer identifies an existing package-level printable route.
- The ledger's Verify step asks to confirm `MASTER_SPEC.md` schema update predates code change in commit order. A pytest test cannot reliably prove chronological editing order inside a single working tree. The reviewer should check the final diff/commit narrative for spec-first discipline; tests should assert the resulting spec contract.
