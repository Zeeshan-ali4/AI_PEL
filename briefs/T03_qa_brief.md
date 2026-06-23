# QA Report — T03: Scenarios + agent simulator + SDK wrapper (PEP)

## Verdict
PASS

## Ledger verification
- Command run: `python -m app.pep.agent_simulator`
- Result: passed — six raw-call representations printed, each preceded by "intercepted before execution"

## Test suite results
- Command run: `pytest tests/T03_scenarios/ -v`
- Total: 11 | Passed: 11 | Failed: 0 | Errors: 0
- Output summary: All 11 tests passed in 0.08s

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_scenario_catalog.py` | `tests/T03_scenarios/test_scenario_catalog.py` | ok |
| `test_agent_simulator.py` | `tests/T03_scenarios/test_agent_simulator.py` | ok |
| `test_sdk_wrapper.py` | `tests/T03_scenarios/test_sdk_wrapper.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| test_catalog_contains_exactly_six_canonical_scenarios | test_catalog_contains_exactly_six_canonical_scenarios | test_scenario_catalog.py | yes | |
| test_payment_scenarios_preserve_fixture_customer_ids_and_amounts | test_payment_scenarios_preserve_fixture_customer_ids_and_amounts | test_scenario_catalog.py | yes | |
| test_payment_scenarios_do_not_include_email_semantic_content | test_payment_scenarios_do_not_include_email_semantic_content | test_scenario_catalog.py | yes | |
| test_email_scenarios_include_required_recipients_and_planted_content | test_email_scenarios_include_required_recipients_and_planted_content | test_scenario_catalog.py | yes | |
| test_expected_outcomes_are_metadata_not_executable_policy | test_expected_outcomes_are_metadata_not_executable_policy | test_scenario_catalog.py | yes | |
| test_agent_simulator_emits_one_raw_tool_call_per_scenario_in_order | test_agent_simulator_emits_one_raw_tool_call_per_scenario_in_order | test_agent_simulator.py | yes | |
| test_agent_simulator_raw_calls_have_later_normalisation_fields | test_agent_simulator_raw_calls_have_later_normalisation_fields | test_agent_simulator.py | yes | |
| test_sdk_wrapper_logs_intercepted_before_execution_for_each_call | test_sdk_wrapper_logs_intercepted_before_execution_for_each_call | test_sdk_wrapper.py | yes | |
| test_sdk_wrapper_forwards_raw_call_unchanged_to_placeholder_pipeline | test_sdk_wrapper_forwards_raw_call_unchanged_to_placeholder_pipeline | test_sdk_wrapper.py | yes | |
| test_sdk_wrapper_does_not_report_business_execution_before_forwarding | test_sdk_wrapper_does_not_report_business_execution_before_forwarding | test_sdk_wrapper.py | yes | |
| test_verify_loop_prints_six_intercepted_raw_calls | test_verify_loop_prints_six_intercepted_raw_calls | test_sdk_wrapper.py | yes | |

### Extra tests (Implementer-added)
- None beyond the brief's 11 cases.

## Spec non-negotiable checks
- Evidence schema has no decision/enforcement/approval fields: not applicable (Evidence not touched in T03)
- No policy logic in Python: passed — expected outcomes are metadata only; raw calls contain no decision fields; wrapper echoes without adding decisions
- Real components real, stubs labelled: passed — `placeholder_policy_pipeline` is clearly documented as temporary T03 placeholder
- Payment scenarios exclude email semantic content: passed — no body/recipient fields in payment raw calls
- Planted phrases match §7 expectations: passed — "can't afford repayments" present in scenario 4; "struggling a bit since losing my job" present in scenario 5; scenario 6 has customer name only

## Failures
- None

## Recommendation
Proceed to human approval.