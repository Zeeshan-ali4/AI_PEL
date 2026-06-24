# Architect Brief — T15: Scenario runner + decision view

## Task selected
- Task: T15 — Scenario runner + decision view
- Current status: To do
- Dependencies checked: pass — T15 depends on T14, and T14 is marked Done in `TASK_LEDGER.md`. Upstream integration dependencies T03–T13 and UI base task T14 are also marked Done.

## Source-of-truth references
- MASTER_SPEC.md: §1 honesty principle and real-vs-stubbed demo framing; §2 model-is-not-judge / policy-engine-is-judge principles; §3 logical architecture and payment semantic-layer skip; §5.1–§5.5 schemas for Action, Context, Evidence, Decision, and Evidence Record; §6 control library, decision precedence, framework mapping labelling, and configurable threshold; §7 six narrative scenarios and exact expected outcomes; §8 enforcement modes; §8A items 2–3 for scenario runner and decision view requirements; §12 acceptance criteria for scenario decisions, payment semantic skip, and highlighted email evidence.
- TASK_LEDGER.md: T15 task block in Phase 3, including goal, dependency on T14, allowed files, done condition, verify step, and reviewer focus.
- AGENTS.md: work on exactly one task; touch only listed files plus tests; do not change schemas, control IDs, scenario outcomes, or policy logic; PM/BA must specify a committed pytest target under `tests/T15_scenarios_ui/`; Implementer must write feature code and test code; do not mark the task DONE.

## Allowed files
- `app/web/templates/scenarios.html`
- `app/web/templates/decision.html`
- `app/web/routes.py`
- `tests/T15_scenarios_ui/`

## Implementation objective
Add the server-rendered scenario runner and decision detail experience for exactly the six canonical scenarios. The scenario runner must present six readable cards with a Run action for each scenario. Running a scenario must trigger the already-integrated pipeline and open a decision view that makes the binding policy outcome easy for a risk/assurance audience to understand: headline decision colour, plain-English reason, triggering control, framework chips, resolved context, evidence used, labelled model-stand-in confidence, `threshold_used`, and escalation routing where applicable.

The implementation should reuse the existing FastAPI/Jinja2/Tailwind-CDN UI structure from T14 and the existing T13 pipeline endpoint behaviour. If adding HTML routes alongside the existing JSON `POST /run/{scenario_id}` endpoint, keep the JSON endpoint backward-compatible for T13 tests and integrations.

## Non-negotiables
- Do not alter scenario data, expected outcomes, schemas, OPA policy logic, control IDs, framework mappings, audit hash-chain behaviour, settings semantics, or enforcement decisions.
- The policy engine remains the judge. The UI must present evidence as evidence only, never as an allow/block authority.
- Render all six §7 scenarios and preserve the exact expected outcomes:
  - #1 payment £80 / CUST-100 → `allow`, no control.
  - #2 payment £850 / CUST-100 without approval → `escalate`, `finance_supervisor`, `FIN-PAY-002`.
  - #3 payment £200 / CUST-300 fraud flag → `block`, `FIN-PAY-001`.
  - #4 external email with NHS number, health condition, and affordability phrase → `escalate`, `data_protection_approver`, `COMM-EMAIL-001`, stub confidence `0.88`.
  - #5 external email with job-loss vulnerability phrase → `escalate`, `vulnerable_customer_team`, `COMM-EMAIL-002`, stub confidence `0.62` at default threshold.
  - #6 external partner email with customer name only → `allow_with_logging`, `COMM-EMAIL-003`.
- Payment decision views must explicitly show that the semantic layer was not invoked (`evidence.evaluated=false`) because payment scenarios intentionally skip semantics.
- Email decision views must show the Evidence panel with real Presidio detected entities and highlighted spans when spans are present. Scenario #4 must visibly show highlighted spans from the real sensor output.
- The nuance classifier/stub must be visibly labelled as a model stand-in / deterministic stub wherever confidence is displayed.
- The Decision view must display `threshold_used` from the Decision returned by OPA, not a hard-coded value.
- If a decision is `escalate`, show a prominent state such as `Sent to {required_approval_role} for human decision` and include a link to the approvals queue route that T16 will complete. It is acceptable if the linked approvals page itself is not implemented until T16, but the T15 decision view should make the human-oversight destination visible.
- Framework references must be labelled or phrased as illustrative mappings; do not cite Horizon Inquiry recommendation numbers.
- Do not create additional production files beyond the allowed files. Tests must live under `tests/T15_scenarios_ui/` as required by AGENTS.md.
- Keep the tone calm, readable, and assurance-focused rather than developer/debug oriented.

## Verify step
Manual ledger verify: click through all six scenarios; confirm every decision view is readable, decisions match §7, #4 renders highlighted spans, stub confidence is labelled, and payment scenarios show semantic layer not invoked.

Programmatic checks expected from downstream agents:
- Run the T15 pytest tests under `tests/T15_scenarios_ui/`.
- Run relevant existing route/pipeline tests to ensure the existing JSON `POST /run/{scenario_id}` endpoint remains compatible.
- If feasible in the local environment, exercise the app with TestClient or a browser-like request flow for the scenario list and each scenario run.

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T15_architect_brief.md and briefs/T15_test_brief.md. Implement exactly T15. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.