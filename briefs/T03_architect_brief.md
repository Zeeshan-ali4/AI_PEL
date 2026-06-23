# Architect Brief — T03: Scenarios + agent simulator + SDK wrapper (PEP)

## Task selected
- Task: T03 — Scenarios + agent simulator + SDK wrapper (PEP)
- Current status: To do
- Dependencies checked: pass — T03 depends on T02, and `TASK_LEDGER.md` marks T02 as Done. T01 is also Done, satisfying T02's dependency chain.

## Source-of-truth references
- MASTER_SPEC.md: §1 item 1 (agent actions are intercepted before execution through the SDK wrapper PEP); §2 (model is not the judge, deterministic policy later, payment scenarios skip semantics later); §3 logical architecture (`Agent simulator` → `SDK wrapper = Policy Enforcement Point (PEP)` → downstream pipeline); §5.1 Action schema context for raw call fields that later normalisation must preserve; §7 six narrative scenarios and planted confidence phrases; §8 enforcement modes only as values carried by scenario/raw calls, not enforced in this task; §10/§12 only insofar as later tests and acceptance criteria depend on the six scenarios remaining stable.
- TASK_LEDGER.md: T03 only — goal, dependency on T02, allowed files, done criteria, verify step, and reviewer focus.
- AGENTS.md: work on exactly one task; do not start the next task; touch only files listed for T03 plus the test file specified by the PM/BA Test Brief; preserve schemas, directory layout, control IDs, scenario outcomes, and policy logic; every task must produce committed pytest tests in the task test subfolder.

## Allowed files
- `scenarios/scenarios.py`
- `app/pep/agent_simulator.py`
- `app/pep/sdk_wrapper.py`
- `tests/T03_scenarios/`
- `briefs/T03_architect_brief.md`

## Implementation objective
Encode the six canonical demo scenarios from `MASTER_SPEC.md` §7 as stable scenario data, provide an agent simulator that emits one raw tool-call dictionary per scenario, and provide an SDK wrapper that makes the Policy Enforcement Point unmistakable by intercepting each raw tool call before any simulated execution can occur. Because the full pipeline is not implemented until T13, the wrapper should hand the intercepted raw call to a clearly named placeholder pipeline entry point that echoes the raw call unchanged.

The implementation should make two demo claims obvious in code and tests:

1. The agent does not execute tools directly; it emits a raw request that must pass through the SDK wrapper first.
2. The SDK wrapper logs the exact phrase `intercepted before execution` and forwards a raw tool-call dictionary downstream.

## Non-negotiables
- Implement exactly T03. Do not implement normalisation, context resolution, semantic evidence, OPA policy, enforcement, audit writes, UI, or any T04+ behaviour.
- Scenario data must cover exactly the six scenarios in `MASTER_SPEC.md` §7 and must preserve their expected outcomes/control intent as metadata or comments only, not as executable policy decisions.
- Scenario #1, #2, and #3 must include fixture customer IDs: `CUST-100`, `CUST-100`, and `CUST-300` respectively.
- Scenario #4 must include an external Gmail recipient/no disclosure-basis setup and planted email content containing an NHS number, a health condition, and the phrase `can't afford repayments`, so later deterministic stub logic can yield confidence `0.88`.
- Scenario #5 must include an external recipient and planted content containing the phrase `struggling a bit since losing my job`, so later deterministic stub logic can yield confidence `0.62`.
- Scenario #6 must represent an external known partner recipient and an email body with a customer name only; it must not include special-category or vulnerability planted phrases.
- Payment scenarios must not include email body content that would imply semantic-layer processing. The payment path must remain compatible with the later requirement that payment scenarios never invoke the semantic layer.
- Raw tool calls should be plain dictionaries suitable for later normalisation. Keep names stable and obvious, such as a tool name, target system, customer/resource identifiers, payment amount for payment scenarios, recipient/body fields for email scenarios, and `enforcement_mode` defaulting to a valid spec value such as `full` unless the PM/BA Test Brief narrows this.
- The SDK wrapper may use logging/printing for the required interception message, but it must not silently execute or pretend to execute the underlying business action before forwarding.
- The placeholder downstream function must be visibly temporary and limited to echoing the intercepted raw call. It must not encode policy, decisions, approvals, or audit records.
- Do not add new files outside the allowed list unless the human updates the task scope. If package imports require missing `__init__.py` files outside the allowed list, stop and ask rather than creating them.

## Verify step
Run the T03 ledger verify step by executing a script or module that loops over all six scenarios and prints each intercepted raw call. The command may be one of these, depending on the implementer's module design:

```bash
docker compose run --rm app python -m app.pep.agent_simulator
```

or

```bash
docker compose run --rm app python - <<'PY'
from app.pep.agent_simulator import iter_scenario_tool_calls
from app.pep.sdk_wrapper import SDKWrapper

wrapper = SDKWrapper()
for raw_call in iter_scenario_tool_calls():
    print(wrapper.call_tool(raw_call))
PY
```

The output must show six intercepted raw calls and include the phrase `intercepted before execution` for each call. The PM/BA Test Brief must also specify a pytest target under `tests/T03_scenarios/`; the Implementer must create and pass those tests.

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T03_architect_brief.md and briefs/T03_test_brief.md. Implement exactly T03. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
