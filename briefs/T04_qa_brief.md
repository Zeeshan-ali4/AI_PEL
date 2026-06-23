# QA Report — T04: Action normaliser

## Verdict
PASS

## Ledger verification
- Command run: `pytest test_normaliser.py`
- Result: failed — the task ledger names the future T20 aggregate file `test_normaliser.py`, which is not present in this T04 task scope. The closest T04-specific verification target, `pytest tests/T04_normaliser/ -v`, was run and passed.

## Test suite results
- Command run: `pytest tests/T04_normaliser/ -v`
- Total: 10 | Passed: 10 | Failed: 0 | Errors: 0
- Output summary: `collected 10 items`; all tests in `tests/T04_normaliser/test_normaliser_errors.py` and `tests/T04_normaliser/test_normaliser_scenarios.py` passed; final summary `10 passed in 0.22s`.

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_normaliser_scenarios.py` | `tests/T04_normaliser/test_normaliser_scenarios.py` | ok |
| `test_normaliser_errors.py` | `tests/T04_normaliser/test_normaliser_errors.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| `test_all_canonical_scenarios_normalise_to_valid_actions` | `test_all_canonical_scenarios_normalise_to_valid_actions` | `tests/T04_normaliser/test_normaliser_scenarios.py` | yes | Iterates scenarios 1–6, asserts `Action` instance, `environment="demo"`, `enforcement_mode="full"`, and preservation of actor, tool, target system, resource, and parameters. |
| `test_payment_tool_maps_to_financial_payment_issue` | `test_payment_tool_maps_to_financial_payment_issue` | `tests/T04_normaliser/test_normaliser_scenarios.py` | yes | Covers scenarios 1–3, action type `financial.payment.issue`, no email content/recipient, and preservation of payment parameters. |
| `test_email_tool_maps_to_communication_email_send` | `test_email_tool_maps_to_communication_email_send` | `tests/T04_normaliser/test_normaliser_scenarios.py` | yes | Covers scenarios 4–6, action type `communication.email.send`, recipient propagation, content from `parameters["body"]`, and subject/body preservation. |
| `test_normaliser_generates_fresh_uuid4_action_and_correlation_ids` | `test_normaliser_generates_fresh_uuid4_action_and_correlation_ids` | `tests/T04_normaliser/test_normaliser_scenarios.py` | yes | Verifies UUID version 4 identifiers, freshness across repeated normalisation, and no reuse of scenario/customer identifiers. |
| `test_normaliser_sets_current_schema_valid_timestamp` | `test_normaliser_sets_current_schema_valid_timestamp` | `tests/T04_normaliser/test_normaliser_scenarios.py` | yes | Verifies the timestamp is a schema-valid `datetime` within before/after execution bounds. |
| `test_missing_enforcement_mode_defaults_to_shadow` | `test_missing_enforcement_mode_defaults_to_shadow` | `tests/T04_normaliser/test_normaliser_scenarios.py` | yes | Removes `enforcement_mode` from a canonical raw call and confirms the documented default `shadow`. |
| `test_invalid_enforcement_mode_is_rejected_by_schema` | `test_invalid_enforcement_mode_is_rejected_by_schema` | `tests/T04_normaliser/test_normaliser_errors.py` | yes | Supplies `invalid-mode` and confirms Pydantic validation rejects it with an enforcement-mode-specific error. |
| `test_unknown_tool_name_raises_clear_error` | `test_unknown_tool_name_raises_clear_error` | `tests/T04_normaliser/test_normaliser_errors.py` | yes | Supplies `unknown_tool` and confirms `UnsupportedToolError` names the unsupported tool. |
| `test_normaliser_does_not_add_decision_evidence_context_or_audit_fields` | `test_normaliser_does_not_add_decision_evidence_context_or_audit_fields` | `tests/T04_normaliser/test_normaliser_scenarios.py` | yes | Confirms serialised output contains only canonical Action fields and excludes decision, evidence, context, enforcement-execution, and audit fields. |

### Extra tests (Implementer-added)
- `test_missing_tool_name_raises_clear_error` in `tests/T04_normaliser/test_normaliser_errors.py` verifies missing `tool_name` is rejected clearly.

## Spec non-negotiable checks
- Action normalisation only: passed — `app/normaliser/normaliser.py` only maps raw tool calls into `Action` and does not resolve context, build evidence, call policy, enforce decisions, or write audit records.
- OPA/PDP owns decisions: passed — no policy decision fields or decision logic are produced by the normaliser.
- Evidence schema has no decision/enforcement/approval fields: not applicable to T04 file scope; the normaliser test explicitly verifies no evidence/decision/context/audit fields are added to the Action output.
- Real components/stubs labelling: not applicable — T04 has no OPA, Presidio, Postgres, or stub component dependency.

## Failures
- None for the T04 implementation or T04 test suite. The literal ledger command `pytest test_normaliser.py` fails because that file is not part of the T04 scoped test folder and is described by the ledger as a T20 aggregate test.

## Recommendation
Proceed to human approval. Do not mark T04 `DONE` until the human accepts the verification result.
