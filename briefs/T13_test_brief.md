# Test Brief — T13: pipeline.py (INTEGRATION MILESTONE)

## Spec references
- MASTER_SPEC.md: §2 principles (OPA is judge, Evidence is evidence only, fail closed), §3 logical architecture, §5.1–§5.5 canonical schemas, §6 controls/precedence/threshold, §7 six narrative scenario outcomes, §8 enforcement modes, §11 pipeline order, §12 acceptance criteria, §13 scope fences.
- TASK_LEDGER.md: T13 goal, dependencies T03–T12, allowed files, key notes, done-when, verify step, and reviewer focus.
- Architect Brief: `briefs/T13_architect_brief.md`, especially allowed-file exception for minimal router registration in `app/main.py`, non-negotiables, and endpoint-level pytest expectations.

## Target test location
- Folder: `tests/T13_pipeline/`
- Suggested files:
  - `test_pipeline_scenarios.py` — covers the six normal-path scenario outcomes, record creation, payment semantic skip, threshold flip, and intact chain after normal runs.
  - `test_pipeline_endpoint.py` — covers `POST /run/{scenario_id}` endpoint behaviour for scenarios 1–6 and invalid scenario IDs.
  - `test_pipeline_fail_closed.py` — covers context-resolution, sensor, and OPA-failure fail-closed paths writing audit records.
  - `__init__.py` — package marker for the T13 test folder.

## Test cases

### test_pipeline_runs_all_scenarios_with_exact_spec_decisions
- **Traces to:** MASTER_SPEC.md §7; TASK_LEDGER.md T13 “Done when”; Architect Brief normal-path scenario requirements.
- **Input:** Run the full T13 pipeline for scenario IDs `1` through `6` using the real scenario simulator/wrapper, normaliser, context resolver, evidence builder, settings store, OPA/Rego client, enforcement handler, approval queue, and audit store.
- **Expected outcome:** Each result returns a parsed Decision with exactly these values:
  - Scenario 1: `decision="allow"`, `control_id is None`, `required_approval_role is None`.
  - Scenario 2: `decision="escalate"`, `control_id="FIN-PAY-002"`, `required_approval_role="finance_supervisor"`.
  - Scenario 3: `decision="block"`, `control_id="FIN-PAY-001"`, `required_approval_role is None`.
  - Scenario 4: `decision="escalate"`, `control_id="COMM-EMAIL-001"`, `required_approval_role="data_protection_approver"`.
  - Scenario 5: `decision="escalate"`, `control_id="COMM-EMAIL-002"`, `required_approval_role="vulnerable_customer_team"` at the default threshold.
  - Scenario 6: `decision="allow_with_logging"`, `control_id="COMM-EMAIL-003"`, `required_approval_role is None`.
- **Notes:** Normal-path decisions must come from the real OPA/Rego path. Do not mock or hardcode the policy result for this test.

### test_pipeline_writes_hash_chained_record_for_every_scenario
- **Traces to:** MASTER_SPEC.md §5.5 and §11 step 7; TASK_LEDGER.md T13 “Every run writes a record regardless of decision.”
- **Input:** Run scenarios `1` through `6` through the full pipeline.
- **Expected outcome:** Every pipeline result includes a non-empty `record_hash` matching the persisted audit record; six `action_evaluation` records are appended; each persisted row includes the Action, Context, Evidence, Decision, enforcement mode, executed flag, `prev_hash`, and `record_hash` according to the Evidence Record schema.
- **Notes:** This is acceptance coverage, not an internal hash implementation unit test. Use the real T12 audit store/hash-chain path.

### test_audit_chain_intact_after_six_pipeline_runs
- **Traces to:** MASTER_SPEC.md §5.5, §8A item 6, §11 step 7, §12 “Verify chain passes.”
- **Input:** After six successful scenario runs, call the real T12 `verify_chain()` path.
- **Expected outcome:** Chain verification reports intact and includes/counts the records written by the pipeline runs.
- **Notes:** Do not manually recompute a separate chain in the test; verify via the store API that the application will use.

