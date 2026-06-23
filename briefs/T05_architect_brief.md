# Architect Brief — T05: Context resolver + fixtures

## Task selected
- Task: T05 — Context resolver + fixtures
- Current status: To do
- Dependencies checked: pass — T05 depends on T04, and `TASK_LEDGER.md` marks T04 as `Done`. T01, T02, and T03 are also marked `Done`, so the schema, scenario, simulator, SDK wrapper, and normaliser prerequisites are present.

## Source-of-truth references
- MASTER_SPEC.md: §3 logical architecture places the Context resolver after the Action normaliser and before the semantic evidence layer; §5.2 defines the exact Context schema; §6 defines the policy controls that consume context; §7 defines the six scenario fixture expectations and intended decisions; §11 step 3 requires `resolve()` to return Context and set `context_resolution_ok=false` on failure.
- TASK_LEDGER.md: T05 goal, dependencies, allowed files, key notes, done-when, verify step, and reviewer focus.
- AGENTS.md: work on exactly one task at a time; `MASTER_SPEC.md` wins over all other docs; touch only files listed for the current task; every task must produce pytest tests under its task test folder; do not silently change schemas, directory layout, control IDs, scenario outcomes, or policy logic.

## Allowed files
- `app/context/fixtures.py`
- `app/context/resolver.py`
- `tests/T05_context/`

Tests are mandatory for this task. The PM/BA Test Brief must name a concrete target test file under `tests/T05_context/`, and the Implementer must create `tests/T05_context/__init__.py` plus real pytest tests in that folder. Do not modify schemas, scenarios, normaliser code, policy files, or any other application files for T05.

## Implementation objective
Build the fixture-backed Context resolver for the demo. Given a normalised `Action` from T04, the resolver must return an `app.schemas.context.Context` object matching `MASTER_SPEC.md` §5.2 and carrying fixture values that drive the six narrative scenario outcomes in §7 when later policy tasks are added.

The fixtures are deliberately not real enterprise connectors. Implement them as clearly labelled demo stand-ins for IAM/CRM/fraud/sanctions/payment-history/approval/disclosure-basis systems. The resolver should compose those fixture records into the canonical Context schema without making network calls or real system calls.

## Non-negotiables
- Preserve the exact Context schema from `MASTER_SPEC.md` §5.2 by instantiating the existing Pydantic models from `app.schemas.context`; do not add, remove, or rename schema fields.
- The fixtures must be visibly labelled as demo fixtures / stand-ins for enterprise systems.
- Scenario-driving fixture expectations:
  - Scenario 1 (`CUST-100`, £80 payment): normal clean customer; no fraud/sanctions/blocked status; payment history below control thresholds; no prior approval needed for the low amount; should later allow.
  - Scenario 2 (`CUST-100`, £850 payment): same clean customer but no approval, so context must expose `approval_state.has_approval=false`; the payment amount remains in `Action.parameters`, not Context; should later trigger FIN-PAY-002.
  - Scenario 3 (`CUST-300`, £200 payment): customer fixture must have `fraud_flag=true` so it later triggers FIN-PAY-001 block.
  - Scenario 4 (external Gmail email): recipient context must have `is_external=true`, `domain="gmail.com"`, and `approved_disclosure_basis=false`; should later combine with semantic evidence to trigger COMM-EMAIL-001.
  - Scenario 5 (external adviser email): recipient context must have `is_external=true` and preserve the scenario disclosure-basis value; should later combine with semantic evidence confidence 0.62 to trigger COMM-EMAIL-002 at default threshold.
  - Scenario 6 (known partner email): recipient context must have `is_external=true`, domain from the email, and `approved_disclosure_basis=true`; should later combine with personal-data evidence to trigger COMM-EMAIL-003 allow-with-logging.
- Set `affects_individual_financial_standing=true` for payment actions and `false` for email actions unless the spec is updated. Do not implement any policy decision based on this flag in Python.
- Set `business_hours` deterministically from fixtures or a simple documented demo default. Avoid time-flaky tests.
- Provide a clear way to force `context_resolution_ok=false` for the later fail-closed demo, without requiring callers to corrupt real fixture data. This can be a resolver argument or a sentinel fixture/action condition, but it must be explicit and tested.
- For unknown or missing required fixture records, return a valid Context with `context_resolution_ok=false` rather than silently fabricating a successful context. Required nested objects still need safe placeholder values so the Pydantic Context validates.
- Do not implement semantic evidence, OPA decisions, enforcement, audit writes, settings, or UI behaviour in T05.
- Do not put allow/block/escalate decision logic in the context resolver. Context is input evidence for policy, not the judge.

## Verify step
Ledger verify: run a script that prints resolved Context per scenario; spot-check `customer.fraud_flag` and `recipient.is_external`.

Recommended exact verification for this task after implementation:

```bash
docker compose run --rm app pytest -q tests/T05_context
```

Also run a small scenario-print check, for example:

```bash
docker compose run --rm app python - <<'PY'
from scenarios.scenarios import get_raw_tool_call
from app.normaliser.normaliser import normalise
from app.context.resolver import resolve

for number in range(1, 7):
    action = normalise(get_raw_tool_call(number))
    context = resolve(action)
    print(number, context.model_dump())
PY
```

Manual spot checks from the printed output:
- Scenario 3 has `customer.fraud_flag` set to `true`.
- Scenarios 4, 5, and 6 have `recipient.is_external` set to `true`.
- Forced failure path returns `context_resolution_ok=false` and still validates as a Context object.

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T05_architect_brief.md and briefs/T05_test_brief.md. Implement exactly T05. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
