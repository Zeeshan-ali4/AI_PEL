# Test Brief — T04: Action normaliser

## Spec references
- MASTER_SPEC.md: §1 item 2 (normalise proposed actions into one governance schema); §3 (Action normaliser position after SDK wrapper/PEP); §5.1 (canonical Action schema); §7 (six canonical scenario inputs and action categories); §10 (file layout); §11 step 2 (pipeline normalisation order).
- TASK_LEDGER.md: T04 goal, key notes, done criteria, verify guidance, and reviewer focus: convert every raw tool call into a canonical `Action`, map tool names to `financial.payment.issue` or `communication.email.send`, generate `action_id` and `correlation_id` as UUIDs, set `timestamp`, set `environment="demo"`, carry `enforcement_mode`, reject unknown tools clearly, and ensure all six scenarios normalise to valid Action objects.
- Architect brief: T04 allowed files and non-negotiables, especially that the normaliser must not introduce context lookup, semantic evidence, policy decisions, enforcement, or audit writes.

## Target test location
- Folder: `tests/T04_normaliser/`
- Suggested files:
  - `test_normaliser_scenarios.py` — covers successful normalisation for all six canonical scenarios, canonical field preservation, UUID/timestamp generation, and default/carry-through enforcement mode behaviour.
  - `test_normaliser_errors.py` — covers clear failure for unsupported/unknown tool names and schema validation of invalid enforcement modes.

## Test cases

### test_all_canonical_scenarios_normalise_to_valid_actions
- **Traces to:** MASTER_SPEC.md §5.1; MASTER_SPEC.md §7; TASK_LEDGER.md T04 “Done when”.
- **Input:** Iterate over the six raw tool calls returned by the T03 scenario source, e.g. `scenarios.scenarios.get_raw_tool_call(1)` through `get_raw_tool_call(6)`, and pass each into the T04 normaliser.
- **Expected outcome:**
  - Each result is an instance of the canonical `Action` schema (or validates successfully into `Action` if the normaliser returns a serialisable dict).
  - `environment` is exactly `demo` for every action.
  - `enforcement_mode` is carried through from each raw call; the current canonical scenarios should all produce `full`.
  - `actor`, `tool`, `target_system`, `resource`, and `parameters` preserve the corresponding raw-call values without adding decision, context, evidence, enforcement, or audit fields.
- **Notes:** This is the main acceptance test proving all current scenario simulator outputs can enter the governance schema.

### test_payment_tool_maps_to_financial_payment_issue
- **Traces to:** MASTER_SPEC.md §5.1; TASK_LEDGER.md T04 key notes; Architect brief supported action types.
- **Input:** Raw tool calls for scenarios 1, 2, and 3 (`tool_name="issue_payment"`).
- **Expected outcome:** Each normalised action has `action_type == "financial.payment.issue"`, `content is None`, `recipient is None`, and the payment details remain in `parameters` including `amount_gbp`, `currency`, `approval_present`, and `payment_reason`.
- **Notes:** Payment scenarios must not gain email content or semantic-layer concerns during normalisation.

### test_email_tool_maps_to_communication_email_send
- **Traces to:** MASTER_SPEC.md §5.1; MASTER_SPEC.md §7 scenarios 4–6; TASK_LEDGER.md T04 key notes.
- **Input:** Raw tool calls for scenarios 4, 5, and 6 (`tool_name="send_email"`).
- **Expected outcome:** Each normalised action has `action_type == "communication.email.send"`, `recipient` equal to the raw recipient, and `content` equal to the raw email body in `parameters["body"]`. Email metadata such as `subject` remains available in `parameters`.
- **Notes:** This test ensures the downstream semantic layer will receive the unstructured body through the canonical Action `content` field, while still preserving the original action-specific parameters.

### test_normaliser_generates_fresh_uuid4_action_and_correlation_ids
- **Traces to:** MASTER_SPEC.md §5.1; TASK_LEDGER.md T04 key notes; Architect brief non-negotiables.
- **Input:** Normalise the same raw scenario call twice.
- **Expected outcome:**
  - Both `action_id` values are valid UUID version 4 values.
  - Both `correlation_id` values are valid UUID version 4 values.
  - The second normalisation produces different `action_id` and `correlation_id` values from the first; the normaliser must not reuse `scenario_id`, `customer_id`, or any raw-call identifier as either UUID.
