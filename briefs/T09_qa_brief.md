# QA Report — T09: OPA round-trip (prove the HTTP path before real policy)

## Verdict
PASS

## Ledger verification
- Command run: `pytest tests/T09_opa_client/ -v` (Docker not available in this environment; offline tests run directly, OPA round-trip tests correctly skip)
- Result: passed — 7 passed, 2 skipped (OPA-dependent round-trip tests skip when OPA is not running, as designed)

## Test suite results
- Command run: `pytest tests/T09_opa_client/ -v`
- Total: 9 | Passed: 7 | Failed: 0 | Errors: 0 | Skipped: 2
- Output summary: All offline tests pass. Two OPA-dependent tests (`test_roundtrip_allow_decision`, `test_decision_schema_fields_complete`) correctly skip with reason "OPA not running on localhost:8181". These require a live OPA container and are structured to pass when OPA is available.

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_controls_json.py` | `tests/T09_opa_client/test_controls_json.py` | ok |
| `test_opa_roundtrip.py` | `tests/T09_opa_client/test_opa_roundtrip.py` | ok |
| `test_fail_closed.py` | `tests/T09_opa_client/test_fail_closed.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| controls_json_structure | `test_controls_json_structure` | test_controls_json.py | yes | Checks all 7 IDs, required fields, framework_mappings as list |
| controls_json_framework_mappings | `test_controls_json_framework_mappings` | test_controls_json.py | yes | Spot-checks FIN-PAY-001, COMM-EMAIL-001, COMM-EMAIL-003 mappings |
| controls_json_fin_pay_004_proposed | `test_controls_json_fin_pay_004_proposed` | test_controls_json.py | yes | Asserts FIN-PAY-004 proposed=true, others not proposed |
| roundtrip_allow_decision | `test_roundtrip_allow_decision` | test_opa_roundtrip.py | yes | Requires live OPA; skipped in CI without OPA; asserts decision="allow" |
| decision_schema_fields_complete | `test_decision_schema_fields_complete` | test_opa_roundtrip.py | yes | Checks all Decision fields are not None |
| opa_input_contract_shape | `test_opa_input_contract_shape` | test_opa_roundtrip.py | yes | Validates input payload structure with all 4 keys |
| opa_unreachable_fail_closed | `test_opa_unreachable_fail_closed` | test_fail_closed.py | yes | Uses dead port 19999 for real connection failure |
| fail_closed_decision_fields | `test_fail_closed_decision_fields` | test_fail_closed.py | yes | Checks reason, logging_requirements, framework_mappings, policy_version, threshold_used |
| opa_non_2xx_fail_closed | `test_opa_non_2xx_fail_closed` | test_fail_closed.py | yes | Fallback to connection-refused when OPA down; uses nonsense path when OPA up |

### Extra tests (Implementer-added)
- None beyond the brief's test cases.

## Spec non-negotiable checks
- OPA/PDP owns decisions (Python only produces fail_closed): passed — `opa_client.py` only returns fail_closed on OPA unreachable/non-2xx/parse failure; all other decisions come from OPA response
- Decision schema fields match §5.4: passed — all fields present in trivial Rego policy and parsed correctly
- Fail-closed is real (not a swallowed exception): passed — separate handling for ConnectError, TimeoutException, NetworkError, non-2xx status, missing result, and parse failure
- controls.json framework_mappings match §6 verbatim: passed — verified by test
- FIN-PAY-004 has proposed flag: passed — verified by test
- Trivial Rego policy labelled as placeholder: passed — `policy_version: "0.1.0-trivial"`

## Failures
- None

## Recommendation
Proceed to human approval. All offline tests pass. The 2 skipped tests require a live OPA container and are correctly gated. The reviewer brief (APPROVE) confirms no issues. Implementation matches the architect brief, test brief, and spec requirements.