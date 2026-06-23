# Test Brief — T05: Context resolver + fixtures

## Spec references
- MASTER_SPEC.md: §3 Context resolver position in the policy pipeline; §5.2 exact Context schema; §6 controls that consume context; §7 six narrative scenarios and expected policy-driving context; §11 resolver failure must set `context_resolution_ok=false`.
- TASK_LEDGER.md: T05 goal, key notes, done-when, verify step, and reviewer focus for fixture-backed context resolution.
- briefs/T05_architect_brief.md: fixture expectations, allowed files, non-negotiables, and explicit forced-failure requirement.

## Target test location
- Folder: `tests/T05_context/`
- Suggested files:
  - `test_context_resolution.py` — covers scenario-by-scenario context outputs and schema-valid Context objects.
  - `test_context_failure.py` — covers forced context-resolution failure and missing/unknown fixture behaviour.
  - `test_fixture_labels.py` — covers visible demo-fixture labelling / no real connector expectation where exposed by the fixture module.

## Test cases

### test_resolves_clean_low_value_payment_context_for_scenario_1
- **Traces to:** MASTER_SPEC.md §5.2 and §7 scenario 1; TASK_LEDGER T05 done-when.
- **Input:** Normalise `get_raw_tool_call(1)` and pass the resulting Action to `app.context.resolver.resolve()`.
- **Expected outcome:** Returned object is an `app.schemas.context.Context`; `customer.id == "CUST-100"`; `customer.status == "normal"`; `customer.fraud_flag is False`; `customer.sanctions_match is False`; `payment_history.count_30d` is below the FIN-PAY-003 threshold of 3; `approval_state.has_approval is False`; `affects_individual_financial_standing is True`; `business_hours` is deterministic; `context_resolution_ok is True`.
- **Notes:** This verifies the clean payment fixture remains capable of later producing the §7 `allow` result without policy logic in Python.

### test_resolves_high_value_payment_without_approval_for_scenario_2
- **Traces to:** MASTER_SPEC.md §5.2, §6 FIN-PAY-002, and §7 scenario 2.
- **Input:** Normalise `get_raw_tool_call(2)` and resolve context.
- **Expected outcome:** `customer.id == "CUST-100"`; `customer.fraud_flag is False`; `customer.sanctions_match is False`; `customer.status == "normal"`; `approval_state.has_approval is False`; `approval_state.approver is None`; `approval_state.approval_id is None`; `context_resolution_ok is True`; the payment amount remains on `action.parameters["amount_gbp"] == 850` and is not duplicated into Context.
- **Notes:** The resolver must expose approval absence for later FIN-PAY-002 evaluation while avoiding policy decisions.

### test_resolves_fraud_flag_payment_for_scenario_3
- **Traces to:** MASTER_SPEC.md §6 FIN-PAY-001 and §7 scenario 3; TASK_LEDGER T05 verify spot-check.
- **Input:** Normalise `get_raw_tool_call(3)` and resolve context.
- **Expected outcome:** `customer.id == "CUST-300"`; `customer.fraud_flag is True`; `customer.status` remains a valid schema value; `context_resolution_ok is True`; `affects_individual_financial_standing is True`.
- **Notes:** This is the critical context fixture for the later prohibited-tier block. The test must not assert any Decision object or decision string from the resolver.

### test_resolves_external_gmail_without_disclosure_basis_for_scenario_4
- **Traces to:** MASTER_SPEC.md §5.2, §6 COMM-EMAIL-001, and §7 scenario 4; TASK_LEDGER T05 reviewer focus.
- **Input:** Normalise `get_raw_tool_call(4)` and resolve context.
- **Expected outcome:** `recipient.is_external is True`; `recipient.domain == "gmail.com"`; `recipient.approved_disclosure_basis is False`; `affects_individual_financial_standing is False`; `context_resolution_ok is True`; customer fixture validates for `CUST-200`.
- **Notes:** This test covers recipient-domain extraction and disclosure-basis propagation for an external Gmail recipient.

### test_resolves_external_adviser_disclosure_basis_for_scenario_5
- **Traces to:** MASTER_SPEC.md §5.2, §6 COMM-EMAIL-002, and §7 scenario 5.
- **Input:** Normalise `get_raw_tool_call(5)` and resolve context.
- **Expected outcome:** `recipient.is_external is True`; `recipient.domain == "example.org"`; `recipient.approved_disclosure_basis is True`, matching the raw scenario input; `affects_individual_financial_standing is False`; `context_resolution_ok is True`; customer fixture validates for `CUST-250`.
- **Notes:** Scenario 5's later escalation depends on semantic uncertainty, not missing disclosure basis, so context must preserve the approved basis as true.

