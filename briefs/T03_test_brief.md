# Test Brief — T03: Scenarios + agent simulator + SDK wrapper (PEP)

## Spec references
- MASTER_SPEC.md: §1 item 1 (agent actions are intercepted before execution through the SDK wrapper PEP), §3 logical architecture (`Agent simulator` → `SDK wrapper = Policy Enforcement Point (PEP)`), §5.1 Action schema values to preserve in raw calls for later normalisation, §7 six narrative scenarios and planted phrase expectations, §8 valid enforcement modes, §12 acceptance criteria for scenario decisions and payment/email handling that later tasks depend on.
- TASK_LEDGER.md: T03 goal, allowed files, key notes, Done when, Verify step, and Reviewer focus.
- Architect Brief: `briefs/T03_architect_brief.md` implementation objective and non-negotiables.

## Target test location
- Folder: `tests/T03_scenarios/`
- Suggested files:
  - `test_scenario_catalog.py` — covers canonical scenario count, stable IDs, raw-call shape, fixture customer IDs, planted email content, expected-outcome metadata, and payment/email separation.
  - `test_agent_simulator.py` — covers simulator iteration/emission of exactly one raw tool call per scenario and no direct execution semantics.
  - `test_sdk_wrapper.py` — covers the SDK wrapper PEP interception message, downstream placeholder echo, forwarding of unchanged raw-call dictionaries, and verification-loop behaviour across all six scenarios.

## Test cases

### test_catalog_contains_exactly_six_canonical_scenarios
- **Traces to:** MASTER_SPEC.md §7; TASK_LEDGER.md T03 Goal and Key notes.
- **Input:** Import the scenario catalog from `scenarios.scenarios`.
- **Expected outcome:** The catalog exposes exactly six scenarios, with stable identifiers representing scenarios 1 through 6 and no extra scenarios.
- **Notes:** This prevents the demo narrative from drifting before policy/UI tasks depend on the canonical set.

### test_payment_scenarios_preserve_fixture_customer_ids_and_amounts
- **Traces to:** MASTER_SPEC.md §7 scenarios 1–3; Architect Brief non-negotiables for customer IDs; TASK_LEDGER.md T03 Key notes.
- **Input:** Read raw tool-call data for scenarios 1, 2, and 3 from the scenario catalog.
- **Expected outcome:**
  - Scenario 1 is a payment raw call for customer/resource `CUST-100` with amount GBP 80.
  - Scenario 2 is a payment raw call for customer/resource `CUST-100` with amount GBP 850 and represents no pre-existing approval.
  - Scenario 3 is a payment raw call for customer/resource `CUST-300` with amount GBP 200.
  - All three payment calls carry a valid `enforcement_mode` value from `shadow`, `soft`, or `full`.
- **Notes:** The test must assert raw input data only. It must not assert a policy decision from executable code, because T03 must not implement policy.

### test_payment_scenarios_do_not_include_email_semantic_content
- **Traces to:** MASTER_SPEC.md §3 semantic layer runs only where needed; §7 scenarios 1–3; TASK_LEDGER.md T03 Reviewer focus; Architect Brief non-negotiable that payment scenarios remain compatible with later `evidence.evaluated=false`.
- **Input:** Raw tool-call dictionaries for scenarios 1, 2, and 3.
- **Expected outcome:** Payment raw calls do not include an email body/content field with unstructured customer communication text, do not include an email recipient, and use a payment-oriented tool/action representation rather than an email send representation.
- **Notes:** This is an acceptance guard for the later requirement that payment scenarios never invoke the semantic layer.

### test_email_scenarios_include_required_recipients_and_planted_content
- **Traces to:** MASTER_SPEC.md §7 scenarios 4–6; Architect Brief non-negotiables for planted phrases and recipients; TASK_LEDGER.md T03 Key notes and Reviewer focus.
- **Input:** Raw tool-call dictionaries for scenarios 4, 5, and 6.
- **Expected outcome:**
  - Scenario 4 is an external email raw call to a Gmail recipient, represents no approved disclosure basis, and its body contains an NHS number, a health condition, and the exact phrase `can't afford repayments`.
  - Scenario 5 is an external email raw call and its body contains the exact phrase `struggling a bit since losing my job`.
  - Scenario 6 is an external email raw call to a known partner recipient and its body contains only low-risk customer-name style content, with no NHS number, no health-condition phrase, no `can't afford repayments`, and no `struggling a bit since losing my job` phrase.
  - All three email calls carry a valid `enforcement_mode` value from `shadow`, `soft`, or `full`.
- **Notes:** These planted phrases must be exact enough for later deterministic Presidio/stub tests to be reproducible. This test should not invoke Presidio or the nuance stub; those are out of T03 scope.

### test_expected_outcomes_are_metadata_not_executable_policy
- **Traces to:** MASTER_SPEC.md §2 model/policy separation; §6 decision precedence belongs to OPA; §7 scenario expected outcomes; Architect Brief non-negotiable that expected outcomes/control intent are metadata or comments only.
- **Input:** Scenario catalog entries for all six scenarios and raw tool calls emitted by the simulator.
- **Expected outcome:** Scenario entries may expose expected decision/control/approval-role metadata for traceability, but emitted raw tool-call dictionaries do not contain binding decision/enforcement fields such as `decision`, `allow`, `block`, `approval_decision`, `executed`, `control_id`, or `triggered_controls`.
- **Notes:** This protects the non-negotiable rule that the policy engine, not scenario data or Python T03 code, will be the judge in later tasks.

