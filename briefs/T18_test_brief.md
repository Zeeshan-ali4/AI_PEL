# Test Brief — T18: Audit log + verify chain + simulate tampering (headline moment)

## Spec references
- MASTER_SPEC.md: §1 points 7–8 (tamper-evident evidence store and risk-visible controls), §1A pillar 2 (evidential reliability and integrity), §5.5 Evidence Record and hash rule, §8A item 6 (Audit log + integrity), §10 canonical file layout, §12 acceptance criteria for chain verification and tamper detection.
- TASK_LEDGER.md: T18 goal, dependencies, allowed files, Done when, Verify step, and Reviewer focus; T12 real audit-store `verify_chain()` and `simulate_tampering()` behaviour; T14 shared assurance UI conventions.
- Architect brief: `briefs/T18_architect_brief.md` non-negotiables for real store usage, visually unambiguous green/red integrity states, chronological record fields, demo-only tamper labelling, and reset/reseed affordance guidance.

## Target test location
- Folder: `tests/T18_audit_ui/`
- Suggested files:
  - `test_audit_log_page.py` — covers chronological audit list rendering, required assurance fields, empty/minimal states, record-view links, and reset/reseed affordance copy.
  - `test_audit_integrity_actions.py` — covers Verify Chain intact state, Simulate Tampering broken state, exact failing record naming, and demo-only/real-store behaviour.

## Test cases

### test_audit_log_lists_records_chronologically_with_assurance_fields
- **Traces to:** MASTER_SPEC.md §5.5, §8A item 6; TASK_LEDGER T18 Goal/Done when; Architect brief chronological audit list requirements.
- **Input:** Seed or create at least three real audit records through the existing audit store/pipeline test fixture with distinct `created_at` values and mixed `record_type` values where feasible (`action_evaluation` and, if already available in fixtures, `approval_decision`). Issue `GET` to the T18 audit log route.
- **Expected outcome:** Response is HTTP 200 and renders records in chronological order. For each rendered record, the page exposes record id, created time, record type, correlation id, decision, executed state, `record_hash`, and `prev_hash`. Hashes should be visibly present as SHA-256 hex strings or safely shortened with enough identifying text while preserving full values in accessible/title/detail text if the UI truncates them.
- **Notes:** This is a functional UI test. It must exercise the real route and the real audit store. Do not assert against private helper implementation details.

### test_audit_log_includes_record_detail_links_when_records_exist
- **Traces to:** MASTER_SPEC.md §8A items 5–6; Architect brief chronological list field/link requirement.
- **Input:** Create one or more real audit records, then request the audit log page.
- **Expected outcome:** Each listed record includes a link to the existing single-record view/export surface where available. The link target should identify the same record/hash shown in the list and should not invent a new record-view route outside existing T17 behaviour.
- **Notes:** If the implemented route uses record id or record hash as the link key, assert the chosen key matches the rendered row and resolves consistently with existing T17 routes.

### test_audit_log_empty_or_minimal_state_is_board_readable
- **Traces to:** MASTER_SPEC.md §8A item 6 assurance UI tone; TASK_LEDGER T18 Done when; Architect brief reset/reseed guidance.
- **Input:** Start with a clean test database containing no audit records, then issue `GET` to the audit log route.
- **Expected outcome:** Response is HTTP 200 and shows calm explanatory copy rather than an error/traceback. The page still presents a clear Verify Chain affordance. It should explain that no records are currently present or guide the user to run demo scenarios to populate audit records.
- **Notes:** This ensures the audit page is safe to open before a demo run. If the verifier treats an empty chain as intact with count `0`, that is acceptable only if the UI clearly says zero records were verified.

### test_verify_chain_shows_green_intact_status_and_count
- **Traces to:** MASTER_SPEC.md §5.5 hash rule, §8A item 6; TASK_LEDGER T18 Done when/Verify step; Architect brief Verify step.
- **Input:** Create at least two untampered audit records through the real audit store. Submit the Verify Chain action through the web route/form, or request the audit page state after verification if verification is GET-driven.
- **Expected outcome:** The response/redirect target is HTTP 200 after following redirects and shows an unmistakable intact/green success state. It includes the exact number of records verified, matching the count in the seeded store. It must not merely display a hard-coded success message.
- **Notes:** Tests must use the real T12 `verify_chain()` behaviour through the route path. Mocks/fakes of the hash-chain verifier are not acceptable for this acceptance test.