### test_payment_scenarios_do_not_invoke_semantic_layer
- **Traces to:** MASTER_SPEC.md §3, §11 step 4, §12 “Payment scenarios never invoke the semantic layer”; Architect Brief payment Evidence non-negotiable.
- **Input:** Run payment scenario IDs `1`, `2`, and `3` through the full pipeline.
- **Expected outcome:** Persisted Evidence for each payment record has `evaluated=false`, `detected_entities=[]`, `evidence_spans=[]`, and no semantic sensor output implying Presidio or nuance analysis was performed.
- **Notes:** The acceptance assertion is on the persisted Evidence contract. If feasible without over-coupling to implementation internals, also assert the evidence builder/sensors were not called for payments.

### test_email_scenarios_use_real_evidence_and_labelled_stub_source
- **Traces to:** MASTER_SPEC.md §5.3, §7 scenarios 4–6, §12 Scenario 4 real Presidio entities; T06/T07 dependency contracts.
- **Input:** Run email scenarios `4`, `5`, and `6` through the full pipeline.
- **Expected outcome:** Persisted Evidence has `evaluated=true`; `sensor_versions.nuance_stub="stub-0.1"`; vulnerability indicator source is `nuance_stub`; scenario 4 contains personal and special-category evidence with non-empty detected entities/spans from Presidio; scenario 5 has vulnerability confidence `0.62`; scenario 6 has no special-category/vulnerability finding and reaches `allow_with_logging`.
- **Notes:** Presidio must be real for this path. The nuance classifier remains a labelled deterministic stub as specified.

### test_threshold_060_flips_scenario_5_to_allow_with_logging
- **Traces to:** MASTER_SPEC.md §6 threshold rule, §8A Settings impact panel, §12 threshold flip; TASK_LEDGER.md T13 verify note.
- **Input:** Persist/update runtime settings so `high_confidence_threshold=0.60`, then run scenario `5` through the full pipeline.
- **Expected outcome:** Scenario 5 returns `decision="allow_with_logging"`, `control_id="COMM-EMAIL-002"` or the policy-defined logging control for the threshold-cleared vulnerable-customer case, `required_approval_role is None`, and the Decision echoes `threshold_used=0.60`.
- **Notes:** Use the real settings store and real OPA input path. If existing settings/test infrastructure cannot safely change the persisted threshold in isolation, the Implementer should document that limitation and still cover threshold propagation through an isolated test database/transaction fixture.

### test_decision_threshold_used_echoes_runtime_setting
- **Traces to:** MASTER_SPEC.md §5.4 Decision schema and §6 threshold configuration.
- **Input:** Run at least one normal scenario with default settings and one scenario after setting threshold to `0.60`.
- **Expected outcome:** The returned and persisted Decision includes `threshold_used` matching the runtime setting value sent to OPA for that run.
- **Notes:** This verifies Python loaded settings and passed them into OPA rather than relying on a Rego-hardcoded threshold.

### test_enforcement_results_and_queue_side_effects_match_decisions
- **Traces to:** MASTER_SPEC.md §8; TASK_LEDGER.md T11/T13 enforcement requirements; Architect Brief blocks do not queue, escalations do.
- **Input:** Run scenarios `2`, `3`, and `4` in full enforcement mode.
- **Expected outcome:** Scenario 2 and 4 escalation runs are not executed and produce pending approval-queue entries with roles `finance_supervisor` and `data_protection_approver`; scenario 3 block is not executed and does not create a human approval-queue entry; all three still write audit records.
- **Notes:** Assert externally visible handler/queue/store state, not private helper implementation.

### test_endpoint_post_run_all_scenarios_returns_decision_and_record_hash
- **Traces to:** MASTER_SPEC.md §11 step 8; TASK_LEDGER.md T13 JSON endpoint and verify commands; Architect Brief endpoint registration requirement.
- **Input:** Use a FastAPI test client or real running app to `POST /run/1`, `/run/2`, `/run/3`, `/run/4`, `/run/5`, `/run/6`.
- **Expected outcome:** Each response has a success HTTP status, a JSON Decision matching the exact §7 expected decision/control/approval-role values, and a non-empty `record_hash` corresponding to a persisted audit record.
- **Notes:** The route must be registered on the real application object served on port 8080, not only on a test-local app instance.

