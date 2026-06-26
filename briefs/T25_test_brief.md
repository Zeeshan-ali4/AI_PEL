# Test Brief — T25: Audit security demonstration (extends T17/T18)

## Spec references
- MASTER_SPEC.md: §1 proof point 7 and honesty principle; §5.5 Evidence Record and hash rule; §8A items 5–6 for evidence records, export, verify chain, and simulated tampering; §12 acceptance criteria for audit integrity and demo assurance.
- TASK_LEDGER.md: T25 dependencies, allowed files, key notes, done criteria, Verify step, and reviewer focus.
- Architect Brief: `briefs/T25_architect_brief.md` non-negotiables and package export requirements.

## Target test location
- Folder: `tests/T25_audit_security/`
- Suggested files:
  - `test_audit_package_export.py` — covers audit package JSON content, explanation/demo labelling, selected-record filtering, full chain hash fields, deterministic package integrity hash, and package hash changes when record content or chain state changes.
  - `test_audit_chain_visuals.py` — covers audit log rendering of green intact visual links, red broken-link state after simulated tampering, and mismatched hash display suitable for a non-technical reviewer.
  - `test_audit_package_route.py` — covers the HTTP download route for audit packages, including content type/download headers, correlation-id selection, and presence of integrity metadata in the returned JSON.

## Test cases

### test_export_package_includes_human_readable_demo_explanation
- **Traces to:** MASTER_SPEC.md §1 honesty principle; TASK_LEDGER.md T25 Done when items 4–5; Architect Brief non-negotiable “demo integrity check — production would use signed attestation.”
- **Input:** Create at least two real audit records using the repository’s audit store path, then call `export_audit_package()` for the selected records.
- **Expected outcome:** Exported package includes a human-readable explanation/header that states what the hashes mean, how the package can be checked, and that this is a demo-grade integrity check rather than production-grade signing or PKI attestation.
- **Notes:** This is acceptance coverage for the buyer-facing honesty requirement. The test should assert meaningful substrings, not exact prose, so copy can remain readable.

### test_export_package_contains_selected_records_and_chain_hashes
- **Traces to:** MASTER_SPEC.md §5.5 Evidence Record; TASK_LEDGER.md T25 Done when item 3; Architect Brief `export_audit_package()` requirements.
- **Input:** Write multiple real audit records, including at least two records sharing one `correlation_id` and one unrelated record. Export by that `correlation_id` or equivalent supported selection.
- **Expected outcome:** Package contains only the selected records; every packaged record exposes full `record_hash` and `prev_hash`; package metadata describes the selection; adjacent/link information is present enough to verify continuity for the selected chain segment.
- **Notes:** Use real audit-store writes and real hash-chain values. Do not mock the audit store or fabricate chain fields.

### test_export_package_integrity_hash_is_reproducible_for_same_selection
- **Traces to:** TASK_LEDGER.md T25 Key notes “package_integrity_hash computed over the entire bundle”; Architect Brief deterministic package requirement.
- **Input:** Export the same selected records twice without changing any audit data.
- **Expected outcome:** Both packages have identical `package_integrity_hash` values and identical canonical package content excluding any non-deterministic transport-only fields. The integrity hash must be computed over package content excluding the hash field itself.
- **Notes:** This verifies the package can be checked consistently by an external reviewer. If timestamps are included in package metadata, they must either be deterministic for the tested selection or excluded from the integrity hash in a documented way.

### test_export_package_integrity_hash_changes_when_record_or_chain_state_changes
- **Traces to:** MASTER_SPEC.md §5.5 hash rule; TASK_LEDGER.md T25 Verify step “Download package again — confirm the integrity hash has changed”; Architect Brief package hash stability/change requirement.
- **Input:** Export a package, then use the existing T18 tamper/simulate-tampering path or an explicit test fixture operation that changes a selected record’s content or chain state in the same way the demo does. Export the same selection again.
- **Expected outcome:** The second package has a different `package_integrity_hash`; the package content reflects the changed record/chain state and remains self-describing.
- **Notes:** The tampering operation is allowed only as a demo/test simulation. Normal approval or evaluation flows must remain append-only and must not mutate historical audit rows.

