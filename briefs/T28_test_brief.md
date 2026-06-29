# Test Brief — T28: Evidence sufficiency checklist (record view)

## Spec references
- MASTER_SPEC.md: §1, §1A, §5, §5.5, §8A item 5, §9, §12
- TASK_LEDGER.md: T28 goal, key notes, done criteria, verify step, and reviewer focus
- Architect brief: `briefs/T28_architect_brief.md`

## Target test location
- Folder: `tests/T28_evidence_sufficiency/`
- Suggested files:
  - `__init__.py` — package marker for the T28 test folder.
  - `test_sufficiency.py` — covers pure checklist evaluation for representative record shapes and edge cases.
  - `test_record_view_sufficiency.py` — covers record-route/template rendering of the checklist and required illustrative/non-certification framing.

## Test cases

### test_allow_record_marks_core_evidence_met_and_human_oversight_not_applicable
- **Traces to:** MASTER_SPEC.md §5.5, §8A item 5; TASK_LEDGER.md T28 done criteria 1–2 and key note on human oversight handling.
- **Input:** A representative `action_evaluation` record for an `allow` decision with `executed` present, `enforcement_mode` present, non-empty `decision.reason`, valid `record_hash`, valid `prev_hash`, and no required approval role.
- **Expected outcome:** The pure sufficiency function returns at least five items. Items for interception/execution evidence, decision rationale, and chain position are `met`; human oversight is `not-applicable`; no item is hardcoded from a scenario number.
- **Notes:** This is the baseline happy path for records that do not require human review.

### test_allow_with_logging_record_accepts_framework_mapping_as_evidence
- **Traces to:** MASTER_SPEC.md §6 COMM-EMAIL-003, §7 scenario 6, §8A item 5; TASK_LEDGER.md T28 criteria around framework mappings.
- **Input:** A representative `action_evaluation` record for `allow_with_logging` with `decision.framework_mappings` populated and `logging_requirements="enhanced"`.
- **Expected outcome:** The checklist marks the framework/control mapping item as `met` and does not require a linked approval record.
- **Notes:** This verifies the checklist can evaluate logging decisions from existing Decision fields.

### test_control_mapping_not_applicable_when_allow_has_no_triggered_control
- **Traces to:** MASTER_SPEC.md §7 scenario 1; TASK_LEDGER.md T28 key note requiring correct not-applicable handling when no mapping is required by record shape.
- **Input:** A clean payment `allow` action-evaluation record whose Decision has `control_id=None`, empty `triggered_controls`, and empty `framework_mappings`.
- **Expected outcome:** The framework/control mapping checklist item is `not-applicable`, not `missing`.
- **Notes:** Do not penalise a clean allow record for having no triggered control.

### test_pending_escalation_marks_human_oversight_pending_or_missing
- **Traces to:** MASTER_SPEC.md §6 FIN-PAY-002 / COMM-EMAIL-001 / COMM-EMAIL-002, §5.5 append-only approvals; TASK_LEDGER.md T28 done criterion 4.
- **Input:** An `action_evaluation` record with `decision.decision="escalate"`, a non-empty `required_approval_role`, `executed=false`, and no linked `approval_decision` record supplied to the sufficiency function.
- **Expected outcome:** Human oversight item status is `pending` or `missing` with explanatory text indicating approval is required but not yet evidenced. Other field-backed items such as rationale and chain position are evaluated independently from their actual fields.
- **Notes:** The PM/BA acceptance requirement allows either `pending` or `missing`; the UI copy should make the pending state clear to a risk reviewer.

### test_approved_escalation_marks_human_oversight_met_when_linked_approval_supplied
- **Traces to:** MASTER_SPEC.md §5.5 append-only approvals; MASTER_SPEC.md §8A item 4; TASK_LEDGER.md T28 done criterion 4.
- **Input:** The same escalated `action_evaluation` record plus a linked `approval_decision` record with the same `correlation_id`, `references_hash` equal to the original record's `record_hash`, non-empty `human_approver`, non-empty `approval_reason`, and resulting `executed` state.
- **Expected outcome:** Human oversight item is `met` and the explanation cites the linked approval evidence (approver/reason/reference), while the original action-evaluation record is not mutated.
- **Notes:** The test should assert linkage by existing fields (`correlation_id` + `references_hash`), not by scenario number.

### test_approval_decision_record_uses_approval_specific_evidence
- **Traces to:** MASTER_SPEC.md §5.5 approval_decision fields; TASK_LEDGER.md T28 key note to handle record types correctly.
- **Input:** An `approval_decision` record containing `references_hash`, `human_approver`, `approval_reason`, `executed`, `record_hash`, and `prev_hash`.
- **Expected outcome:** Checklist items relevant to the approval record are `met` based on approval-specific fields; action-only criteria are either phrased appropriately or `not-applicable`, rather than incorrectly reported as missing.
- **Notes:** Approval records must not be penalised for not being a fresh action evaluation.