### test_endpoint_rejects_unknown_scenario_id_without_writing_success_record
- **Traces to:** MASTER_SPEC.md §11 endpoint purpose; TASK_LEDGER.md T13 endpoint scope.
- **Input:** `POST /run/999` or another scenario ID that does not exist.
- **Expected outcome:** Endpoint returns a clear client error such as `404` or `422` with an explanatory JSON body; no successful action-evaluation record is written for a nonexistent scenario.
- **Notes:** This is an endpoint edge case. It must not invent fallback actions or silently run a default scenario.

### test_context_resolution_failure_fail_closes_and_writes_record
- **Traces to:** MASTER_SPEC.md §2 fail closed, §5.2 `context_resolution_ok`, §11 steps 3/5/7; TASK_LEDGER.md T13 fail-closed note.
- **Input:** Run the pipeline with a scenario/action arranged through existing resolver support to force `context_resolution_ok=false`.
- **Expected outcome:** Pipeline returns/persists a Decision with `decision="fail_closed"`, `failure_mode="fail_closed"`; enforcement prevents execution in full mode; a hash-chained audit record is still appended with the failed context/evidence state.
- **Notes:** Boundary simulation is acceptable for the forced resolver failure, but the persisted record and fail-closed handling must use production schemas/store paths.

### test_sensor_error_fail_closes_and_writes_record_for_email
- **Traces to:** MASTER_SPEC.md §2 fail closed, §5.3 `sensor_error`, §11 steps 4/5/7; Architect Brief fail-closed reachability.
- **Input:** Run an email action while arranging the semantic sensor/evidence path to raise or return `sensor_error=true`.
- **Expected outcome:** Pipeline returns/persists a Decision with `decision="fail_closed"`, `failure_mode="fail_closed"`; `evidence.sensor_error=true`; execution is prevented in full mode; an audit record with a non-empty hash is appended.
- **Notes:** Boundary simulation/mocking is acceptable only to trigger the sensor failure. Do not mock the audit write.

### test_opa_unavailable_fail_closes_and_writes_record
- **Traces to:** MASTER_SPEC.md §2 and §13 OPA failure rule; TASK_LEDGER.md T09/T13 fail-closed requirements.
- **Input:** Run a scenario with OPA unavailable or arrange the existing `opa_client` failure path to return `fail_closed`.
- **Expected outcome:** Pipeline returns/persists a `fail_closed` Decision with `failure_mode="fail_closed"`; a record is appended with the Action, Context, Evidence gathered before the OPA failure; record hash is non-empty.
- **Notes:** This test may use boundary simulation for OPA unavailability. It must not validate a Python-made normal allow/block/escalate decision.

## Coverage checklist
- [x] Happy path covered: all six §7 scenarios through pipeline and endpoint.
- [x] Error/edge cases covered: invalid scenario ID, context failure, sensor failure, OPA failure.
- [x] Spec non-negotiables verified: OPA is normal-path judge, payment semantic skip, Evidence remains evidence-only by persisted contract, fail-closed paths, append-only hash-chained records, blocks do not route to approval queue, escalations do.
- [x] Real dependencies flagged: normal-path tests must use real OPA/Rego, real Presidio/evidence builder, real settings store, real enforcement/approval queue, and real T12 audit store/hash-chain path; mocks are allowed only to induce explicit fail-closed boundary failures.

## Gaps or ambiguities
- The T13 ledger file list omits `app/main.py`, but the Architect Brief allows a minimal router-registration change so the real app on port 8080 exposes `POST /run/{scenario_id}`. Implementer should keep that change minimal and not refactor app scaffolding.
- Scenario 5 threshold flip expectation should assert `allow_with_logging` when `high_confidence_threshold=0.60`. The exact `control_id` for the threshold-cleared vulnerable-customer/logging outcome should follow the existing T10 Rego output; do not invent a new control in T13.
- The test environment must isolate audit records/settings between tests so chain counts and threshold values are deterministic. This is a test-fixture concern for the Implementer, not a product behaviour change.