- **Notes:** Correlation IDs are critical because downstream audit records link on them.

### test_normaliser_sets_current_schema_valid_timestamp
- **Traces to:** MASTER_SPEC.md §5.1; TASK_LEDGER.md T04 key notes.
- **Input:** Record a time immediately before and after normalising a canonical scenario call.
- **Expected outcome:** The action `timestamp` validates as a datetime in the `Action` schema and falls between the recorded before/after bounds, allowing a small tolerance for execution time if necessary.
- **Notes:** The assertion should avoid brittle formatting checks and rely on schema-valid datetime behaviour.

### test_missing_enforcement_mode_defaults_to_shadow
- **Traces to:** MASTER_SPEC.md §5.1 enforcement-mode enum; Architect brief defaulting instruction.
- **Input:** A valid raw tool call copied from a canonical scenario with the `enforcement_mode` key removed.
- **Expected outcome:** The normalised action has `enforcement_mode == "shadow"` and remains schema-valid.
- **Notes:** The Architect brief allows `shadow` as the narrow demo-safe default when the raw call has no established default. This default should be visible in code/tests so it is not accidental.

### test_invalid_enforcement_mode_is_rejected_by_schema
- **Traces to:** MASTER_SPEC.md §5.1 allowed enforcement modes (`shadow`, `soft`, `full`); TASK_LEDGER.md T04 “carry enforcement_mode through”.
- **Input:** A valid raw tool call copied from a canonical scenario with `enforcement_mode="invalid-mode"`.
- **Expected outcome:** Normalisation fails with a schema validation error or another clear explicit error; it must not silently coerce the mode or default to a safe value when an invalid value was supplied.
- **Notes:** This is an edge case guarding the closed enum contract from §5.1.

### test_unknown_tool_name_raises_clear_error
- **Traces to:** TASK_LEDGER.md T04 key notes; Architect brief non-negotiables.
- **Input:** A valid raw tool call copied from a canonical scenario with `tool_name="unknown_tool"` and no supported mapping.
- **Expected outcome:** The normaliser raises a clear explicit exception, and the error message identifies the unknown/unsupported tool name. It must not silently default to either canonical `action_type`.
- **Notes:** This is the key negative acceptance test requested by the task.

### test_normaliser_does_not_add_decision_evidence_context_or_audit_fields
- **Traces to:** MASTER_SPEC.md §2 non-negotiables; MASTER_SPEC.md §3 pipeline separation; Architect brief non-negotiables.
- **Input:** Any successfully normalised canonical raw tool call.
- **Expected outcome:** The serialised action output contains only canonical Action fields from §5.1. It does not contain policy-decision fields such as `decision`, `control_id`, `triggered_controls`, evidence fields such as `contains_personal_data`, context fields such as `customer`/`payment_history`, enforcement execution fields such as `executed`, or audit fields such as `record_hash`/`prev_hash`.
- **Notes:** This verifies the normaliser remains a schema translation step only and does not leak later pipeline responsibilities into T04.

## Coverage checklist
- [x] Happy path covered: all six canonical scenarios normalise successfully.
- [x] Error/edge cases covered: unknown tool, invalid enforcement mode, missing enforcement mode default.
- [x] Spec non-negotiables verified: exact Action schema output, UUID generation, environment fixed to `demo`, no decision/evidence/context/audit leakage.
- [x] Real dependencies flagged (no mocks where forbidden): T04 has no OPA, Presidio, or Postgres dependency. Tests should use the real T03 scenario data and real Pydantic `Action` schema, not hand-rolled schema mocks.

## Gaps or ambiguities
- None blocking. The raw T03 scenarios already include `enforcement_mode="full"`; the Architect brief clarifies that if the field is missing, T04 should default to `shadow` and document that behaviour in code/tests.