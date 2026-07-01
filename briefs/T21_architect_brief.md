# Architect Brief — T21: README + demo script (narration)

## Task selected
- Task: T21 — README + demo script (narration)
- Current status: To do
- Dependencies checked: pass — `TASK_LEDGER.md` marks all T21 dependencies as `Done`: T19, T22, T23, T24, and T25.

## Source-of-truth references
- MASTER_SPEC.md: §1 (what the demo proves and deliberately not in scope), §1A (Head of Risk and Assurance value pillars), §1B (sensitivity/framing guidance), §3 (logical architecture), §5.5 (hash-chained audit records), §6 (control library, decision precedence, configurable threshold), §7 (scenario outcomes), §8A (assurance UI), §9 (demo flow/auditable surface), §12 (acceptance criteria), §14 (deployment guidance for data-sensitive buyer).
- TASK_LEDGER.md: T21 task block, including the ten required demo beats, the three minor UI/runtime additions called out in the notes, the `Done when` criteria, and the T21 verify step.
- AGENTS.md: work on exactly one task; `MASTER_SPEC.md` wins over conflicts; touch only files allowed for the task; do not silently change schemas, layout, control IDs, scenario outcomes, or policy logic; every task must produce committed pytest tests under `tests/`; stubs must be visibly labelled; the model is not the judge; OPA/Rego is the binding policy judge.

## Allowed files
T21's ledger file list names only:
- `README.md`
- `DEMO_SCRIPT.md`

The ledger also explicitly says the following three minor additions are to be implemented during T21 if not already present. To avoid silent scope drift, the Implementer must first inspect whether each capability already exists. If it already exists, do not touch its code; document the existing owner in the handoff. If it is missing, the T21 ledger text authorises only the minimum necessary edits to the existing files that already own that behaviour:
- Dashboard aggregate stats cards: likely `app/web/routes.py`, `app/web/templates/dashboard.html`, and the PM/BA-specified test files under `tests/T21_readme_demo/`.
- Shadow-mode decision callout: likely the existing decision/record/event-feed template that renders decisions, plus `tests/T21_readme_demo/`.
- One-shot OPA failure simulation: likely `app/settings_store.py`, `app/opa_client.py`, `app/web/routes.py`, one existing settings or event-feed template, and `tests/T21_readme_demo/`.

Do not create new product files unless the existing codebase has no appropriate owner for a required T21 behaviour. If a required change appears to need any schema change, policy/Rego change, new persistent table, new service, new scenario outcome, or broad route/layout refactor, stop and ask for a ledger/spec update before proceeding.

Always allowed by AGENTS.md for this task:
- `tests/T21_readme_demo/__init__.py`
- `tests/T21_readme_demo/test_*.py`

## Implementation objective
Produce the final public-facing README and spoken demo narration for the Head-of-Risk-and-Assurance buyer, and ensure the app supports the exact ten-beat demo path described in T21. The README must let a stranger run the demo with `docker compose up` and understand what is real, what is stubbed, what the architecture does, and what each scenario proves. `DEMO_SCRIPT.md` must read like a 12–15 minute assurance story rather than engineering notes: calm operational visibility, routine operation, enforcement, human oversight, semantic evidence, shadow mode, risk-owned policy controls, confidence threshold tuning, audit integrity, and fail-closed behaviour.

## Non-negotiables
- Work only on T21. Do not start T20 or any other task.
- Preserve all schemas, policy decisions, control IDs, scenario outcomes, enforcement-mode semantics, audit-chain semantics, and file layout from `MASTER_SPEC.md`.
- The README must include an explicit real-vs-stubbed honesty list:
  - Real: Presidio deterministic sensor; OPA/Rego policy engine; Postgres-backed append-only, SHA-256 hash-chained audit store; configured controls/settings that affect policy input.
  - Stubbed/fixture/demo-only: MCP interception; enterprise connectors/context; nuance model stub; production auth/multi-tenancy/scale; illustrative framework mappings/control packs; any simulated one-shot OPA failure control.
