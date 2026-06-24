# Architect Brief — T14: base.html + control dashboard (landing)

## Task selected
- Task: T14 — base.html + control dashboard (landing)
- Current status: TODO / To do in `TASK_LEDGER.md`
- Dependencies checked: PASS — T14 depends on T13, and T13 is marked Done. Current build state says Current task: T14, Last completed task: T13, Known blockers: none.

## Source-of-truth references
- MASTER_SPEC.md: §6 control library and decision tiers; §8 enforcement modes; §8A item 1 control dashboard requirements; §9 auditable-surface counter; §10 canonical file layout; §13 scope fences.
- TASK_LEDGER.md: T14 task entry under Phase 3 Assurance UI, including Done when / Verify / Reviewer focus.
- AGENTS.md: Work on exactly one task; touch only current-task files plus tests; preserve `MASTER_SPEC.md` as source of truth; every task must produce committed pytest tests under `tests/`.

## Allowed files
- `app/web/templates/base.html`
- `app/web/templates/dashboard.html`
- `app/web/static/`
- `app/web/routes.py` — routes for `/`
- `tests/T14_dashboard/`

## Implementation objective
Build the first server-rendered assurance UI surface: a calm board-ready landing dashboard at `/` using a shared Jinja2 layout. The dashboard must render the control library from `opa/data/controls.json`, show each control's ID, plain-English purpose, tier, current per-control enforcement mode from `SettingsStore`, framework mapping chips, and real live counts derived from the audit store. It must also expose an enforcement-mode toggle that persists through `SettingsStore`, plus the auditable-surface session counter described in `MASTER_SPEC.md` §9.

## Non-negotiables
- Do not implement T15+ pages, approval handling, export, audit tamper UI, or settings page scope.
- Do not change schemas, policy logic, scenario outcomes, OPA decisions, or audit hash-chain behaviour.
- Dashboard counts must be real audit-derived counts, not hard-coded demo numbers.
- Control metadata must come from `opa/data/controls.json`; do not duplicate framework mappings in templates or Python constants unless unavoidable for presentation-only labels.
- Per-control mode must be read from and persisted through `app/settings_store.py`; do not introduce a second settings source.
- The `/` route should replace the T01 placeholder with the dashboard; keep `/run/{scenario_id}` JSON endpoint working.
- Use Tailwind via CDN in `base.html`; no JS build step and no extra frontend tooling.
- Keep the tone accessible and assurance-focused: large readable type, calm language, no jargon-heavy developer dashboard copy.
- Any stubbed or illustrative element shown on the dashboard must be visibly labelled. Framework mappings should be labelled as illustrative mappings.
- Tests must be real pytest tests in `tests/T14_dashboard/`, including `__init__.py` and at least one `test_*.py`.

## Verify step
Ledger verify: open `/`; run a scenario; counts and counter update on refresh.

Recommended implementer checks:
- `docker compose up --build`
- Open `http://localhost:8080/` and confirm all controls render with framework chips, tier, current mode, live counts, and auditable-surface counter.
- Run one scenario via `curl -X POST http://localhost:8080/run/1`, refresh `/`, and confirm counts/counter reflect the new audit record.
- Change a control mode using the dashboard toggle, refresh `/`, and confirm the persisted mode remains visible.
- Run T14 pytest tests, e.g. `docker compose run --rm app pytest -q tests/T14_dashboard`.

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T14_architect_brief.md and briefs/T14_test_brief.md. Implement exactly T14. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.