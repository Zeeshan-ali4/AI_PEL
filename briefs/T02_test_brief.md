# Test Brief — T02: Pydantic v2 schemas (all five)

## Spec references
- `MASTER_SPEC.md` §2: Evidence is sensor output only and must not contain allow/block/decision/enforcement fields; policy decisions come from OPA, not Python.
- `MASTER_SPEC.md` §4: schemas use Pydantic v2.
- `MASTER_SPEC.md` §5.1: canonical `Action` schema and exact field names.
- `MASTER_SPEC.md` §5.2: canonical `Context` schema and exact field names.
- `MASTER_SPEC.md` §5.3: canonical `Evidence` schema, confidence ranges, sensor fields, and no decision field.
- `MASTER_SPEC.md` §5.4: canonical `Decision` schema, closed decision values, `failure_mode`, `logging_requirements`, and `threshold_used`.
- `MASTER_SPEC.md` §5.5: canonical `EvidenceRecord` schema, `record_type`, `references_hash`, approval-decision linkage fields, and hash fields.
- `MASTER_SPEC.md` §10: canonical file layout for `app/schemas/` and `tests/T02_schemas/`.
- `TASK_LEDGER.md` T02 acceptance criteria: all five models import cleanly and validate a hand-built example each; field names match spec verbatim; closed value sets use enums; `Evidence` has no allow/block/decision field.
- `TASK_LEDGER.md` T02 Verify: import every schema module in Docker and/or run a tiny pytest that instantiates each.

## Target test location
- Folder: `tests/T02_schemas/`
- Suggested files:
  - `test_schema_examples.py` — covers valid hand-built examples for Action, Context, Evidence, Decision, and EvidenceRecord.
  - `test_schema_validation.py` — covers enum rejection, numeric range validation, hash-shape validation, and required-field validation.
  - `test_evidence_contract.py` — covers the Evidence non-negotiable that evidence cannot express policy decisions, enforcement state, or human approval state.

## Test cases

### test_action_accepts_spec_compliant_payment_example
- **Traces to:** `MASTER_SPEC.md` §5.1; `TASK_LEDGER.md` T02 Done when.
- **Input:** Instantiate `Action` with UUID `action_id` and `correlation_id`, ISO timestamp or `datetime`, `action_type="financial.payment.issue"`, actor object, payment tool metadata, resource object, payment parameters, `content=None`, `recipient=None`, `environment="demo"`, and `enforcement_mode="full"`.
- **Expected outcome:** Model validates successfully; `model_dump()` contains every §5.1 top-level field with the exact names `action_id`, `correlation_id`, `timestamp`, `action_type`, `actor`, `tool`, `target_system`, `resource`, `parameters`, `content`, `recipient`, `environment`, and `enforcement_mode`.
- **Notes:** This is an acceptance test for the canonical payment action contract only; do not test normaliser behaviour in T02.

### test_action_accepts_spec_compliant_email_example
- **Traces to:** `MASTER_SPEC.md` §5.1; `MASTER_SPEC.md` §7 email scenario shape.
- **Input:** Instantiate `Action` with `action_type="communication.email.send"`, email tool metadata, `content` containing a short email body, `recipient="external@example.com"`, `environment="demo"`, and `enforcement_mode="shadow"`.
- **Expected outcome:** Model validates successfully and preserves the email `content` and `recipient` values exactly.
- **Notes:** This ensures both closed action types are accepted for downstream scenario work.

### test_context_accepts_spec_compliant_example
- **Traces to:** `MASTER_SPEC.md` §5.2; `TASK_LEDGER.md` T02 Done when.
- **Input:** Instantiate `Context` with nested `customer`, `payment_history`, `approval_state`, and `recipient` objects plus `affects_individual_financial_standing`, `business_hours`, and `context_resolution_ok`.
- **Expected outcome:** Model validates successfully; `customer.status` accepts `normal`, `flagged`, or `blocked`; nullable fields such as `payment_history.last_payment_date`, `approval_state.approver`, `approval_state.approval_id`, and `recipient.domain` accept `None` where specified.
- **Notes:** This test should not resolve fixtures or infer context; it only verifies the schema contract.

