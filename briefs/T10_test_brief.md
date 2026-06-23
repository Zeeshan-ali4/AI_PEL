# Test Brief — T10: OPA real policies + precedence (the heart)

## Spec references
- `MASTER_SPEC.md` §2: model is not the judge; OPA policy is binding; default to human; uncertainty escalates; context/sensor/OPA failures fail closed.
- `MASTER_SPEC.md` §5.4: required `Decision` fields and allowed decision values.
- `MASTER_SPEC.md` §6: complete control library, precedence order, runtime `config.high_confidence_threshold`, framework mappings, and global fail-closed behaviour.
- `MASTER_SPEC.md` §7: six narrative scenarios and exact expected decisions/control IDs.
- `MASTER_SPEC.md` §11: OPA input is `{action, context, evidence, config}` after settings load; payment path has `Evidence(evaluated=false)`.
- `MASTER_SPEC.md` §12: all six scenarios produce exact §7 decisions, payment semantics remain skipped, and lowering threshold to `0.60` flips Scenario 5.
- `TASK_LEDGER.md` T10 acceptance: implement all controls in Rego across `payment.rego`, `email.rego`, and `common.rego`; output full `Decision`; prove scenario decisions, precedence, and threshold behaviour.

## Target test location
- Folder: `tests/T10_policy/`
- Suggested files:
  - `test_policy_scenarios.py` — covers the six scenario acceptance cases and the Scenario 5 threshold flip.
  - `test_policy_precedence.py` — covers precedence regressions, global fail-closed, and Decision metadata completeness.

## Test cases

### test_scenario_1_clean_payment_allows
- **Traces to:** `MASTER_SPEC.md` §6 allow fallback; §7 Scenario 1; `TASK_LEDGER.md` T10 Done when.
- **Input:** Real OPA evaluation through `opa_client` with a canonical payment action for `financial.payment.issue`, amount `80`, clean `CUST-100` context, payment-path evidence where `evaluated=false`, and `config.high_confidence_threshold=0.75`.
- **Expected outcome:** Decision validates against the Pydantic `Decision` schema; `decision == "allow"`; `control_id is None`; `triggered_controls == []`; `required_approval_role is None`; `logging_requirements == "standard"`; `threshold_used == 0.75`.
- **Notes:** This verifies default allow only after no real controls trigger. It must not rely on semantic evidence for payment controls.

### test_scenario_2_large_payment_without_approval_escalates_to_finance_supervisor
- **Traces to:** `MASTER_SPEC.md` §6 `FIN-PAY-002`; §7 Scenario 2; `TASK_LEDGER.md` T10 Verify step.
- **Input:** Real OPA evaluation with payment amount `850`, clean `CUST-100` context, `approval_state.has_approval=false`, payment-path evidence `evaluated=false`, and threshold `0.75`.
- **Expected outcome:** `decision == "escalate"`; `control_id == "FIN-PAY-002"`; `triggered_controls` contains `FIN-PAY-002`; `required_approval_role == "finance_supervisor"`; `framework_mappings` is populated from control metadata; `failure_mode == "fail_closed"`; `threshold_used == 0.75`.
- **Notes:** Confirms risky-but-legitimate payment activity goes to a named human, not `block`.

### test_scenario_3_fraud_flagged_payment_blocks
- **Traces to:** `MASTER_SPEC.md` §6 `FIN-PAY-001`; §7 Scenario 3; prohibited-tier rule.
- **Input:** Real OPA evaluation with payment amount `200`, `CUST-300` context where `customer.fraud_flag=true`, payment-path evidence `evaluated=false`, and threshold `0.75`.
- **Expected outcome:** `decision == "block"`; `control_id == "FIN-PAY-001"`; `triggered_controls` contains `FIN-PAY-001`; `required_approval_role is None`; `framework_mappings` is populated; `threshold_used == 0.75`.
- **Notes:** This is the only scenario expected to block. Do not route prohibited-tier blocks to human escalation in policy output.