### test_audit_log_renders_green_links_for_intact_chain
- **Traces to:** MASTER_SPEC.md §8A items 5–6; TASK_LEDGER.md T25 Done when items 1–2; Architect Brief visual-chain requirement.
- **Input:** Render the audit log page after writing at least three real, untampered audit records and running/using verify-chain status.
- **Expected outcome:** The page shows each record’s truncated `record_hash` and `prev_hash`; visual connectors/arrows are present between records; intact connectors are labelled or styled as green/success/intact; no broken-link warning is shown.
- **Notes:** This is functional HTML acceptance testing, not a pixel-perfect visual test. Assertions may check stable text, CSS classes, ARIA labels, or data attributes added for the visual state.

### test_audit_log_renders_red_broken_link_with_mismatched_hashes_after_tampering
- **Traces to:** MASTER_SPEC.md §5.5 and §8A item 6; TASK_LEDGER.md T25 Done when item 2 and Verify step; Architect Brief “aha moment” requirement.
- **Input:** Render the audit log page after writing at least three records, invoking the existing simulate-tampering action, and re-verifying the chain.
- **Expected outcome:** The page clearly marks the break point in red/error/broken state; it shows the expected previous/current hash relationship and the mismatched hash values side by side; the failing/broken record is identifiable to a non-technical reviewer.
- **Notes:** Use the real T18 tamper/verify workflow. Do not invent a separate hidden test-only broken state if the UI does not use it.

### test_download_audit_package_route_returns_json_file_with_integrity_metadata
- **Traces to:** TASK_LEDGER.md T25 Files/routes and Done when item 3; MASTER_SPEC.md §8A export requirement.
- **Input:** Use the FastAPI test client to request the audit package download route after creating selected audit records.
- **Expected outcome:** Response is successful; response content is JSON; headers indicate a downloadable JSON package; body includes records, chain/hash fields, human-readable explanation, demo labelling, and `package_integrity_hash`.
- **Notes:** This test validates the user-facing download path rather than only the store method.

### test_download_audit_package_route_can_limit_by_correlation_id
- **Traces to:** TASK_LEDGER.md T25 Key note “on the audit page or filtered by correlation_id”; Architect Brief route selection requirement.
- **Input:** Create records for two different `correlation_id` values, then request the package route with one correlation id.
- **Expected outcome:** Returned package includes only records for the requested correlation id and selection metadata states that correlation id. No unrelated records are present.
- **Notes:** If the implementer chooses a different supported selection mode in addition to correlation id, this correlation-id path must still be covered because the Architect Brief explicitly permits and highlights it.

### test_record_page_exposes_package_export_affordance_with_chain_context
- **Traces to:** TASK_LEDGER.md T25 Files `app/web/templates/record.html`; Architect Brief allowed-file objective for extending record export affordance/copy.
- **Input:** Render a single audit record detail page for a real record.
- **Expected outcome:** Page displays the record’s full or truncated `record_hash` and `prev_hash` in the export/chain context and exposes a link or button to download the audit package for the record’s correlation id. Copy must not imply production-grade digital signature.
- **Notes:** This ensures the `record.html` change is acceptance-tested and remains aligned with the audit-package story.

## Coverage checklist
- [ ] Happy path covered: intact audit chain, green visual connectors, package download with records and integrity hash.
- [ ] Error/edge cases covered: simulated tampering/broken chain, mismatched hash display, integrity hash changes after tampering, unrelated records excluded from correlation-id export.
- [ ] Spec non-negotiables verified: real SHA-256 hash-chain fields; demo integrity check labelled honestly; no PKI/signing claims; normal audit operation remains append-only; package hash excludes itself from its own canonical hash.
- [ ] Real dependencies flagged: tests must use the real audit store/hash-chain implementation and FastAPI routes/templates. Do not mock `export_audit_package()`, the audit-store chain fields, or the tamper/verify workflow. OPA/Presidio are not directly in T25 scope unless needed to create records through full scenarios.

## Gaps or ambiguities
- The task allows the package export route to be “on the audit page or filtered by correlation_id,” but the Architect Brief calls out `correlation_id` explicitly. The implementer should provide a correlation-id package download path so tests can verify deterministic selection.
- The exact CSS class names for green/red connectors are not specified. Tests should assert stable semantic markers that the implementer adds, such as visible labels, ARIA labels, or `data-chain-status="intact|broken"`, rather than fragile Tailwind class lists.
- The Verify step is partly manual/visual. Automated tests should cover HTML markers and package JSON; final QA should still perform the manual browser check that the visual connector is immediately understandable.
