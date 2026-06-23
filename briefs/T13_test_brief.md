# Test Brief — T13: pipeline.py (INTEGRATION MILESTONE)

## Spec references
- MASTER_SPEC.md: §2 principles (OPA is judge, evidence only, fail closed), §5.1–§5.5 canonical schemas, §6 control library/precedence/configurable threshold, §7 six narrative scenarios, §8 enforcement modes, §11 pipeline order, §12 acceptance criteria.
- TASK_LEDGER.md: T13 goal, key notes, done-when, verify step, and reviewer focus: full loop through intercept → normalise → resolve → semantic evidence for email only → settings → OPA → enforce → append audit record; `POST /run/{scenario_id}` returns Decision plus record hash; every run writes a record; fail-closed paths are reachable.
- briefs/T13_architect_brief.md: T13 non-negotiables, allowed files, expected §7 outcome table, real-dependency requirements, and minimum pytest coverage.

## Target test location
- Folder: `tests/T13_pipeline/`
- Suggested files:
  - `test_run_endpoint.py` — covers end-to-end JSON endpoint behaviour for scenarios 1–6 and response shape.
  - `test_pipeline_records.py` — covers audit record creation, hash-chain integrity, payment evidence semantics, and enforcement/approval queue side effects observable from the pipeline.
  - `test_pipeline_fail_closed.py` — covers context, sensor, and OPA failure paths writing fail-closed records.
  - `test_pipeline_threshold.py` — covers Scenario 5 default-threshold escalation and threshold-lowered `allow_with_logging` flip.

## Test cases

### test_post_run_all_scenarios_returns_expected_decisions
- **Traces to:** MASTER_SPEC.md §7; MASTER_SPEC.md §11 steps 1–8; MASTER_SPEC.md §12 "All six scenarios produce exactly the §7 decisions"; TASK_LEDGER.md T13 done-when/verify.
- **Input:** Use the FastAPI test client, or equivalent integration client against the app route, to `POST /run/{scenario_id}` for scenario IDs `1`, `2`, `3`, `4`, `5`, and `6` with default settings.
- **Expected outcome:** Each response is successful JSON and includes a `decision` object plus a non-empty `record_hash`. Expected decision assertions:
  - Scenario 1: `decision="allow"`, `control_id is None` or absent/null-equivalent, `required_approval_role is None`.
  - Scenario 2: `decision="escalate"`, `control_id="FIN-PAY-002"`, `required_approval_role="finance_supervisor"`.
  - Scenario 3: `decision="block"`, `control_id="FIN-PAY-001"`, `required_approval_role is None`.
  - Scenario 4: `decision="escalate"`, `control_id="COMM-EMAIL-001"`, `required_approval_role="data_protection_approver"`.
  - Scenario 5: `decision="escalate"`, `control_id="COMM-EMAIL-002"`, `required_approval_role="vulnerable_customer_team"` at the default threshold.
  - Scenario 6: `decision="allow_with_logging"`, `control_id="COMM-EMAIL-003"`, `required_approval_role is None`.
- **Notes:** This is an integration/acceptance test. Decisions must emerge from existing scenario data, normalisation, context, evidence, settings, and OPA policy. The test must not assert outcomes produced by hardcoded Python policy logic.

### test_post_run_rejects_unknown_scenario_without_audit_record
- **Traces to:** MASTER_SPEC.md §11 pipeline starts with an intercepted scenario/tool call; TASK_LEDGER.md T13 endpoint is specifically `POST /run/{scenario_id}` for scenarios 1..6.
- **Input:** `POST /run/999` or another scenario ID that is not defined in `scenarios/scenarios.py`.
- **Expected outcome:** Response is a clear client error such as HTTP 404 or 400 with an explanatory JSON error. No new `action_evaluation` audit record is appended because no valid proposed action entered the pipeline.
- **Notes:** This guards endpoint hygiene without broadening T13 beyond the JSON scenario endpoint.

### test_every_valid_run_writes_action_evaluation_record_with_hash
- **Traces to:** MASTER_SPEC.md §5.5 Evidence Record; MASTER_SPEC.md §11 step 7 "Always written"; TASK_LEDGER.md T13 key note "Every run writes a record regardless of decision."
- **Input:** Run scenarios 1–6 through the pipeline/endpoint using an isolated test database or reset test store.
- **Expected outcome:** Exactly one new `record_type="action_evaluation"` row is appended per valid scenario run. Each row has a non-empty SHA-256-looking `record_hash`, a `prev_hash`, the scenario correlation ID, `action`, `context_used`, `evidence`, `decision`, `enforcement_mode`, and `executed`. The response `record_hash` equals the written row's `record_hash`.
- **Notes:** Use the real T12 audit store/hash-chain implementation. Do not mock out the write path.

