# QA Report — T02: Pydantic v2 schemas (all five)

## Verdict
PASS

## Ledger verification
- Command run: `python -c "from app.schemas.action import Action; from app.schemas.context import Context; from app.schemas.evidence import Evidence; from app.schemas.decision import Decision; from app.schemas.audit import EvidenceRecord; print('ok')"`
- Result: passed — printed `ok` with no errors or side effects

## Test suite results
- Command run: `pytest tests/T02_schemas/ -v`
- Total: 30 | Passed: 30 | Failed: 0 | Errors: 0
- Output summary: All 30 tests pass in 0.16s. Tests span three files covering examples, validation, and the Evidence contract.

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_schema_examples.py` | `tests/T02_schemas/test_schema_examples.py` | ok |
| `test_schema_validation.py` | `tests/T02_schemas/test_schema_validation.py` | ok |
| `test_evidence_contract.py` | `tests/T02_schemas/test_evidence_contract.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| test_action_accepts_spec_compliant_payment_example | `test_action_accepts_spec_compliant_payment_example` | test_schema_examples.py | yes | Asserts all §5.1 field names present in model_dump |
| test_action_accepts_spec_compliant_email_example | `test_action_accepts_spec_compliant_email_example` | test_schema_examples.py | yes | Verifies content and recipient preserved |
| test_context_accepts_spec_compliant_example | `test_context_accepts_spec_compliant_example` | test_schema_examples.py | yes | Checks status enum and nullable fields |
| test_evidence_accepts_spec_compliant_email_sensor_example | `test_evidence_accepts_spec_compliant_email_sensor_example` | test_schema_examples.py | yes | Verifies presidio source and nuance_stub source |
| test_evidence_accepts_payment_path_not_evaluated_example | `test_evidence_accepts_payment_path_not_evaluated_example` | test_schema_examples.py | yes | Confirms evaluated=False with empty lists |
| test_decision_accepts_spec_compliant_escalation_example | `test_decision_accepts_spec_compliant_escalation_example` | test_schema_examples.py | yes | Asserts threshold_used=0.75 |
| test_evidence_record_accepts_action_evaluation_example | `test_evidence_record_accepts_action_evaluation_example` | test_schema_examples.py | yes | Checks nested model keys and references_hash=None |
| test_evidence_record_accepts_approval_decision_reference_example | `test_evidence_record_accepts_approval_decision_reference_example` | test_schema_examples.py | yes | Verifies approval_decision record_type with references_hash, human_approver, approval_reason |
| test_closed_value_enums_reject_invalid_values | `test_action_closed_value_enums_reject_invalid_values`, `test_context_closed_value_enums_reject_invalid_values`, `test_evidence_closed_value_enums_reject_invalid_values`, `test_decision_closed_value_enums_reject_invalid_values`, `test_record_type_enum_rejects_invalid_values` | test_schema_validation.py | yes | All invalid enum values from the brief are covered via parametrize |
| test_confidence_and_threshold_ranges_are_enforced | `test_confidence_and_threshold_ranges_are_enforced` | test_schema_validation.py | yes | Tests -0.01 and 1.01 for vulnerability confidence, overall_confidence, and threshold_used |
| test_hash_fields_validate_sha256_hex_shape | `test_hash_fields_validate_sha256_hex_shape` | test_schema_validation.py | yes | Tests valid 64-char hex, too short, too long, and non-hex chars |
| test_required_spec_fields_are_not_optional | `test_required_spec_fields_are_not_optional` | test_schema_validation.py | yes | Parametrized across all five models with representative required fields |
| test_evidence_model_has_no_decision_or_enforcement_fields | `test_evidence_model_has_no_decision_or_enforcement_fields` | test_evidence_contract.py | yes | Asserts exact field set matches §5.3 and checks all forbidden substrings |
| test_model_imports_are_clean | `test_model_imports_are_clean` | test_evidence_contract.py | yes | Imports all five models and asserts truthy |

### Extra tests (Implementer-added)
- None beyond the brief — the 30 tests map directly to the 14 brief test cases (some expanded via parametrize).

## Spec non-negotiable checks
- Evidence schema has no decision/enforcement/approval fields: **passed** — field set is exactly the 10 §5.3 fields; forbidden name check passes
- No policy logic in Python schemas: **passed** — schemas contain only Pydantic validation (enums, ranges, regex); no OPA calls, no decision computation
- Field names match §5 verbatim: **passed** — spot-checked action_id, correlation_id, action_type, context_resolution_ok, contains_special_category_data, sensitivity_level, detected_entities, evidence_spans, vulnerability_indicators, overall_confidence, sensor_error, threshold_used, record_type, references_hash, record_hash, prev_hash

## Failures
- None

## Recommendation
Proceed to human approval.