# Test Brief — T20: Test suite

## Spec references
- MASTER_SPEC.md: §2 principles; §5 canonical schemas; §6 control library and precedence; §7 six narrative scenarios; §10 canonical file layout; §11 pipeline order; §12 acceptance criteria; §13 scope fences.
- TASK_LEDGER.md: T20 acceptance criteria — create four regression test files for normaliser mapping, real Presidio detection, policy decisions for all six scenarios, and audit chain integrity/tamper detection; `test_policy_decisions` must guard against silent drift from MASTER_SPEC §7.
- Architect brief: `briefs/T20_architect_brief.md` allowed files and non-negotiables.

## Target test location
- Folder: `tests/`
- Suggested files:
  - `test_normaliser.py` — covers canonical Action mapping for all six raw scenario tool calls.
  - `test_presidio_sensor.py` — covers real Presidio detection/evidence classification on planted email bodies.
  - `test_policy_decisions.py` — covers the complete MASTER_SPEC §7 decision table, control IDs, approval roles, threshold behaviour, and payment semantic skip where exposed by the path under test.
  - `test_audit_chain.py` — covers append-only hash-chain integrity and exact tamper detection.

## Test cases

### test_normaliser_maps_all_scenarios_to_canonical_actions
- **Traces to:** MASTER_SPEC §5.1, §7, §10; TASK_LEDGER T20 normaliser mapping goal.
- **Input:** Each of the six scenario definitions/raw tool calls from the existing scenario source.
- **Expected outcome:** Normalising each scenario returns a valid canonical Action with populated `action_id`, `correlation_id`, ISO-like timestamp, actor, tool, target system, resource, environment, and propagated/default enforcement mode. Scenario action types must be:
  - #1, #2, #3: `financial.payment.issue`
  - #4, #5, #6: `communication.email.send`
- **Notes:** The test should assert schema-conformant field presence and values, not implementation internals. Do not add decision or enforcement data to Action.

### test_normaliser_preserves_payment_fields_and_skips_email_fields_for_payments
- **Traces to:** MASTER_SPEC §5.1, §7, §11; TASK_LEDGER T20 normaliser mapping goal.
- **Input:** Payment scenarios #1 (£80), #2 (£850), and #3 (£200).
- **Expected outcome:** Each canonical Action preserves the payment amount/currency/customer/resource identifiers needed by downstream context and policy. Payment Actions must not require email `content` or `recipient` values to be policy-evaluable.
- **Notes:** This protects the payment path from accidentally becoming dependent on unstructured semantic content.

### test_normaliser_preserves_email_content_and_recipients
- **Traces to:** MASTER_SPEC §5.1, §7, §11; TASK_LEDGER T20 normaliser mapping goal.
- **Input:** Email scenarios #4, #5, and #6.
- **Expected outcome:** Each canonical Action preserves the exact email body content and recipient/domain data needed by Presidio, the nuance stub, context resolution, and OPA. Scenario #4 must retain the planted NHS/health/repayment text; #5 must retain the planted “struggling a bit since losing my job” phrase; #6 must retain customer-name-only content for the partner email.
- **Notes:** Exact planted phrases matter because the Presidio and nuance tests rely on deterministic scenario content.

### test_presidio_detects_scenario_4_real_pii_and_special_category_evidence
- **Traces to:** MASTER_SPEC §1, §2, §5.3, §7 scenario #4, §12 real Presidio acceptance criterion; TASK_LEDGER T20 Presidio detection goal.
- **Input:** Scenario #4 email body: external email with NHS number, health condition, and “can't afford repayments” content.
- **Expected outcome:** Running the real Presidio sensor/evidence builder path reports detected entities and evidence spans from the real sensor, includes an NHS-number or equivalent planted identifier detection, sets `contains_personal_data=true`, sets `contains_special_category_data=true`, sets `evaluated=true`, and preserves `sensor_versions.presidio` plus `sensor_versions.nuance_stub="stub-0.1"` where full evidence is asserted.
- **Notes:** Do not fake or hardcode detections in the test. The test may assert entity types/spans flexibly enough for Presidio scoring variation, but it must prove real sensor output exists and special-category classification follows from it.

### test_presidio_scenario_6_is_personal_data_only_not_special_category
- **Traces to:** MASTER_SPEC §5.3, §7 scenario #6, §12; TASK_LEDGER T20 Presidio detection goal.
- **Input:** Scenario #6 partner email body containing only a customer name/personal data and no special-category or vulnerability trigger phrase.
- **Expected outcome:** Evidence is evaluated, identifies personal data where the real sensor supports it, does not mark special-category data, has no vulnerability indicator, and produces the evidence conditions that allow COMM-EMAIL-003 to be reached downstream.
- **Notes:** This is the negative-control email case; it prevents the demo from over-escalating benign partner disclosure scenarios.

### test_policy_decisions_match_master_spec_section_7_for_all_six_scenarios
- **Traces to:** MASTER_SPEC §6, §7, §11, §12; TASK_LEDGER T20 policy-decision regression guard.
- **Input:** Execute/evaluate scenarios #1 through #6 through the existing policy path that calls OPA/Rego with Action, Context, Evidence, and runtime config.
- **Expected outcome:** Decisions must exactly match:
  - #1: `allow`, no control ID required.
  - #2: `escalate`, `control_id="FIN-PAY-002"`, `required_approval_role="finance_supervisor"`.
  - #3: `block`, `control_id="FIN-PAY-001"`, no human approval queue role required by policy.
  - #4: `escalate`, `control_id="COMM-EMAIL-001"`, `required_approval_role="data_protection_approver"`.
  - #5: `escalate`, `control_id="COMM-EMAIL-002"`, `required_approval_role="vulnerable_customer_team"` at the default threshold `0.75`.
  - #6: `allow_with_logging`, `control_id="COMM-EMAIL-003"`, enhanced logging where exposed.
