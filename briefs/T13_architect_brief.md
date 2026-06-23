# Architect Brief — T13: pipeline.py (INTEGRATION MILESTONE)

## Task selected
- Task: T13 — pipeline.py (INTEGRATION MILESTONE)
- Current status: To do
- Dependencies checked: pass — T13 depends on T03–T12, and TASK_LEDGER.md marks T03, T04, T05, T06, T07, T08, T09, T10, T11, and T12 as Done. Current build state also says current task is T13, last completed task is T12, and known blockers are none.

## Source-of-truth references
- MASTER_SPEC.md: §1 (what the demo proves), §2 (principles: model is evidence only, OPA is judge, fail closed), §3 (logical architecture), §5.1–§5.5 (Action, Context, Evidence, Decision, Evidence Record contracts), §6 (control library, precedence, threshold), §7 (six scenario outcomes), §8 (enforcement modes), §10 (canonical file layout), §11 (pipeline order), §12 (acceptance criteria), §13 (scope fences).
- TASK_LEDGER.md: Current build state; golden rules; T13 task block including goal, dependencies, files, key notes, done-when, verify step, and reviewer focus.
- AGENTS.md: Work on exactly one task; MASTER_SPEC.md wins conflicts; touch only listed task files plus required tests; do not change schemas, layout, control IDs, scenario outcomes, or policy logic; every task must produce pytest tests under the task test folder; do not mark DONE unless verification passes.

## Allowed files
- app/pipeline.py
- app/web/routes.py
- tests/T13_pipeline/

## Implementation objective
Wire the first full end-to-end integration path for the demo. A run of `POST /run/{scenario_id}` must take one of the six encoded scenarios through the existing SDK wrapper/interception flow, normalise the raw tool call into the canonical Action, resolve Context, build Evidence only when the Action is an email, load runtime settings, call OPA for the binding Decision, enforce that Decision under the Action/settings mode, append an audit EvidenceRecord, and return JSON containing the Decision plus the written record hash.

This task should integrate existing components from T03–T12, not reimplement their logic. Python may orchestrate and may produce `fail_closed` only for required failure paths already allowed by the spec, such as OPA unreachable or required context/sensor failure. Binding policy decisions must still come from OPA.

## Non-negotiables
- Work on T13 only. Do not start any UI task and do not broaden the endpoint beyond the JSON integration endpoint required here.
- Touch only `app/pipeline.py`, `app/web/routes.py`, and files under `tests/T13_pipeline/`.
- Preserve the exact canonical schemas from MASTER_SPEC.md §5. Do not add decision/enforcement fields to Evidence.
- Preserve scenario outcomes exactly as MASTER_SPEC.md §7:
  - Scenario 1: `allow`, no control.
  - Scenario 2: `escalate`, `finance_supervisor`, `FIN-PAY-002`.
  - Scenario 3: `block`, `FIN-PAY-001`.
  - Scenario 4: `escalate`, `data_protection_approver`, `COMM-EMAIL-001`.
  - Scenario 5: `escalate`, `vulnerable_customer_team`, `COMM-EMAIL-002` at the default threshold.
  - Scenario 6: `allow_with_logging`, `COMM-EMAIL-003`.
- Payment scenarios must not invoke the semantic layer. Their Evidence must have `evaluated=false`.
- Email scenarios must use the real Presidio path plus the clearly labelled deterministic `nuance_stub` through the existing evidence builder.
- Load runtime settings and pass `config.high_confidence_threshold` into OPA. The Decision must echo `threshold_used` as defined by the Decision schema.
- Every run must append an audit record regardless of decision, including block, escalate, and fail-closed outcomes.
- The audit write must use the T12 append-only store/hash-chain path. Do not mutate existing records.
- Enforcement must use the T11 handler/approval queue interfaces. Blocks do not go to the human queue; escalations do.
- Fail-closed paths must be reachable: context resolution failure, sensor error, or OPA failure must result in a written record with a `fail_closed` Decision.
- Do not hardcode final policy outcomes in `pipeline.py` or `routes.py`; outcomes must emerge from context/evidence/settings passed to OPA.
- Do not create new production files outside the canonical layout or additional helper modules for this task.

## Verify step
Run the ledger verify for T13:

```bash
curl -X POST http://localhost:8080/run/1
curl -X POST http://localhost:8080/run/2
curl -X POST http://localhost:8080/run/3
curl -X POST http://localhost:8080/run/4
curl -X POST http://localhost:8080/run/5
curl -X POST http://localhost:8080/run/6
```

Confirm each response includes the expected §7 Decision and a non-empty record hash, then verify the audit chain is intact using the T12 store verification path exposed or exercised by the T13 tests.

Also add and run pytest coverage in `tests/T13_pipeline/` that verifies at minimum:
- all six scenarios return the expected decision/control/approval role outcomes;
- every scenario writes a record with a hash;
- the audit chain verifies intact after the six runs;
- payment Evidence has `evaluated=false`;
- Scenario 5 flips from `escalate` to `allow_with_logging` when the threshold is lowered to `0.60`, if the existing settings/test infrastructure permits doing so without touching files outside T13 scope;
- at least one fail-closed path writes a record.

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T13_architect_brief.md and briefs/T13_test_brief.md. Implement exactly T13. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.