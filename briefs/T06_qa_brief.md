# QA Report — T06: Presidio sensor (REAL)

## Verdict
PASS

## Ledger verification
- Command run: `python - <<'PY' ... PY` (script imported the scenario catalog, ran `PresidioSensor` on Scenarios 4, 5, and 6, and printed detected entities plus spans)
- Result: passed
- Output summary:
  - Scenario 4: detected `PERSON` span `(0,19)` text `Customer Alex Green`; `PHONE_NUMBER` span `(35,47)` text `485 777 3456`; `UK_NHS_NUMBER` span `(35,47)` text `485 777 3456`; `DATE_TIME` span `(43,47)` text `3456`; `HEALTH_INFORMATION` span `(68,84)` text `cancer diagnosis`.
  - Scenario 5: detected `PERSON` span `(0,10)` text `Pat Morgan`.
  - Scenario 6: detected `PERSON` span `(15,27)` text `Jamie Taylor`.
- Environment note: the first direct local run failed because `presidio_analyzer` was not installed in the current interpreter, and `docker compose run --rm app ...` could not be used because `docker` is not installed in this environment. I installed the declared `requirements.txt` dependencies and the `en_core_web_sm` spaCy model into the local interpreter, then re-ran verification successfully.

## Test suite results
- Command run: `pytest tests/T06_presidio/ -v`
- Total: 7 | Passed: 7 | Failed: 0 | Errors: 0
- Output summary:
  - `tests/T06_presidio/test_presidio_sensor_contract.py::test_custom_nhs_number_recognizer_is_registered_with_presidio PASSED`
  - `tests/T06_presidio/test_presidio_sensor_contract.py::test_output_contract_contains_raw_evidence_only PASSED`
  - `tests/T06_presidio/test_presidio_sensor_contract.py::test_sensor_handles_empty_or_whitespace_body_without_policy_decision PASSED`
  - `tests/T06_presidio/test_presidio_sensor_scenarios.py::test_scenario_4_detects_nhs_number_and_health_entities_with_spans PASSED`
  - `tests/T06_presidio/test_presidio_sensor_scenarios.py::test_scenario_5_returns_raw_presidio_findings_without_policy_judgement PASSED`
  - `tests/T06_presidio/test_presidio_sensor_scenarios.py::test_scenario_6_detects_customer_name_only_no_health_or_nhs_entity PASSED`
  - `tests/T06_presidio/test_presidio_sensor_scenarios.py::test_all_returned_spans_are_valid_for_original_text PASSED`
  - Summary line: `7 passed, 1 warning in 9.66s`

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_presidio_sensor_scenarios.py` | `tests/T06_presidio/test_presidio_sensor_scenarios.py` | ok |
| `test_presidio_sensor_contract.py` | `tests/T06_presidio/test_presidio_sensor_contract.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| `test_scenario_4_detects_nhs_number_and_health_entities_with_spans` | `test_scenario_4_detects_nhs_number_and_health_entities_with_spans` | `tests/T06_presidio/test_presidio_sensor_scenarios.py` | yes | Uses Scenario 4 fixture body, asserts exact NHS-number text/span, `HEALTH_INFORMATION`, no decision keys, `source == "presidio"`, bounded scores, and valid spans. |
| `test_scenario_5_returns_raw_presidio_findings_without_policy_judgement` | `test_scenario_5_returns_raw_presidio_findings_without_policy_judgement` | `tests/T06_presidio/test_presidio_sensor_scenarios.py` | yes | Uses Scenario 5 fixture body, asserts raw entity list, no decision/enforcement/approval/allow/block keys, and valid spans. |
| `test_scenario_6_detects_customer_name_only_no_health_or_nhs_entity` | `test_scenario_6_detects_customer_name_only_no_health_or_nhs_entity` | `tests/T06_presidio/test_presidio_sensor_scenarios.py` | yes | Uses Scenario 6 fixture body, asserts `Jamie Taylor` is detected, and verifies no NHS, health, vulnerability, decision, or escalation output. |
| `test_custom_nhs_number_recognizer_is_registered_with_presidio` | `test_custom_nhs_number_recognizer_is_registered_with_presidio` | `tests/T06_presidio/test_presidio_sensor_contract.py` | yes | Uses minimal NHS-number string, asserts one `UK_NHS_NUMBER` entity with exact span text, Presidio source, and bounded score. |
| `test_output_contract_contains_raw_evidence_only` | `test_output_contract_contains_raw_evidence_only` | `tests/T06_presidio/test_presidio_sensor_contract.py` | yes | Recursively checks forbidden decision/enforcement/evidence-classification keys are absent and verifies only raw evidence keys are returned. |
| `test_all_returned_spans_are_valid_for_original_text` | `test_all_returned_spans_are_valid_for_original_text` | `tests/T06_presidio/test_presidio_sensor_scenarios.py` | yes | Runs Scenarios 4, 5, and 6 through the sensor and validates integer offsets against original source text. |
| `test_sensor_handles_empty_or_whitespace_body_without_policy_decision` | `test_sensor_handles_empty_or_whitespace_body_without_policy_decision` | `tests/T06_presidio/test_presidio_sensor_contract.py` | yes | Checks empty string, whitespace-only string, and `None` return empty raw collections without forbidden decision/fail-closed fields. |

### Extra tests (Implementer-added)
- None beyond the PM/BA brief cases. The implementer added helper assertions (`_assert_valid_spans`, `_walk_keys`) inside the requested files, but no extra pytest test functions.

## Spec non-negotiable checks
- Evidence/schema decision leakage: passed — T06 sensor returns raw `entities`, `detected_entities`, `evidence_spans`, and `sensor_versions`; tests recursively reject decision, enforcement, approval, fail-closed, and T07 final evidence-classification fields.
- No policy logic in Python sensor: passed — sensor wraps Presidio findings and custom recognizers only; it does not return allow/block/escalate/control/policy outcomes.
- Real Presidio component: passed — implementation imports and constructs `presidio_analyzer.AnalyzerEngine` with a spaCy NLP engine, and tests exercise it after installing the declared real dependency and `en_core_web_sm` model.
- Custom NHS recognizer: passed — `UK_NHS_NUMBER` is registered with Presidio's analyzer registry and detected through the sensor output with `source == "presidio"`.
- Span fidelity: passed — tests assert returned offsets slice back to non-empty original source text for Scenarios 4, 5, and 6.
- Stub labelling: not applicable — T06 introduces no stub; the later nuance stub is T07 scope.

## Failures
- None after installing the declared dependencies and spaCy model locally.

## Recommendation
Proceed to human approval.