### test_agent_simulator_emits_one_raw_tool_call_per_scenario_in_order
- **Traces to:** MASTER_SPEC.md §3 logical architecture; TASK_LEDGER.md T03 Goal and Done when; Architect Brief implementation objective.
- **Input:** Use the agent simulator public API, such as `iter_scenario_tool_calls()` or the implementer's equivalent documented iterator.
- **Expected outcome:** The simulator yields exactly six plain `dict` raw tool calls, one per canonical scenario, in scenario-number order.
- **Notes:** The test should assert public behaviour only. It should not require a specific internal data structure beyond the public scenario catalog and emitted dictionaries.

### test_agent_simulator_raw_calls_have_later_normalisation_fields
- **Traces to:** MASTER_SPEC.md §5.1 Action schema; TASK_LEDGER.md T03 Goal; Architect Brief raw tool-call guidance.
- **Input:** Every raw tool call emitted by the agent simulator.
- **Expected outcome:** Each raw call includes stable, obvious fields sufficient for later normalisation, including tool name, target system, actor/agent identity or equivalent actor metadata, resource/customer identifier, action type or tool-call kind, scenario identifier, parameters, and enforcement mode. Email raw calls include recipient/body fields; payment raw calls include amount/currency fields.
- **Notes:** This is intentionally a raw-call contract test, not a Pydantic Action schema validation test. Full normalisation is T04.

### test_sdk_wrapper_logs_intercepted_before_execution_for_each_call
- **Traces to:** MASTER_SPEC.md §1 item 1; §3 PEP; TASK_LEDGER.md T03 Done when and Verify; Architect Brief required exact phrase.
- **Input:** Pass each simulator-emitted raw tool-call dictionary through `SDKWrapper.call_tool()` or the implementer's equivalent public wrapper API while capturing stdout/stderr/log output with pytest facilities.
- **Expected outcome:** For each of the six calls, the captured output/log contains the exact phrase `intercepted before execution`.
- **Notes:** The phrase must appear once per intercepted call in the test loop so the ledger Verify step can visibly demonstrate interception.

### test_sdk_wrapper_forwards_raw_call_unchanged_to_placeholder_pipeline
- **Traces to:** MASTER_SPEC.md §3 logical architecture; TASK_LEDGER.md T03 Goal; Architect Brief placeholder downstream function requirement.
- **Input:** Pass representative payment and email raw-call dictionaries through the SDK wrapper.
- **Expected outcome:** The wrapper returns a dictionary equal to the original raw call, or a wrapper response whose documented echoed raw-call payload is exactly equal to the original raw call. The original raw-call dictionary must not be mutated.
- **Notes:** The downstream pipeline entry point in T03 must be visibly temporary and limited to echoing. It must not add policy decisions, approvals, audit records, or execution results.

### test_sdk_wrapper_does_not_report_business_execution_before_forwarding
- **Traces to:** MASTER_SPEC.md §1 item 1; §3 PEP; TASK_LEDGER.md T03 Reviewer focus; Architect Brief non-negotiable that the wrapper must not execute or pretend to execute the underlying business action before forwarding.
- **Input:** Pass payment and email raw calls through the SDK wrapper and inspect the returned payload plus captured logs/output.
- **Expected outcome:** The wrapper output/log demonstrates interception and forwarding only. It must not contain success messages or fields implying the payment was issued, the email was sent, a decision was enforced, an approval was created, or an audit record was written.
- **Notes:** This is a functional acceptance check for the PEP demo claim: execution cannot proceed without interception.

### test_verify_loop_prints_six_intercepted_raw_calls
- **Traces to:** TASK_LEDGER.md T03 Verify; Architect Brief Verify step.
- **Input:** Run the implementer's supported module/script entry point, preferably `python -m app.pep.agent_simulator` inside the app environment, or run the documented inline loop over simulator calls and `SDKWrapper`.
- **Expected outcome:** The command exits successfully, prints six raw-call representations, and includes the phrase `intercepted before execution` six times.
- **Notes:** This may be implemented as a subprocess-style pytest acceptance test if practical. If Docker is not available inside pytest, the test may invoke the module with the local Python interpreter while the final manual Verify still uses the ledger command.

## Coverage checklist
- [x] Happy path covered: all six canonical scenarios emit and are intercepted.
- [x] Error/edge cases covered: no extra scenarios, no missing planted phrases, no semantic email content in payment scenarios, no accidental executable decision fields in raw calls, no mutation during wrapper forwarding.
- [x] Spec non-negotiables verified: PEP interception before execution, policy decisions not encoded in Python/raw calls, payment path remains semantic-layer-free, planted content and fixture IDs preserved.
- [x] Real dependencies flagged (no mocks where forbidden): T03 has no required OPA, Presidio, or Postgres dependency. Tests should not mock those systems because they are out of scope; they also should not introduce fake policy/sensor/audit behaviour.

## Gaps or ambiguities
- TASK_LEDGER.md requires a script that loops the six scenarios and prints each intercepted raw call, but it does not mandate the exact command. The Architect Brief permits either `docker compose run --rm app python -m app.pep.agent_simulator` or an inline Python loop. The Implementer should document which command is supported and use it consistently in verification.
- The exact raw tool-call field names are intentionally not fixed until T04 normalisation. Tests should assert the presence of stable business meaning (tool, target system, customer/resource, amount or recipient/body, enforcement mode) without over-constraining implementation-specific names beyond what the Implementer documents as the public T03 contract.