### test_audit_chain_is_intact_after_six_runs
- **Traces to:** MASTER_SPEC.md §5.5 hash rule; MASTER_SPEC.md §12 "Verify chain passes"; TASK_LEDGER.md T13 verify step "hit verify_chain → intact."
- **Input:** After running scenarios 1–6 in order, call the T12 store verification path (`verify_chain()` or the existing exposed equivalent).
- **Expected outcome:** Chain verification reports intact/valid and includes all six appended action-evaluation records in the verified count or result set.
- **Notes:** This must use the real audit store verification logic, not an assertion over response JSON alone.

### test_payment_scenarios_do_not_evaluate_semantic_layer
- **Traces to:** MASTER_SPEC.md §3 "payment path skips it"; MASTER_SPEC.md §5.3 Evidence `evaluated=false` for payment path; MASTER_SPEC.md §12 "Payment scenarios never invoke the semantic layer"; TASK_LEDGER.md T13 reviewer focus.
- **Input:** Run payment scenarios 1, 2, and 3.
- **Expected outcome:** The audit record evidence for each payment scenario has `evaluated=false`, `sensor_error=false`, no meaningful Presidio spans/entities required, and no vulnerability-stub confidence driving the payment decision. Decisions still match §7.
- **Notes:** If the existing evidence object uses empty lists/default booleans for non-evaluated payments, assert those defaults exactly as implemented by the T07 schema while preserving `evaluated=false` as the primary acceptance assertion.

### test_email_scenarios_evaluate_real_evidence_and_stub_labels
- **Traces to:** MASTER_SPEC.md §2 deterministic tools before model stub; MASTER_SPEC.md §5.3 Evidence; MASTER_SPEC.md §7 scenarios 4–6; MASTER_SPEC.md §12 Scenario 4 real Presidio entities and labelled stub confidence.
- **Input:** Run email scenarios 4, 5, and 6.
- **Expected outcome:** Each audit record evidence has `evaluated=true`, `sensor_versions.nuance_stub="stub-0.1"`, and vulnerability indicator `source="nuance_stub"` where represented. Scenario 4 evidence includes real detected entities/spans for the planted NHS/health/personal-data content and `overall_confidence`/vulnerability confidence consistent with `0.88`. Scenario 5 includes vulnerability confidence `0.62`. Scenario 6 has no special category and no vulnerability indicator sufficient to escalate.
- **Notes:** Presidio must be exercised for real; do not replace it with a mocked entity list. The nuance layer is intentionally a labelled deterministic stub.

### test_escalations_are_queued_and_blocks_are_not_queued
- **Traces to:** MASTER_SPEC.md §8 enforcement modes; MASTER_SPEC.md §11 step 6; TASK_LEDGER.md T11/T13 reviewer focus that blocks do not go to the human queue and escalations do.
- **Input:** With default/full enforcement mode, run Scenario 2 and Scenario 3, then inspect the existing T11 approval queue interface/state.
- **Expected outcome:** Scenario 2 writes an action-evaluation record with `executed=false` and creates/records a pending escalation for `finance_supervisor`. Scenario 3 writes an action-evaluation record with `executed=false` and does not create a human approval queue item because `block` is prohibited-tier hard stop.
- **Notes:** If the default seeded enforcement mode is not full, the test setup may explicitly set full mode using the T08 settings interface. Keep this an observable pipeline acceptance test, not a unit test of the T11 handler.

### test_shadow_mode_block_executes_but_records_block_decision
- **Traces to:** MASTER_SPEC.md §8 shadow mode; MASTER_SPEC.md §12 "Shadow mode makes Scenario 3 execute anyway with a would-have-blocked badge; the record shows executed=true, decision=block."
- **Input:** Set enforcement mode to `shadow` using the existing settings/control-mode interface, then run Scenario 3.
- **Expected outcome:** Response/audit record decision remains `block` with `control_id="FIN-PAY-001"`, but the audit record has `executed=true`. If the T11 enforcement result exposes a `would_have_blocked`/equivalent flag in response or record metadata, assert it; otherwise assert the mandated `executed=true` plus unchanged binding decision.
- **Notes:** This verifies that enforcement mode changes execution, not OPA's binding decision.

### test_scenario_5_threshold_flip_to_allow_with_logging
- **Traces to:** MASTER_SPEC.md §6 configurable `HIGH_CONFIDENCE` threshold; MASTER_SPEC.md §7 Scenario 5 confidence `0.62`; MASTER_SPEC.md §8A/§12 threshold flip; TASK_LEDGER.md T13 architect minimum coverage.
- **Input:** First run Scenario 5 at default threshold; then update the settings row high-confidence threshold to `0.60` using the existing T08 settings store; run Scenario 5 again.
- **Expected outcome:** Default run returns `decision="escalate"`, `control_id="COMM-EMAIL-002"`, `required_approval_role="vulnerable_customer_team"`, and `threshold_used=0.75` or the seeded default. Lowered-threshold run returns `decision="allow_with_logging"`, expected logging control such as `COMM-EMAIL-003` if returned by policy for this path, no approval role, and `threshold_used=0.60`.
- **Notes:** The acceptance point is that settings are loaded at runtime and passed into OPA input; no app restart and no hardcoded threshold. If the policy returns a different logging control for the allow-with-logging side of Scenario 5, the Implementer should align with MASTER_SPEC/T10 policy behaviour and document the exact observed control in the test assertion.

