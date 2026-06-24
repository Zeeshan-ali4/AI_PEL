# Architect Brief — T21: README + demo script (narration)

## Task selected
- Task: T21 — README + demo script (narration)
- Current status: To do
- Dependencies checked: pass — T21 depends on T19, and T19 is marked `Done` in `TASK_LEDGER.md`. The ledger also shows T01–T19 complete enough for this documentation task. T20 remains `To do`, but T21 does not depend on T20.

## Source-of-truth references
- MASTER_SPEC.md: §1 (what the demo proves and real-vs-stubbed scope), §1A (Head of Risk & Assurance value pillars), §1B / §13 framing constraints (do not use Horizon as a hook or cite recommendation numbers; label stubs/illustrative mappings), §3 (logical architecture), §6 (control library and threshold), §7 (six narrative scenarios), §8 / §8A (enforcement modes and assurance UI), §9 (auditable surface counter), §10 (canonical file layout), §12 (acceptance criteria), §14 (deployment conversation framing).
- TASK_LEDGER.md: T21 goal, dependency, file list, done criteria, verify step, and reviewer focus under “PHASE 4 — Verify & present”.
- AGENTS.md: Work on exactly one task, touch only allowed files, do not create extra files unless explicitly allowed, preserve product rules, and do not start another task.

## Allowed files
- `README.md`
- `DEMO_SCRIPT.md`
- `tests/T21_readme_demo/` (allowed by AGENTS.md test responsibility rules; the PM/BA must specify the exact target test file path)

## Implementation objective
Update the README from its current scaffold form into the final user-facing project README, and create a standalone demo narration script for the Head-of-Risk-and-Assurance audience. The result must let a stranger understand what the product demonstrates, run it with Docker Compose, navigate the assurance UI, and deliver the six-scenario demo plus audit-chain tamper moment and threshold-change moment without needing undocumented context.

The README should be concise but complete:
- State what the demo is and whom it is for.
- Explain the assurance value before implementation detail.
- Document how to run the stack with `docker compose up` / `docker compose up --build`, including the app URL and key pages a user should visit.
- Summarise the architecture in one clear paragraph aligned to MASTER_SPEC.md §3.
- Include an explicit “What is real vs stubbed” honesty list: real Presidio sensor, real OPA/Rego policy engine, real Postgres-backed tamper-evident hash chain; stubbed/fixture items include MCP interception, enterprise connectors/context, nuance model, auth/multi-tenancy/production scale, and illustrative framework mappings/control packs.
- Summarise the six scenario outcomes exactly as MASTER_SPEC.md §7 defines them.
- Mention that payment scenarios intentionally skip the semantic layer, while email scenarios use evidence only; the model/stub is not the judge.
- Mention settings/threshold behaviour: default threshold 0.75, lowering to 0.60 flips Scenario 5 to `allow_with_logging`.
- Mention audit-chain verification and tamper simulation.

The demo script should be written as spoken narration, not engineering notes:
- Lead with assurance value, human oversight, evidential reliability, demonstrable control operation, risk-owned policy, and deterministic/proportionate enforcement.
- Walk through all six scenarios in order with the exact expected outcomes and controls from MASTER_SPEC.md §7.
- Include the tamper-evident audit chain moment: verify intact, simulate tampering, then show the named broken record.
- Include the threshold-change moment: at 0.75 Scenario 5 escalates; at 0.60 it allows with logging.
- Explicitly explain real vs stubbed components in honest buyer-safe language.
- Honour the sensitivity guidance: do not use Horizon as the hook, do not cite Horizon Inquiry recommendation numbers, and do not imply unsupported IT-control recommendations.

## Non-negotiables
- Work only on T21; do not implement features, change policy logic, change schemas, or start T20 or any other task.
- Do not edit files outside `README.md`, `DEMO_SCRIPT.md`, and the PM/BA-specified `tests/T21_readme_demo/` test files.
- README and script must not contradict MASTER_SPEC.md scenario outcomes, architecture, acceptance criteria, or real-vs-stubbed boundaries.
- Scenario outcomes must match MASTER_SPEC.md §7 exactly:
  - Scenario 1: `allow`, no control.
  - Scenario 2: `escalate` to `finance_supervisor`, FIN-PAY-002.
  - Scenario 3: `block`, FIN-PAY-001.
  - Scenario 4: `escalate` to `data_protection_approver`, COMM-EMAIL-001, stub confidence 0.88.
  - Scenario 5: `escalate` to `vulnerable_customer_team`, COMM-EMAIL-002, stub confidence 0.62 at threshold 0.75.
  - Scenario 6: `allow_with_logging`, COMM-EMAIL-003.
- Preserve the core product message: the model is not the judge; evidence is only evidence; OPA/Rego returns the binding decision; uncertainty escalates; fail-closed remains the safe default.
- Clearly label stubs, fixtures, and illustrative framework mappings. Do not overclaim production readiness.
- Do not use Horizon as a sales hook or cite Horizon Inquiry recommendation numbers.
- The PM/BA Test Brief must specify a concrete pytest file under `tests/T21_readme_demo/`; the Implementer must add real pytest coverage for the documentation content.

## Verify step
From `TASK_LEDGER.md`: follow the README on a clean checkout, then run the demo from the script.

Task-specific checks for Implementer/QA:
- Run `docker compose up --build` and confirm the documented app URL loads.
- Follow the README’s run instructions exactly as written.
- Use `DEMO_SCRIPT.md` to run through the six scenarios, approval/audit moments, tamper simulation, and threshold flip.
- Run the PM/BA-specified pytest file for T21 documentation checks, then run the task-level test command if provided in the test brief.

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T21_architect_brief.md and briefs/T21_test_brief.md. Implement exactly T21. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
