# QA Report — T10: OPA real policies + precedence (the heart)

## Verdict
PASS

## Ledger verification
- Command run: `opa eval` via pytest (OPA CLI v0.70.0 installed; all six scenarios evaluated against real Rego policies + controls.json)
- Result: passed — all six scenarios produce §7-correct decisions; threshold flip at 0.60 confirmed for Scenario 5.

## Test suite results
- Command run: `pytest tests/T10_policy/ -v`
- Total: 12 | Passed: 12 | Failed: 0 | Errors: 0
- Output summary: All 12 tests passed in 0.49s. Tests use real OPA CLI evaluation against the three Rego policy files and `controls.json`.

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_policy_scenarios.py` | `tests/T10_policy/test_policy_scenarios.py` | ok |
| `test_policy_precedence.py` | `tests/T10_policy/test_policy_precedence.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| test_scenario_1_clean_payment_allows | test_scenario_1_clean_payment_allows | test_policy_scenarios.py | yes | Asserts allow, no controls, standard logging, threshold 0.75 |
| test_scenario_2_large_payment_without_approval_escalates_to_finance_supervisor | test_scenario_2_large_payment_without_approval_escalates_to_finance_supervisor | test_policy_scenarios.py | yes | Asserts escalate, FIN-PAY-002, finance_supervisor, framework_mappings populated |
| test_scenario_3_fraud_flagged_payment_blocks | test_scenario_3_fraud_flagged_payment_blocks | test_policy_scenarios.py | yes | Asserts block, FIN-PAY-001, no approval role |
| test_scenario_4_external_special_category_email_escalates_to_data_protection | test_scenario_4_external_special_category_email_escalates_to_data_protection | test_policy_scenarios.py | yes | Asserts escalate, COMM-EMAIL-001, data_protection_approver |
| test_scenario_5_uncertain_vulnerability_email_escalates_at_default_threshold | test_scenario_5_uncertain_vulnerability_email_escalates_at_default_threshold | test_policy_scenarios.py | yes | Asserts escalate, COMM-EMAIL-002, vulnerable_customer_team, threshold_used 0.75 |
| test_scenario_5_threshold_060_flips_to_allow_with_logging | test_scenario_5_threshold_060_flips_to_allow_with_logging | test_policy_scenarios.py | yes | Asserts allow_with_logging, COMM-EMAIL-003, COMM-EMAIL-002 not triggered, enhanced logging, threshold_used 0.60 |
| test_scenario_6_partner_email_with_personal_data_allows_with_logging | test_scenario_6_partner_email_with_personal_data_allows_with_logging | test_policy_scenarios.py | yes | Asserts allow_with_logging, COMM-EMAIL-003, enhanced logging, framework_mappings populated |
| test_precedence_fraud_flag_over_large_payment_blocks_not_escalates | test_precedence_fraud_flag_over_large_payment_blocks_not_escalates | test_policy_precedence.py | yes | Both FIN-PAY-001 and FIN-PAY-002 triggered; block wins via precedence |
| test_fail_closed_when_context_resolution_failed | test_fail_closed_when_context_resolution_failed | test_policy_precedence.py | yes | fail_closed, GLOBAL-FAIL-CLOSED in triggered_controls, enhanced logging, framework_mappings present |
| test_fail_closed_when_sensor_error_true | test_fail_closed_when_sensor_error_true | test_policy_precedence.py | yes | fail_closed on sensor_error=true, enhanced logging |
| test_decision_metadata_is_complete_for_selected_controls | test_decision_metadata_is_complete_for_selected_controls | test_policy_precedence.py | yes | Covers allow/block/escalate/allow_with_logging/fail_closed; validates reason, policy_version, threshold_used, framework_mappings, approval_role correctness |
| test_fin_pay_004_proposed_control_respects_metadata_flag_if_present | test_fin_pay_004_proposed_control_respects_metadata_flag_if_present | test_policy_precedence.py | yes | FIN-PAY-004 not triggered due to `proposed: true` in controls.json; decision remains allow |

### Extra tests (Implementer-added)
- None beyond brief-specified cases.

## Spec non-negotiable checks
- OPA/Rego is the sole decision-maker (no decision logic in Python): passed — all three .rego files contain the control triggers, precedence resolver, and decision assembly; Python test code only invokes OPA CLI.
- Evidence has no decision/allow/block field: passed — Evidence schema untouched by T10; policy reads `evidence.contains_special_category_data`, `evidence.vulnerability_indicators`, etc. as evidence only.
- `block` reserved for prohibited tier only (FIN-PAY-001): passed — only FIN-PAY-001 has `decision: "block"` in controls.json; all other controls escalate.
- Threshold read from input, not hardcoded: passed — `common.rego` line 12: `object.get(input.config, "high_confidence_threshold", 0.75)` with 0.75 as fallback only; Scenario 5 threshold flip test proves it.
- Precedence correct (fail_closed > block > escalate > ... > allow): passed — `precedence_rank` in common.rego matches spec §6 exactly; precedence regression test confirms fraud+large-payment resolves to block.
- Framework mappings sourced from controls.json: passed — `control_mappings(id) := data.controls[id].framework_mappings` in common.rego.
- FIN-PAY-004 proposed flag respected: passed — `control_enabled` checks `not data.controls[id].proposed == true`; controls.json has `"proposed": true` for FIN-PAY-004.
- Fail-closed on context_resolution_ok=false and sensor_error=true: passed — both tested and passing.

## Failures
- None

## Recommendation
Proceed to human approval. All 12 tests pass against real OPA evaluation. Policy logic, precedence, threshold behaviour, fail-closed paths, and metadata completeness all verified against MASTER_SPEC.md §6 and §7.