### test_scenario_4_external_special_category_email_escalates_to_data_protection
- **Traces to:** `MASTER_SPEC.md` §6 `COMM-EMAIL-001`; §7 Scenario 4; §2 default-to-human.
- **Input:** Real OPA evaluation with `communication.email.send`, external gmail recipient, `recipient.approved_disclosure_basis=false`, evidence containing `contains_special_category_data=true`, `contains_personal_data=true`, `overall_confidence=0.88`, vulnerability indicators present, and threshold `0.75`.
- **Expected outcome:** `decision == "escalate"`; `control_id == "COMM-EMAIL-001"`; `triggered_controls` contains `COMM-EMAIL-001`; `required_approval_role == "data_protection_approver"`; `framework_mappings` is populated; `threshold_used == 0.75`.
- **Notes:** Special-category email escalates; it must not block. If other email controls also trigger, precedence must select this escalation as the top decision/control for Scenario 4.

### test_scenario_5_uncertain_vulnerability_email_escalates_at_default_threshold
- **Traces to:** `MASTER_SPEC.md` §6 `COMM-EMAIL-002`; §7 Scenario 5; §12 threshold acceptance criterion.
- **Input:** Real OPA evaluation with external recipient, evidence where `vulnerability_indicators.present=true`, `overall_confidence=0.62`, no special-category data, personal data may be present, and `config.high_confidence_threshold=0.75`.
- **Expected outcome:** `decision == "escalate"`; `control_id == "COMM-EMAIL-002"`; `triggered_controls` contains `COMM-EMAIL-002`; `required_approval_role == "vulnerable_customer_team"`; `threshold_used == 0.75`.
- **Notes:** This is the core uncertainty-escalates case. The assertion must prove policy reads the threshold from input rather than using a hard-coded value hidden in Rego.

### test_scenario_5_threshold_060_flips_to_allow_with_logging
- **Traces to:** `MASTER_SPEC.md` §6 runtime threshold; §7 Scenario 5; §12 settings threshold flip.
- **Input:** Same action/context/evidence as Scenario 5, but `config.high_confidence_threshold=0.60`.
- **Expected outcome:** `decision == "allow_with_logging"`; `control_id == "COMM-EMAIL-003"` when personal-data logging applies to the assembled Scenario 5 evidence; `triggered_controls` does not include `COMM-EMAIL-002`; `logging_requirements == "enhanced"`; `threshold_used == 0.60`.
- **Notes:** If Scenario 5 evidence has no personal data in the implemented fixture, expected top decision should be `allow`; however, the Architect Brief expects personal-data logging to apply. QA should flag any mismatch for spec/fixture clarification instead of accepting a silent policy change.

### test_scenario_6_partner_email_with_personal_data_allows_with_logging
- **Traces to:** `MASTER_SPEC.md` §6 `COMM-EMAIL-003`; §7 Scenario 6.
- **Input:** Real OPA evaluation with external known partner recipient, no special-category data, no vulnerability indicators, `contains_personal_data=true`, and threshold `0.75`.
- **Expected outcome:** `decision == "allow_with_logging"`; `control_id == "COMM-EMAIL-003"`; `triggered_controls == ["COMM-EMAIL-003"]` or includes it as the selected logging control; `required_approval_role is None`; `logging_requirements == "enhanced"`; `framework_mappings` is populated; `threshold_used == 0.75`.
- **Notes:** Confirms benign personal-data disclosure is allowed but evidenced with enhanced logging.

### test_precedence_fraud_flag_over_large_payment_blocks_not_escalates
- **Traces to:** `MASTER_SPEC.md` §6 precedence order and prohibited tier; `TASK_LEDGER.md` T10 Reviewer focus.
- **Input:** Synthetic payment action with amount over `500`, `approval_state.has_approval=false`, and customer context where `fraud_flag=true` or `sanctions_match=true`.
- **Expected outcome:** `triggered_controls` contains both `FIN-PAY-001` and `FIN-PAY-002`; selected `decision == "block"`; `control_id == "FIN-PAY-001"`; `required_approval_role is None`.
- **Notes:** This regression proves `block` outranks escalation and catches accidental first-match policy behaviour.