### test_resolves_known_partner_recipient_for_scenario_6
- **Traces to:** MASTER_SPEC.md §5.2, §6 COMM-EMAIL-003, and §7 scenario 6.
- **Input:** Normalise `get_raw_tool_call(6)` and resolve context.
- **Expected outcome:** `recipient.is_external is True`; `recipient.domain == "trusted-partner.example"`; `recipient.approved_disclosure_basis is True`; `customer.id == "CUST-100"`; `affects_individual_financial_standing is False`; `context_resolution_ok is True`.
- **Notes:** This confirms a known partner is still external for policy purposes, but has an approved disclosure basis.

### test_all_scenarios_return_schema_valid_context_objects
- **Traces to:** MASTER_SPEC.md §5.2; TASK_LEDGER T05 done-when and verify.
- **Input:** Loop scenarios 1 through 6, normalise each raw tool call, and resolve context.
- **Expected outcome:** Every result is an instance of the canonical `Context` Pydantic model and `context.model_dump()` includes exactly the schema fields from §5.2: `customer`, `payment_history`, `approval_state`, `recipient`, `affects_individual_financial_standing`, `business_hours`, and `context_resolution_ok`.
- **Notes:** This acceptance test guards against schema drift and missing nested context values.

### test_forced_resolution_failure_returns_valid_fail_closed_context
- **Traces to:** MASTER_SPEC.md §5.2 and §11; TASK_LEDGER T05 key note to force `context_resolution_ok=false`; Architect Brief forced-failure non-negotiable.
- **Input:** Use the explicit failure mechanism provided by the resolver, such as a documented `force_failure=True` argument or equivalent explicit sentinel, with a normalised valid Action.
- **Expected outcome:** Returned object is a valid `Context`; `context_resolution_ok is False`; all nested schema objects are present with safe placeholder values; no exception is required for the expected forced-failure path.
- **Notes:** This path exists for later fail-closed policy demonstration. It must be explicit and deterministic, not dependent on corrupting real fixture data.

### test_unknown_customer_or_missing_required_fixture_returns_failed_context
- **Traces to:** MASTER_SPEC.md §11 fail-closed context failure; Architect Brief non-negotiable on unknown or missing required fixture records.
- **Input:** Build or copy a valid normalised Action and set `action.resource.id` / relevant customer id to an unknown fixture key such as `CUST-DOES-NOT-EXIST`, then resolve.
- **Expected outcome:** Returned object is a valid `Context`; `context_resolution_ok is False`; `customer.id` reflects the requested unknown id or a documented safe placeholder; required nested objects validate; no successful fabricated clean context is returned.
- **Notes:** The resolver should fail closed at the context level rather than silently inventing enterprise facts.

### test_no_policy_decision_fields_or_decision_logic_in_context_output
- **Traces to:** MASTER_SPEC.md §2 and §5.2; AGENTS.md non-negotiable product rules.
- **Input:** Resolve any successful payment scenario and any successful email scenario.
- **Expected outcome:** `context.model_dump()` contains no keys named `decision`, `allow`, `block`, `escalate`, `control_id`, `approval_role`, or similar enforcement outputs; the resolver does not return a tuple containing policy results.
- **Notes:** Context is policy input only. This test protects the product rule that the policy engine, not Python context resolution, is the judge.

### test_fixtures_are_labelled_as_demo_enterprise_stand_ins
- **Traces to:** MASTER_SPEC.md §1 deliberately not in scope and T05 key notes; Architect Brief fixture-labelling non-negotiable.
- **Input:** Inspect public fixture metadata/constants/docstrings exposed by `app.context.fixtures`.
- **Expected outcome:** The fixture module makes clear that data is demo fixture data / stand-ins for IAM, CRM, fraud, sanctions, payment-history, approval, and disclosure-basis systems. Tests should assert a concrete exposed label or metadata value if the implementation provides one.
- **Notes:** Do not require real network or enterprise connectors; for T05, tests should fail if implementation appears to require external systems.

## Coverage checklist
- [ ] Happy path covered for all six narrative scenarios.
- [ ] Error/edge cases covered for forced failure and unknown/missing fixtures.
- [ ] Spec non-negotiables verified: exact Context schema, context-only evidence, no Python decision logic, payment financial-standing flag true, email financial-standing flag false, fixtures labelled as demo stand-ins.
- [ ] Real dependencies flagged: T05 must not use real enterprise connectors or network calls; fixture-backed resolution is intentional. No OPA, Presidio, Postgres, enforcement, audit, or UI dependencies are required for this task.

## Gaps or ambiguities
- `MASTER_SPEC.md` does not prescribe exact `payment_history`, `account_age_days`, `business_hours`, or placeholder values for failed contexts. Tests should assert policy-relevant bounds and deterministic behaviour rather than arbitrary numeric literals, unless the Implementer documents specific fixture constants.
- The forced-failure API shape is intentionally left to implementation, but it must be explicit, deterministic, and tested. The Implementer should document the chosen mechanism in `app/context/resolver.py` so QA can call it directly.
