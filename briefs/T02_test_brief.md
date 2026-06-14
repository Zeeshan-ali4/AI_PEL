# Test Brief — T02: Pydantic v2 schemas (all five)

## Spec references
- `MASTER_SPEC.md` §2: Evidence is sensor evidence only and must not contain any allow/block/decision/enforcement field.
- `MASTER_SPEC.md` §4: schemas use Pydantic v2.
- `MASTER_SPEC.md` §5.1: canonical `Action` schema.
- `MASTER_SPEC.md` §5.2: canonical `Context` schema.
- `MASTER_SPEC.md` §5.3: canonical `Evidence` schema.
- `MASTER_SPEC.md` §5.4: canonical `Decision` schema, including `threshold_used`.
- `MASTER_SPEC.md` §5.5: canonical `EvidenceRecord` schema, including `record_type` and `references_hash`.
- `MASTER_SPEC.md` §10: schema file layout under `app/schemas/`.
- `MASTER_SPEC.md` §13: no decision field on Evidence and no policy decision in Python schemas.
- `TASK_LEDGER.md` T02: implement all five Pydantic v2 schemas; use enums for closed value sets; add plain-English field docstrings/descriptions; imports and hand-built examples validate; Evidence cannot express a decision; write tests under `tests/T02_schemas/`.

## Target test location
- `tests/T02_schemas/`
- Suggested files grouped by concern: `test_action.py`, `test_context.py`, `test_evidence.py`, `test_decision.py`, `test_audit_record.py`, and `test_validation.py`.

## Test cases

### test_all_schema_modules_import_cleanly
- **Traces to:** `TASK_LEDGER.md` T02 Done when / Verify; `MASTER_SPEC.md` §10.
- **Input:** Import the public schema classes from all five modules: `Action`, `Context`, `Evidence`, `Decision`, and `EvidenceRecord`.
- **Expected outcome:** All imports complete without exceptions and print/return `ok`.
- **Notes:** This is the minimum ledger verification and should be run in the Docker app container so it uses the project dependency set.

### test_valid_action_example_matches_spec_contract
- **Traces to:** `MASTER_SPEC.md` §5.1; `TASK_LEDGER.md` T02 field-name fidelity and closed value sets.
- **Input:** A hand-built payment `Action` example with UUID `action_id` and `correlation_id`, ISO-8601 `timestamp`, `action_type="financial.payment.issue"`, nested `actor`, `tool`, `target_system`, nested `resource`, `parameters` containing an amount/currency/customer reference, `content=None`, `recipient=None`, `environment="demo"`, and `enforcement_mode="full"`.
- **Expected outcome:** The model validates; dumped field names exactly include the §5.1 names and do not rename or omit required fields.
- **Notes:** Also instantiate an email `Action` variant using `action_type="communication.email.send"`, non-null `content`, and non-null `recipient` to prove both closed action types are accepted.

### test_valid_context_example_matches_spec_contract
- **Traces to:** `MASTER_SPEC.md` §5.2; `TASK_LEDGER.md` T02 hand-built examples.
- **Input:** A hand-built `Context` with nested `customer`, `payment_history`, `approval_state`, and `recipient`, including `customer.status="normal"`, boolean fraud/sanctions/vulnerability flags, integer `account_age_days`, numeric `total_30d_gbp`, nullable `last_payment_date`, nullable approver/approval ID, `affects_individual_financial_standing`, `business_hours`, and `context_resolution_ok=True`.
- **Expected outcome:** The model validates and preserves the exact §5.2 field names and nesting.
- **Notes:** Include a second valid variant with `context_resolution_ok=False` to prove the schema can represent the later fail-closed trigger without deciding anything itself.

### test_valid_evidence_example_matches_spec_contract
- **Traces to:** `MASTER_SPEC.md` §2, §5.3, §13; `TASK_LEDGER.md` T02 no decision field on Evidence.
- **Input:** A hand-built email `Evidence` with `evaluated=True`, personal/special-category flags, `sensitivity_level="high"`, one `detected_entities` item with `source="presidio"`, one `evidence_spans` item, `vulnerability_indicators` with `present=True`, `confidence=0.88`, categories such as `health` and `financial_vulnerability`, `source="nuance_stub"`, `overall_confidence=0.88`, `sensor_versions` including `presidio` and `nuance_stub`, and `sensor_error=False`.
- **Expected outcome:** The model validates and dumps only the §5.3 Evidence fields. It contains no outcome/enforcement fields such as `allow`, `block`, `decision`, `approved`, `approval`, `enforcement`, `executed`, `control_id`, `required_approval_role`, or `failure_mode`.
- **Notes:** Include a payment-path valid variant with `evaluated=False` and empty sensor/entity/span data to prove the schema can represent “semantic layer not invoked” without implying a decision.