- The demo script must include the ten beats from `TASK_LEDGER.md` in exactly this order: dashboard calm; routine live feed; enforcement live feed; human oversight; semantic evidence; shadow mode; policy control; confidence threshold; audit integrity; fail closed.
- Scenario outcomes must match `MASTER_SPEC.md` §7 exactly:
  - Scenario 1: `allow`, no triggered control.
  - Scenario 2: `escalate`, `FIN-PAY-002`, required approval role `finance_supervisor`.
  - Scenario 3: `block`, `FIN-PAY-001`.
  - Scenario 4: `escalate`, `COMM-EMAIL-001`, required approval role `data_protection_approver`, stub confidence 0.88.
  - Scenario 5: `escalate`, `COMM-EMAIL-002`, required approval role `vulnerable_customer_team`, stub confidence 0.62 at default threshold 0.75; at threshold 0.60 it flips to `allow_with_logging`.
  - Scenario 6: `allow_with_logging`, `COMM-EMAIL-003`.
- Payment scenarios must not invoke the semantic layer. Email evidence is evidence only; the model/stub is not the judge; OPA/Rego returns the binding decision.
- Shadow mode must be narrated and rendered honestly: the action executes because enforcement mode is shadow, while the record still shows the decision that would have applied in full enforcement.
- Fail-closed simulation must be one-shot and auto-reset. It must not require stopping OPA for the whole demo and must not create a persistent unsafe failure mode.
- Do not use Horizon as a hook, do not mention Horizon, and do not cite Horizon Inquiry recommendation numbers.
- Label framework mappings as illustrative/demo mappings, not certified production mappings.
- Tests must include real pytest checks for README/script content and any T21 code additions or pre-existing support behaviours relied on by the script. Documentation-only inline checks are not enough.

## Verify step
From `TASK_LEDGER.md`: follow the README on a clean checkout; run the demo from the script, hitting every beat; confirm shadow mode renders clearly; confirm fail-closed simulation works and auto-resets; confirm aggregate stats update after running scenarios.

Minimum programmatic checks for Implementer/QA:
- `docker compose run --rm app pytest -q tests/T21_readme_demo`
- `python -m pytest -q tests/T21_readme_demo` may be used as a faster local smoke check when dependencies are already installed, but the Docker command remains the ledger-aligned check.
- If T21 touches runtime code, also run the relevant existing focused tests for the touched areas and, where practical, `docker compose run --rm app pytest -q`.

Manual demo verification checklist:
1. Start with `docker compose up --build` using only README instructions and open the documented app URL.
2. Confirm dashboard aggregate stats and controls/modes/framework chips are visible and update after scenario runs.
3. Run low-risk live-feed scenario #1 or #6 and confirm background events are green/neutral and audit records are written.
4. Run #3 and confirm focal event blocks with `FIN-PAY-001`; trace shows each pipeline stage.
5. Run #2 and confirm escalation, approval badge increment, enriched queue item, and append-only approval with reason.
6. Run #4 and confirm Presidio/stub evidence is visible while OPA is clearly the decision-maker.
7. Switch controls to shadow mode, re-run #3, and confirm executed-shadow/would-have-blocked messaging; restore full mode and confirm block.
8. Disable and re-enable `FIN-PAY-002`; change its threshold 500 → 1000 → 500 and confirm #2 decision changes accordingly.
9. Change semantic threshold 0.75 → 0.60 and confirm #5 flips from `escalate` to `allow_with_logging`; restore 0.75.
10. Verify audit chain, simulate tampering, confirm red broken link/mismatched hashes, and download audit package.
11. Trigger one-shot policy engine failure, confirm next event returns `fail_closed` with policy-engine-unreachable messaging, and confirm the following event runs normally.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T21_architect_brief.md` and `briefs/T21_test_brief.md`. Implement exactly T21. Touch only `README.md`, `DEMO_SCRIPT.md`, the T21 test files, and the minimum existing runtime/template files needed for the three T21 ledger-authorised demo-support additions if they are missing. Do not start any other task. Report changed files and verification result.