### test_simulate_tampering_breaks_chain_and_names_exact_failing_record
- **Traces to:** MASTER_SPEC.md §5.5 hash rule, §8A item 6; §12 acceptance criterion; TASK_LEDGER T18 Done when/Verify step; Architect brief non-negotiables.
- **Input:** Create at least three audit records through the real audit store. Trigger the Simulate Tampering action through the T18 web route/form, then follow the response to the audit page or integrity result.
- **Expected outcome:** The UI shows an unmistakable broken/red failure state and names the exact failing record/row returned by the real verifier after tampering. The named record must correspond to the record altered by the demo-only tamper helper, not just a generic “chain failed” message.
- **Notes:** This is the headline acceptance test. It must call the route that uses the real T12 `simulate_tampering()` helper; do not mutate the database directly in the test except through fixture setup. The assertion should cover both failure status and identifying text for the broken record.

### test_simulate_tampering_action_is_labelled_demo_only
- **Traces to:** MASTER_SPEC.md §1 honesty principle, §8A item 6; Architect brief non-negotiables.
- **Input:** Request the audit log page with at least one audit record present.
- **Expected outcome:** The Simulate Tampering affordance is visibly labelled as demo-only/deliberate tampering and does not look like a normal edit/update/delete operation. The route/form copy should make clear this intentionally alters a stored row to prove tamper evidence.
- **Notes:** This guards the non-negotiable that normal audit operation remains append-only and that the in-place alteration path is explicitly a demo helper.

### test_no_normal_update_or_delete_audit_controls_are_exposed
- **Traces to:** MASTER_SPEC.md §5.5 append-only approvals and hash rule; AGENTS.md non-negotiable product rules; TASK_LEDGER T18 Reviewer focus.
- **Input:** Request the audit log page and inspect rendered forms/links/buttons.
- **Expected outcome:** The page exposes no generic edit, update, or delete controls for audit records. The only control that implies alteration is the clearly labelled demo-only Simulate Tampering affordance.
- **Notes:** This is a black-box UI assertion, not a source-code inspection. It helps ensure the audit table is still presented as append-only in normal operation.

### test_reset_or_reseed_affordance_is_present_without_new_subsystem_assumption
- **Traces to:** TASK_LEDGER T18 Done when; Architect brief reset demo data guidance.
- **Input:** Request the audit log page before and/or after simulated tampering.
- **Expected outcome:** The page offers a “reset demo data” or reseed/recovery affordance. If no existing reset helper/route is available, the page must show clear copy explaining how to reseed/reset using the existing demo workflow rather than silently inventing a new data-management subsystem.
- **Notes:** The test should assert the user is not stranded after the tamper demo. It should not require a new reset implementation unless the implementer finds an existing allowed helper/route to reuse.

## Coverage checklist
- [ ] Happy path covered: audit log renders real records chronologically and Verify Chain reports green/intact with exact count.
- [ ] Error/edge cases covered: empty/minimal dataset is readable; tampered chain fails red and names the exact broken record; post-tamper recovery/reset guidance is present.
- [ ] Spec non-negotiables verified: real hash chain, append-only normal presentation, demo-only tamper labelling, exact failing-record visibility, no decision/schema/policy drift.
- [ ] Real dependencies flagged (no mocks where forbidden): tests must exercise real T12 audit-store `verify_chain()` and `simulate_tampering()` through T18 routes; no fake verifier in tests or web layer.

## Gaps or ambiguities
- The exact route paths and HTTP methods for the audit page, Verify Chain action, and Simulate Tampering action are not prescribed by the spec/ledger. Tests should discover/assert the paths chosen by the implementer from rendered links/forms where practical, while still requiring the user-visible behaviours above.
- The spec asks to “offer a reset demo data affordance” but does not define a canonical reset helper. If no existing helper is available inside the allowed route/store surface, acceptance should be satisfied by clear reseed/reset guidance copy rather than a new data-management subsystem.