### test_context_resolution_failure_writes_fail_closed_record
- **Traces to:** MASTER_SPEC.md §2 fail closed; MASTER_SPEC.md §5.2 `context_resolution_ok=false`; MASTER_SPEC.md §11 steps 3, 5, and 7; TASK_LEDGER.md T13 key notes.
- **Input:** Exercise the existing T05-supported mechanism for forcing context resolution failure through the pipeline for a valid scenario/action.
- **Expected outcome:** Pipeline returns/writes a Decision with `decision="fail_closed"`, `failure_mode="fail_closed"`, and a clear reason. An audit `action_evaluation` record is still appended with `context_used.context_resolution_ok=false`, the fail-closed decision, and a non-empty `record_hash`.
- **Notes:** This test may use monkeypatching only to trigger the failure mechanism if no scenario fixture exposes it directly. It must still assert the real pipeline writes the record.

### test_sensor_error_writes_fail_closed_record_for_email
- **Traces to:** MASTER_SPEC.md §2 fail closed; MASTER_SPEC.md §5.3 `sensor_error=true`; MASTER_SPEC.md §11 steps 4, 5, and 7; TASK_LEDGER.md T13 key notes.
- **Input:** Cause the existing email evidence builder/sensor path to report or raise a sensor error while running an email scenario such as Scenario 4.
- **Expected outcome:** Pipeline returns/writes a Decision with `decision="fail_closed"`, `failure_mode="fail_closed"`; evidence has `evaluated=true` or attempted email evaluation semantics plus `sensor_error=true`; a non-empty audit record hash is written.
- **Notes:** It is acceptable to monkeypatch the sensor/evidence builder to raise for this acceptance test, because the purpose is fail-closed pipeline behaviour. Do not mock OPA for the normal scenario decision tests.

### test_opa_unreachable_writes_fail_closed_record
- **Traces to:** MASTER_SPEC.md §2 fail closed; MASTER_SPEC.md §11 step 5; TASK_LEDGER.md T09 OPA unreachable contract and T13 fail-closed reachability.
- **Input:** Run a valid scenario while configuring the real OPA client to use an unreachable OPA endpoint, or monkeypatch only the OPA client boundary to simulate the existing T09 unreachable behaviour.
- **Expected outcome:** Pipeline returns/writes `decision="fail_closed"`, `failure_mode="fail_closed"`, includes a clear OPA-unreachable reason/control as defined by the existing Decision schema/client behaviour, and still appends an audit record with a non-empty `record_hash`.
- **Notes:** Normal decision tests must use real OPA. This failure test may simulate the boundary condition if starting/stopping the OPA service is impractical inside pytest.

### test_endpoint_response_contains_contract_fields_without_exposing_extra_ui_scope
- **Traces to:** MASTER_SPEC.md §5.4 Decision schema; TASK_LEDGER.md T13 goal "JSON endpoint only for now".
- **Input:** `POST /run/1`.
- **Expected outcome:** Response includes the Decision fields required by §5.4, a non-empty `record_hash`, and any minimal record identifier/correlation metadata needed by downstream UI. Response does not require server-rendered templates or T14+ UI artifacts.
- **Notes:** This keeps T13 limited to the JSON integration milestone and avoids starting Phase 3 early.

## Coverage checklist
- [ ] Happy path covered: all six scenario runs through `POST /run/{scenario_id}` with exact §7 decisions and response hashes.
- [ ] Error/edge cases covered: unknown scenario, context failure, sensor error, OPA unreachable.
- [ ] Spec non-negotiables verified: OPA remains binding judge, Evidence has no decision semantics, payment path has `evaluated=false`, every valid run writes an append-only hash-chained record, blocks do not go to approval queue, threshold is runtime-configurable.
- [ ] Real dependencies flagged (no mocks where forbidden): normal scenario decision tests use real OPA policy path, email evidence tests use real Presidio plus labelled nuance stub, audit tests use real T12 store/hash-chain. Boundary simulation is allowed only for explicit failure injection tests.

## Gaps or ambiguities
- The T13 task requires verifying the audit chain but does not name a JSON route for chain verification yet. Tests should call the existing T12 store `verify_chain()` path directly unless the Implementer exposes a minimal existing route within `app/web/routes.py` without expanding into T18 UI scope.
- The exact response envelope for `POST /run/{scenario_id}` is not specified beyond Decision plus record hash. The Implementer should keep it minimal and stable; tests should require the Decision object and `record_hash` while tolerating optional correlation/record identifiers.
- The exact seeded/default enforcement mode may depend on T08 settings. Tests that assert full-mode queue/block execution should explicitly set full mode through the settings store if the default is not full.
- The policy-side control ID for Scenario 5 after lowering the threshold to `0.60` should follow the existing T10 policy/spec behaviour. The required business outcome is `allow_with_logging` with `threshold_used=0.60`; if the returned control differs from `COMM-EMAIL-003`, align the assertion to the policy metadata rather than hardcoding a PM/BA guess.