### test_fail_closed_record_reports_available_evidence_without_treating_failure_as_certification_failure
- **Traces to:** MASTER_SPEC.md §2 fail closed, §5.4 failure mode, §11 pipeline order; TASK_LEDGER.md T28 architect non-negotiables.
- **Input:** An `action_evaluation` record whose Decision has `decision="fail_closed"`, `failure_mode="fail_closed"`, non-empty `reason`, and chain hashes present.
- **Expected outcome:** Checklist marks decision rationale and chain position from actual fields, marks human oversight as `not-applicable` unless the record itself requires it, and does not treat fail-closed as an automatic checklist failure solely because a component failed.
- **Notes:** Missing fields should still be reported honestly if omitted; the special requirement is not to equate fail-closed with regulatory insufficiency by default.

### test_incomplete_record_marks_missing_fields_from_actual_absence
- **Traces to:** MASTER_SPEC.md §5.5 required evidence record fields; TASK_LEDGER.md T28 done criterion 2.
- **Input:** A deliberately incomplete record-like object or dict missing one or more sufficiency inputs, such as empty `decision.reason`, missing `record_hash`, or missing `enforcement_mode`.
- **Expected outcome:** Only checklist items whose backing fields are absent/empty are `missing`; unrelated items retain their correct `met` or `not-applicable` status.
- **Notes:** This verifies field-derived evaluation and guards against all-green hardcoding.

### test_sufficiency_function_has_no_database_or_policy_side_effects
- **Traces to:** TASK_LEDGER.md T28 reviewer focus; Architect brief non-negotiables for `app/audit/sufficiency.py` purity.
- **Input:** Representative records passed directly to the sufficiency function without an app, database session, OPA, semantic layer, or scenario runner.
- **Expected outcome:** The function returns deterministic checklist items and does not require or create database state, does not mutate input records, and does not call OPA or semantic components.
- **Notes:** This can be asserted by using plain objects/dicts and comparing inputs before/after. Do not mock real dependencies because no dependency should be called.

### test_record_view_renders_checklist_and_illustrative_non_certification_label
- **Traces to:** MASTER_SPEC.md §8A item 5, §12 stub/illustrative labelling; TASK_LEDGER.md T28 done criteria 1 and 3.
- **Input:** Render the record view for a representative stored record through the FastAPI route/test client or the existing route rendering helper.
- **Expected outcome:** The HTML contains the sufficiency checklist section, at least five checklist rows/items, and explicit copy equivalent to "Illustrative sufficiency check, not a compliance certification." The existing T26 regulator-questions panel remains present.
- **Notes:** This test may use the repository's existing web test fixtures/patterns. If a real database is already required for record routes, use the real test database path established by prior tasks rather than replacing persistence with mocks.

### test_record_view_updates_human_oversight_after_approval
- **Traces to:** MASTER_SPEC.md §5.5 append-only approvals; TASK_LEDGER.md T28 verify step and done criterion 4.
- **Input:** Create or obtain an escalated action-evaluation record, render its record page before any linked approval, then append a linked `approval_decision` record and render the original record page again.
- **Expected outcome:** Before approval, the human oversight checklist item is pending/missing. After approval, re-viewing the original record shows human oversight as `met`, based on the linked approval record. The original record's stored fields are unchanged.
- **Notes:** Use real audit-store append behaviour if the existing route test pattern supports it. Do not implement this by changing the original action-evaluation record.

## Coverage checklist
- [x] Happy path covered: clean allow/logging records and normal record-view rendering.
- [x] Error/edge cases covered: pending escalation, fail-closed, incomplete/missing fields, approval-decision record type.
- [x] Spec non-negotiables verified: field-derived checklist only, append-only approval linkage, no Evidence schema changes, no scenario special-casing, illustrative/non-certification label.
- [x] Real dependencies flagged: record-route tests should use the real app/audit route patterns and real persistence where existing tests require it; the pure sufficiency function must not call database, OPA, Presidio, or scenario code.

## Gaps or ambiguities
- The task allows the human-oversight status for an unapproved escalation to render as either `pending` or `missing`. The Implementer should choose one clear label and use it consistently in both function output and UI copy.
- The exact `SufficiencyItem` shape is intentionally left to the Implementer, but tests should assert stable semantic fields such as item key/label, status, and explanatory text so the route and template can consume it consistently.