### test_evidence_accepts_spec_compliant_email_sensor_example
- **Traces to:** `MASTER_SPEC.md` §5.3; `MASTER_SPEC.md` §2; `TASK_LEDGER.md` T02 reviewer focus.
- **Input:** Instantiate `Evidence` with `evaluated=True`, personal/special category booleans, `sensitivity_level="high"`, at least one detected entity from `source="presidio"`, at least one evidence span, vulnerability indicators using `source="nuance_stub"`, `overall_confidence=0.88`, sensor versions including `presidio` and `nuance_stub="stub-0.1"`, and `sensor_error=False`.
- **Expected outcome:** Model validates successfully and serialises the nested lists/objects with the exact field names from §5.3.
- **Notes:** Presidio itself is not run in T02; real sensor verification belongs to T06. This test should use hand-built representative sensor output.

### test_evidence_accepts_payment_path_not_evaluated_example
- **Traces to:** `MASTER_SPEC.md` §3 semantic layer payment skip; `MASTER_SPEC.md` §5.3; `MASTER_SPEC.md` §12 payment scenarios never invoke semantic layer.
- **Input:** Instantiate `Evidence` for a payment path with `evaluated=False`, no detected entities, no evidence spans, no vulnerability categories, `overall_confidence=0`, and `sensor_error=False`.
- **Expected outcome:** Model validates successfully and preserves `evaluated=False`.
- **Notes:** This verifies the schema can represent the later payment-path contract without invoking semantic components.

### test_decision_accepts_spec_compliant_escalation_example
- **Traces to:** `MASTER_SPEC.md` §5.4; `MASTER_SPEC.md` §6; `TASK_LEDGER.md` T02 goal including `threshold_used`.
- **Input:** Instantiate `Decision` with `decision="escalate"`, `control_id="FIN-PAY-002"`, `triggered_controls=["FIN-PAY-002"]`, a reason string, `required_approval_role="finance_supervisor"`, framework mappings, `failure_mode="fail_closed"`, `logging_requirements="enhanced"`, `policy_version`, and `threshold_used=0.75`.
- **Expected outcome:** Model validates successfully; `threshold_used` is present and equals `0.75`.
- **Notes:** This test does not assert OPA policy logic; it only asserts the PDP output schema can carry later policy output.

### test_evidence_record_accepts_action_evaluation_example
- **Traces to:** `MASTER_SPEC.md` §5.5; `TASK_LEDGER.md` T02 goal including `record_type`, `references_hash`, and nested models.
- **Input:** Instantiate `EvidenceRecord` with an integer `id`, UUID `correlation_id`, nested valid `Action`, `Context`, `Evidence`, and `Decision` instances, `enforcement_mode="full"`, `executed=False`, `record_type="action_evaluation"`, `references_hash=None`, no human approver/reason, `created_at`, a 64-character lowercase SHA-256 hex `record_hash`, and genesis `prev_hash` of 64 zeroes.
- **Expected outcome:** Model validates successfully; nested model data serialises under exact keys `action`, `context_used`, `evidence`, and `decision`; `references_hash` accepts `None` for action-evaluation records.
- **Notes:** Hash computation and append-only storage are out of scope until T12.

### test_evidence_record_accepts_approval_decision_reference_example
- **Traces to:** `MASTER_SPEC.md` §5.5 append-only approvals.
- **Input:** Instantiate `EvidenceRecord` with `record_type="approval_decision"`, a non-null 64-character SHA-256 `references_hash`, non-null `human_approver`, non-null `approval_reason`, and the same required nested schema fields.
- **Expected outcome:** Model validates successfully and preserves `references_hash`, `human_approver`, and `approval_reason`.
- **Notes:** The test should not assert database insertion or mutation behaviour in T02.

### test_closed_value_enums_reject_invalid_values
- **Traces to:** `MASTER_SPEC.md` §5.1-§5.5; `TASK_LEDGER.md` T02 Key notes.
- **Input:** Try to instantiate representative models with invalid closed-set values, including `action_type="unknown.tool"`, `environment="qa"`, `enforcement_mode="monitor"`, `customer.status="vip"`, `sensitivity_level="critical"`, detected entity `source="manual"`, vulnerability category `"unknown"`, vulnerability `source="llm"`, `decision="approve"`, `failure_mode="ignore"`, `logging_requirements="verbose"`, and `record_type="mutation"`.
- **Expected outcome:** Each invalid value raises `pydantic.ValidationError`.
- **Notes:** It is acceptable to split these assertions into parametrized tests inside `test_schema_validation.py`.

