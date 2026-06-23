# Review Report — T03: Scenarios + agent simulator + SDK wrapper (PEP)

## Verdict
APPROVE

## Critical findings
- None

## Spec and ledger compliance
- Correct task only: yes
- Dependencies respected: yes (T01 and T02 both Done)
- Allowed files only: yes (7 files changed: `scenarios/scenarios.py`, `app/pep/agent_simulator.py`, `app/pep/sdk_wrapper.py`, plus 4 test files under `tests/T03_scenarios/`)
- `Done when` satisfied: yes — each scenario can be emitted and intercepted; the wrapper logs "intercepted before execution" and passes a raw tool-call dict onward
- `Verify` satisfied: yes — `python -m app.pep.agent_simulator` prints six intercepted raw calls with the required phrase; all 11 pytest tests pass
- Reviewer focus satisfied: yes — execution genuinely cannot proceed without passing through the wrapper; planted content matches §7 confidence expectations (NHS number + health + "can't afford repayments" for 0.88; "struggling a bit since losing my job" for 0.62)

## Product invariant checks
- Model is not judge: pass (no model invocation)
- OPA/PDP owns decisions: pass (no decisions made; expected outcomes are metadata only)
- Evidence has no decision fields: pass (not applicable — Evidence schema not touched)
- Fail-closed preserved: not applicable (no OPA/sensor integration in T03)
- Append-only audit preserved: not applicable (no audit writes in T03)
- Stubs labelled: pass (placeholder pipeline is clearly documented as temporary)
- Scenario outcomes preserved: pass (all six match §7 exactly)

## Required changes
None.

## Non-blocking notes
- Missing `__init__.py` in `app/pep/` and `scenarios/`. Imports work via implicit namespace packages currently but may need explicit init files for later tasks. The architect brief correctly instructs the implementer to stop and ask rather than create them outside allowed files — this can be addressed when T04 or later tasks need it.
- Scenario 5 body says "losing my job" in first person within a third-person sentence ("Pat Morgan told us they are struggling a bit since losing my job"). Minor grammatical inconsistency but functionally correct — the planted phrase "struggling a bit since losing my job" is present verbatim as required.