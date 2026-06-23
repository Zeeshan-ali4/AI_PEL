# QA Report — T07: Nuance stub + evidence builder

## Verdict
PASS

## Ledger verification
- Command run: `python - <<'PY'
from app.normaliser.normaliser import normalise
from app.semantic.evidence_builder import build_evidence
from scenarios.scenarios import get_raw_tool_call

for number in range(1, 7):
    action = normalise(get_raw_tool_call(number))
    evidence = build_evidence(action)
    print(f"Scenario {number}:")
    print(evidence.model_dump_json(indent=2))
PY`
- Result: passed

## Test suite results
- Command run: `pytest tests/T07_evidence/ -v`
- Total: 11 | Passed: 11 | Failed: 0 | Errors: 0
- Output summary: `collected 11 items`; all T07 evidence-builder, nuance-stub, and sensor-error tests passed. Pytest emitted one third-party spaCy/Click deprecation warning only.

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_nuance_stub.py` | `tests/T07_evidence/test_nuance_stub.py` | ok |
| `test_evidence_builder.py` | `tests/T07_evidence/test_evidence_builder.py` | ok |
| `test_sensor_error_handling.py` | `tests/T07_evidence/test_sensor_error_handling.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| `test_nuance_stub_scenario_4_health_affordability_phrase_returns_fixed_high_confidence` | `test_nuance_stub_scenario_4_health_affordability_phrase_returns_fixed_high_confidence` | `tests/T07_evidence/test_nuance_stub.py` | yes | Uses Scenario 4 fixture body, asserts `present=true`, `confidence == 0.88`, `source == "nuance_stub"`, expected categories, and no decision-like fields. |
| `test_nuance_stub_scenario_5_job_loss_phrase_returns_fixed_uncertain_confidence` | `test_nuance_stub_scenario_5_job_loss_phrase_returns_fixed_uncertain_confidence` | `tests/T07_evidence/test_nuance_stub.py` | yes | Uses Scenario 5 fixture body, asserts `present=true`, `confidence == 0.62`, `financial_vulnerability`, stub source, and no decision-like fields. |
| `test_nuance_stub_scenario_6_name_only_returns_no_vulnerability` | `test_nuance_stub_scenario_6_name_only_returns_no_vulnerability` | `tests/T07_evidence/test_nuance_stub.py` | yes | Uses Scenario 6 fixture body, asserts no vulnerability, confidence below `0.75`, empty categories, stub source, and no decision-like fields. |
| `test_build_evidence_payments_skip_presidio_and_nuance_for_scenarios_1_to_3` | `test_build_evidence_payments_skip_presidio_and_nuance_for_scenarios_1_to_3` | `tests/T07_evidence/test_evidence_builder.py` | yes | Instruments both semantic sensors to fail if called; all payment scenarios return schema-valid unevaluated low-sensitivity Evidence with empty findings, stub version, and `sensor_error=false`. |
| `test_build_evidence_scenario_4_email_combines_real_presidio_with_labelled_stub` | `test_build_evidence_scenario_4_email_combines_real_presidio_with_labelled_stub` | `tests/T07_evidence/test_evidence_builder.py` | yes | Uses real Presidio path and T07 stub; asserts evaluated email Evidence, special-category true, high sensitivity, Presidio-origin findings/spans, `0.88` stub confidence, stub source/version, and `sensor_error=false`. |
| `test_build_evidence_scenario_5_email_preserves_uncertain_vulnerability_confidence` | `test_build_evidence_scenario_5_email_preserves_uncertain_vulnerability_confidence` | `tests/T07_evidence/test_evidence_builder.py` | yes | Asserts Scenario 5 evaluated Evidence preserves `0.62` confidence, `financial_vulnerability`, no special category, stub source/version, and `sensor_error=false`. |
| `test_build_evidence_scenario_6_email_personal_data_only_allows_logging_evidence_shape` | `test_build_evidence_scenario_6_email_personal_data_only_allows_logging_evidence_shape` | `tests/T07_evidence/test_evidence_builder.py` | yes | Asserts Scenario 6 personal-data-only Evidence with medium sensitivity, Presidio-origin findings/spans, no vulnerability, low confidence, empty categories, and `sensor_error=false`. |
| `test_build_evidence_output_has_no_policy_decision_fields` | `test_build_evidence_output_has_no_policy_decision_fields` | `tests/T07_evidence/test_evidence_builder.py` | yes | Parameterised over one payment and one email scenario; recursively checks serialised Evidence for forbidden decision/enforcement/approval fields. |
| `test_build_evidence_presidio_exception_returns_valid_sensor_error_evidence` | `test_build_evidence_presidio_exception_returns_valid_sensor_error_evidence` | `tests/T07_evidence/test_sensor_error_handling.py` | yes | Patches Presidio to raise; builder returns schema-valid evaluated Evidence with `sensor_error=true` and no decision-like fields. |
| `test_build_evidence_nuance_exception_returns_valid_sensor_error_evidence` | `test_build_evidence_nuance_exception_returns_valid_sensor_error_evidence` | `tests/T07_evidence/test_sensor_error_handling.py` | yes | Patches nuance stub to raise; builder returns schema-valid evaluated Evidence with `sensor_error=true`, empty findings, no vulnerability, and no decision-like fields. |

### Extra tests (Implementer-added)
- `test_build_evidence_output_has_no_policy_decision_fields` is parameterised for both Scenario 1 and Scenario 4, providing an extra concrete scenario instance beyond the single-case brief wording.

## Spec non-negotiable checks
- Evidence schema has no decision/enforcement/approval fields: passed — recursive test coverage passed for payment and email Evidence output, and manual ledger output for Scenarios 1–6 contained only Evidence fields.
- No policy logic in Python schemas or components: passed — T07 components emit evidence only (`sensor_error` facts on sensor failure) and no allow/block/escalate/approval/control decision fields were observed.
- Real components are real, stubs are labelled: passed — Scenario 4–6 builder tests used the real Presidio path; the nuance stub output uses `source: "nuance_stub"` and `sensor_versions["nuance_stub"] == "stub-0.1"`.
- Payment scenarios do not invoke semantics: passed — payment test monkeypatches both Presidio and nuance entry points to fail on invocation, and Scenarios 1–3 still returned `evaluated=false` Evidence.
- Fixed scenario confidences preserved: passed — Scenario 4 returned `0.88`, Scenario 5 returned `0.62`, and Scenario 6 returned no vulnerability with confidence below the default high-confidence threshold.
- Sensor exceptions are fail-closed-ready: passed — Presidio and nuance exceptions produced valid Evidence with `sensor_error=true` rather than raising.

## Failures
- None

## Recommendation
Proceed to human approval.