### test_confidence_and_threshold_ranges_are_enforced
- **Traces to:** `MASTER_SPEC.md` §5.3 and §5.4; Architect Brief numeric range non-negotiable.
- **Input:** Try to instantiate `Evidence` with `vulnerability_indicators.confidence` below 0 or above 1, `Evidence.overall_confidence` below 0 or above 1, and `Decision.threshold_used` below 0 or above 1.
- **Expected outcome:** Values inside `[0, 1]` validate; values outside `[0, 1]` raise `pydantic.ValidationError`.
- **Notes:** This verifies schema-shape validation only, not policy threshold decisions.

### test_hash_fields_validate_sha256_hex_shape
- **Traces to:** `MASTER_SPEC.md` §5.5 hash-chain schema.
- **Input:** Instantiate `EvidenceRecord` using valid 64-character lowercase SHA-256 hex strings for `record_hash`, `prev_hash`, and non-null `references_hash`; then try invalid hash strings that are too short, too long, or contain non-hex characters.
- **Expected outcome:** Valid hashes are accepted; invalid hashes raise `pydantic.ValidationError`.
- **Notes:** This test is limited to field shape. Chain verification belongs to T12.

### test_required_spec_fields_are_not_optional
- **Traces to:** `MASTER_SPEC.md` §5.1-§5.5 exact contracts.
- **Input:** For each of the five top-level models, omit one required representative field: `Action.action_id`, `Context.customer`, `Evidence.evaluated`, `Decision.decision`, and `EvidenceRecord.record_hash`.
- **Expected outcome:** Each omission raises `pydantic.ValidationError`.
- **Notes:** Avoid asserting implementation-internal defaults. Requiredness should follow the spec JSON shapes unless the spec explicitly marks a field nullable.

### test_evidence_model_has_no_decision_or_enforcement_fields
- **Traces to:** `MASTER_SPEC.md` §2; `MASTER_SPEC.md` §5.3; `TASK_LEDGER.md` golden rule #4 and T02 Done when.
- **Input:** Inspect `Evidence.model_fields`.
- **Expected outcome:** The field set is exactly the §5.3 Evidence top-level fields, and contains none of the forbidden names or substrings: `allow`, `block`, `decision`, `approval`, `approved`, `enforcement`, `executed`, `control_id`, `triggered_controls`, `required_approval_role`, `failure_mode`, or `policy_version`.
- **Notes:** This is the key non-negotiable acceptance test for T02: Evidence is evidence only.

### test_model_imports_are_clean
- **Traces to:** `TASK_LEDGER.md` T02 Verify.
- **Input:** Import `Action`, `Context`, `Evidence`, `Decision`, and `EvidenceRecord` from their respective modules.
- **Expected outcome:** Imports complete without side effects or exceptions.
- **Notes:** The Implementer may include this as a simple pytest or rely on the example tests importing all models. QA should still run the ledger Docker import command.

## Coverage checklist
- [x] Happy path covered: valid hand-built examples for all five canonical schemas.
- [x] Error/edge cases covered: invalid enums, out-of-range confidence/threshold values, invalid hash strings, and missing required fields.
- [x] Spec non-negotiables verified: Evidence has no decision/enforcement/approval fields; `threshold_used`, `record_type`, and `references_hash` are covered.
- [x] Real dependencies flagged (no mocks where forbidden): T02 has no real OPA, Presidio, Postgres, or hash-chain dependency to exercise. Tests must not mock these dependencies because they are not in scope; real dependency tests begin in later tasks.

## Gaps or ambiguities
- The spec does not state whether SHA-256 hex strings must be lowercase only or case-insensitive. For consistent audit hashing later, this brief expects lowercase 64-character hex strings; if the Implementer believes uppercase should be accepted, they should request clarification before broadening the contract.
- The spec marks some fields as nullable but does not define defaults. This brief expects required fields to be explicitly provided, with nullable fields accepting `None` only when supplied. If defaults are added for convenience, they should not hide required contract fields from downstream callers.