- **Notes:** OPA/Rego must be the judge. The test may compare to a static expected table, but must not duplicate policy decision logic in Python. Assert `triggered_controls`, framework mappings presence, `failure_mode`, and `threshold_used` where exposed by the Decision schema.

### test_policy_precedence_blocks_prohibited_payment_even_when_other_payment_controls_trigger
- **Traces to:** MASTER_SPEC §6 decision precedence and FIN-PAY-001 prohibited tier; TASK_LEDGER T20 reviewer focus on full policy guard.
- **Input:** A policy input based on a flagged/sanctions/blocked customer payment that also satisfies another payment escalation trigger, such as amount > £500 without approval.
- **Expected outcome:** OPA returns `decision="block"` with `control_id="FIN-PAY-001"` because `block` for the prohibited tier outranks escalation. `triggered_controls` may include lower-precedence controls, but the binding decision must be block.
- **Notes:** This protects the “block only clearly prohibited, but highest precedence wins” message without adding product code.

### test_threshold_change_flips_scenario_5_to_allow_with_logging
- **Traces to:** MASTER_SPEC §6 configurable `HIGH_CONFIDENCE`, §7 scenario #5, §12 threshold acceptance criterion; TASK_LEDGER T20 policy-decision guard.
- **Input:** Scenario #5 evaluated with default threshold `0.75`, then with threshold `0.60` through the existing settings/config path or OPA input config.
- **Expected outcome:** At `0.75`, scenario #5 escalates via COMM-EMAIL-002 to `vulnerable_customer_team`. At `0.60`, the same planted confidence (`0.62`) no longer satisfies the uncertainty escalation and the decision becomes `allow_with_logging` through COMM-EMAIL-003. The Decision must echo the threshold used.
- **Notes:** This is a functional acceptance test for risk-owned policy tuning. Do not hardcode `0.75` in application logic to satisfy the test.

### test_payment_scenarios_do_not_invoke_semantic_layer
- **Traces to:** MASTER_SPEC §2, §3, §5.3, §11, §12; non-negotiable payment semantic skip rule.
- **Input:** Payment scenarios #1, #2, and #3 through the tested pipeline/evidence path.
- **Expected outcome:** Evidence for payment actions has `evaluated=false`, no required semantic detections, and no semantic-layer output is needed for the policy decision.
- **Notes:** This may live in `test_policy_decisions.py` if the scenario execution returns evidence, or in `test_normaliser.py` only if the available T20 path does not expose evidence. Prefer the pipeline/policy test because it validates the integrated skip.

### test_audit_chain_verifies_multiple_appended_records_intact
- **Traces to:** MASTER_SPEC §5.5 hash rule, §12 verify-chain acceptance criterion; TASK_LEDGER T20 audit chain integrity goal.
- **Input:** Use the existing audit store to append at least three action/evaluation-style records with valid Action, Context, Evidence, and Decision payloads.
- **Expected outcome:** Each write produces a record hash; the first record uses the 64-zero genesis previous hash; later records link to the previous record hash; `verify_chain()` reports intact for all written records.
- **Notes:** Use real store/hash-chain implementation. Test data may be minimal but must satisfy schema contracts. Normal audit writes must be append-only.

### test_audit_chain_reports_exact_tampered_record
- **Traces to:** MASTER_SPEC §5.5 simulate tampering and tamper-evident hash chain; MASTER_SPEC §8A item 6; TASK_LEDGER T20 chain tamper detection reviewer focus.
- **Input:** After creating an intact multi-record chain, tamper with a historical row using the existing deliberately labelled tamper helper.
- **Expected outcome:** `verify_chain()` fails and reports the exact tampered row/record identifier or index, not merely a generic failure. Records before the tampered row remain valid up to that point.
- **Notes:** This test must not implement an ad hoc database update path except through the existing `simulate_tampering()` helper intended for the demo.

## Coverage checklist
- [x] Happy path covered: normaliser mapping, all six scenario decisions, intact audit chain.
- [x] Error/edge cases covered: policy precedence, threshold boundary/flip, scenario #6 negative-control email, tamper detection.
- [x] Spec non-negotiables verified: OPA is judge, Evidence has no decision field, payments skip semantics, real Presidio, append-only hash chain.
- [x] Real dependencies flagged: Presidio tests must use the real sensor; policy decisions must call real OPA/Rego via the existing client/pipeline; audit tests must use the real audit store/hash implementation rather than mocked hashes.

## Gaps or ambiguities
- TASK_LEDGER T20 lists the files as `tests/test_normaliser.py`, `test_presidio_sensor.py`, `test_policy_decisions.py`, and `test_audit_chain.py`; the Architect brief clarifies all four are root-level files under `tests/`. Implementer should use exactly those paths and not create task subdirectories for T20.
- If the existing codebase cannot run OPA/Postgres-dependent tests under `docker compose run --rm app pytest -q` without service setup, the Implementer should report the infrastructure gap rather than replacing real OPA, Presidio, or hash-chain behaviour with mocks.