### test_fail_closed_when_context_resolution_failed
- **Traces to:** `MASTER_SPEC.md` §2 fail closed; §6 Global fail-closed.
- **Input:** Any otherwise allowable action with `context.context_resolution_ok=false`, evidence `sensor_error=false`, and threshold `0.75`.
- **Expected outcome:** `decision == "fail_closed"`; `control_id` is either `null` or a documented global fail-closed control identifier if implemented; `triggered_controls` includes a fail-closed/global marker if the policy exposes one; `framework_mappings` includes safe-default/robustness mappings; `logging_requirements == "enhanced"`; `failure_mode == "fail_closed"`; `threshold_used == 0.75`.
- **Notes:** This must be decided by OPA for context failures. OPA-unreachable fail-closed remains Python client behaviour from T09 and is not part of this Rego-only task.

### test_fail_closed_when_sensor_error_true
- **Traces to:** `MASTER_SPEC.md` §2 fail closed; §5.3 `sensor_error`; §6 Global fail-closed.
- **Input:** Email action with otherwise low-risk context, evidence `sensor_error=true`, and threshold `0.75`.
- **Expected outcome:** `decision == "fail_closed"`; fail-closed outranks all other potential outcomes; `framework_mappings` includes safe-default/robustness mappings; `logging_requirements == "enhanced"`; `failure_mode == "fail_closed"`; `threshold_used == 0.75`.
- **Notes:** This protects against policies that continue evaluating ambiguous semantic data after a sensor failure.

### test_decision_metadata_is_complete_for_selected_controls
- **Traces to:** `MASTER_SPEC.md` §5.4 Decision schema; §6 framework mappings; `TASK_LEDGER.md` T10 Goal.
- **Input:** One representative result for each selected decision category: allow, block, escalate, allow_with_logging, and fail_closed.
- **Expected outcome:** Every OPA output validates as a `Decision`; `reason` is non-empty; `policy_version` is non-empty; `threshold_used` equals the input threshold; selected control decisions include non-empty `framework_mappings`; escalation decisions include the correct `required_approval_role`; non-escalation decisions have `required_approval_role is None`.
- **Notes:** This verifies the output is audit-ready and that metadata comes from `controls.json` for real controls rather than being omitted by the resolver.

### test_fin_pay_004_proposed_control_respects_metadata_flag_if_present
- **Traces to:** `MASTER_SPEC.md` §6 `FIN-PAY-004`; `TASK_LEDGER.md` T10 key notes about proposed flag in `controls.json`.
- **Input:** A payment action/context where `affects_individual_financial_standing=true` and no higher-precedence controls trigger. Run with the current `controls.json` metadata unchanged.
- **Expected outcome:** If `FIN-PAY-004` is marked active/enabled in metadata, decision escalates with `control_id == "FIN-PAY-004"` and `required_approval_role == "named_decision_maker"`; if metadata marks it inactive/disabled/proposed-only, it must not affect the decision.
- **Notes:** This test should reflect the metadata contract already present from T09. Implementer must not edit `opa/data/controls.json` in T10; if no flag exists and exact behaviour is unclear, flag the ambiguity.

## Coverage checklist
- [ ] Happy path covered: clean payment allows; benign partner email allows with logging.
- [ ] Error/edge cases covered: context failure, sensor failure, and multi-control precedence.
- [ ] Spec non-negotiables verified: OPA decides; only prohibited tier blocks; uncertainty escalates; threshold comes from input; Decision includes audit metadata.
- [ ] Real dependencies flagged: policy tests must evaluate real OPA/Rego via `opa_client` or OPA's real evaluation API/CLI, not mocked policy decisions. Payment-path tests must use `evidence.evaluated=false` and must not require semantic evidence.

## Gaps or ambiguities
- `FIN-PAY-004` is specified as proposed and should be controlled by metadata in `controls.json`, but T10 is not allowed to edit that file. Tests should reflect the existing metadata flag if present; if the metadata lacks an explicit active/inactive flag, the Implementer should stop for clarification rather than inventing a schema outside T10 scope.
- Scenario 5 threshold flip expects `allow_with_logging` at threshold `0.60`. That requires the Scenario 5 evidence to satisfy `COMM-EMAIL-003` personal-data logging after `COMM-EMAIL-002` no longer triggers. If current fixtures/evidence do not mark personal data for Scenario 5, this is a spec/fixture ambiguity to raise rather than silently changing expected outcomes.