### test_valid_decision_example_matches_spec_contract
- **Traces to:** `MASTER_SPEC.md` §5.4 and §6; `TASK_LEDGER.md` T02 inclusion of `threshold_used` and decision enums.
- **Input:** A hand-built `Decision` such as `decision="escalate"`, `control_id="COMM-EMAIL-002"`, `triggered_controls=["COMM-EMAIL-002"]`, a plain reason string, `required_approval_role="vulnerable_customer_team"`, non-empty `framework_mappings`, `failure_mode="fail_closed"`, `logging_requirements="enhanced"`, `policy_version`, and `threshold_used=0.75`.
- **Expected outcome:** The model validates and preserves all §5.4 fields including `threshold_used`.
- **Notes:** Also instantiate valid `allow`, `block`, `modify`, `allow_with_logging`, `require_evidence`, and `fail_closed` decision values to prove the full closed set is represented.

### test_valid_evidence_record_example_matches_spec_contract
- **Traces to:** `MASTER_SPEC.md` §5.5; `TASK_LEDGER.md` T02 inclusion of `record_type` and `references_hash`.
- **Input:** A hand-built `EvidenceRecord` containing valid nested `Action`, `Context`, `Evidence`, and `Decision` objects, `id`, `correlation_id`, `enforcement_mode="full"`, `executed=False`, `record_type="action_evaluation"`, `references_hash=None`, nullable human approver/reason, `created_at`, a 64-character hex `record_hash`, and a 64-character hex `prev_hash`.
- **Expected outcome:** The model validates and preserves the exact §5.5 field names and nested model structure.
- **Notes:** Include an `approval_decision` variant whose `references_hash` is a valid SHA-256 hex string and whose `human_approver` and `approval_reason` are populated. The schema should represent append-only approval records but must not implement persistence or hash-chain computation in T02.

### test_closed_value_sets_reject_invalid_values
- **Traces to:** `MASTER_SPEC.md` §5; `TASK_LEDGER.md` T02 enum requirement.
- **Input:** Attempt to validate examples with invalid enum-like values, including an unknown `action_type`, `environment`, `enforcement_mode`, `customer.status`, `sensitivity_level`, detected entity `source`, vulnerability category, vulnerability `source`, `decision`, `failure_mode`, `logging_requirements`, and `record_type`.
- **Expected outcome:** Each invalid value raises a Pydantic validation error rather than being silently accepted or coerced to a default.
- **Notes:** This is an acceptance-level guard for contract drift because downstream tasks depend on these closed sets.

### test_confidence_and_threshold_ranges_reject_out_of_bounds_values
- **Traces to:** `MASTER_SPEC.md` §5.3 and §5.4; `briefs/T02_architect_brief.md` non-negotiables.
- **Input:** Attempt to validate `vulnerability_indicators.confidence`, `overall_confidence`, and `threshold_used` with values below `0` and above `1`.
- **Expected outcome:** Each out-of-range value raises a Pydantic validation error. Boundary values `0` and `1` validate.
- **Notes:** These ranges support later policy threshold behaviour while keeping T02 limited to schema validation only.

### test_sha256_hash_fields_validate_shape
- **Traces to:** `MASTER_SPEC.md` §5.5; `TASK_LEDGER.md` T02 `references_hash` requirement.
- **Input:** Validate `EvidenceRecord` examples with `record_hash`, `prev_hash`, and non-null `references_hash` values that are exactly 64 lowercase hex characters; then attempt values with the wrong length and non-hex characters.
- **Expected outcome:** Valid hash-shaped strings are accepted; malformed hash strings raise Pydantic validation errors.
- **Notes:** T02 should validate the contract shape only. It must not compute hashes or verify the chain; those behaviours belong to T12.

### test_schema_models_do_not_encode_policy_logic
- **Traces to:** `MASTER_SPEC.md` §2 and §13; `TASK_LEDGER.md` T02 reviewer focus.
- **Input:** Instantiate records representing risky inputs, such as Evidence with `sensor_error=True`, Context with `context_resolution_ok=False`, or Evidence with high-confidence special-category indicators.
- **Expected outcome:** Models validate the data shape but do not auto-populate a policy outcome, mutate fields into a `Decision`, or infer `fail_closed`/`escalate`/`block`.
- **Notes:** This protects the core product rule that the policy engine, not schemas or Python model validation, is the judge. Python fail-closed handling is a later OPA/client/pipeline concern, not a T02 schema behaviour.

## Coverage checklist
- [x] Happy path covered: valid hand-built examples for all five schemas, including payment and email variants where relevant.
- [x] Error/edge cases covered: invalid closed-set values, out-of-range confidences/thresholds, malformed SHA-256 hash fields, nullable approval/reference fields, and fail-closed trigger data represented without policy decisions.
- [x] Spec non-negotiables verified: Evidence has no decision/enforcement/approval fields; schemas do not implement policy logic; `threshold_used`, `record_type`, and `references_hash` are present.
- [x] Real dependencies flagged (no mocks where forbidden): no real external dependencies are required for T02 beyond Pydantic v2 in the app container; OPA, Presidio, and Postgres are out of scope for this schema-only task and must not be mocked into these tests.

## Gaps or ambiguities
- None. `TASK_LEDGER.md` T02 now lists `tests/T02_schemas/` as the allowed target location for persistent schema tests.
- The spec requires “docstrings explaining each field in plain English.” Tests can verify that models import and fields expose descriptions/docstrings if implemented through Pydantic `Field(description=...)`, but exact prose quality is partly review-based and should be checked manually by Reviewer/QA.
