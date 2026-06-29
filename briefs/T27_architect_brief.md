# Architect Brief — T27: "Evidence gap" contrast page + demo Beat 0

## Task selected
- Task: T27 — "Evidence gap" contrast page + demo Beat 0
- Current status: To do
- Dependencies checked: pass — T27 depends on T19 only, and T19 is marked Done in `TASK_LEDGER.md`.

## Source-of-truth references
- MASTER_SPEC.md: §1 "What the demo proves"; §1A "Risk & Assurance buyer proof-points"; §8A "UI / UX for assurance"; §9 "Log the gate, not the agent". These sections define the assurance framing, the evidence/integrity claims the UI may make, and the requirement to be honest about what the demo evidences.
- TASK_LEDGER.md: T27 task definition, including allowed files, done criteria, verify step, and reviewer focus. Dependency note confirms T27 depends only on T19.
- AGENTS.md: Work exactly one task at a time; touch only the task's listed files plus tests; do not change schemas, control IDs, policy logic, scenario outcomes, or directory layout; every task must produce committed pytest tests under its task test folder.

## Allowed files
- `app/web/templates/evidence_gap.html` — new static contrast page.
- `app/web/routes.py` — add a `GET /evidence-gap` route only.
- `app/web/templates/base.html` — add a navigation link to the evidence-gap page.
- `DEMO_SCRIPT.md` — add new Beat 0 before the existing dashboard-calm beat and keep beat numbering/cross-references consistent.
- `tests/T27_evidence_gap/` — create the task test package and pytest tests for this task.

## Implementation objective
Add a concise, server-rendered evidence-gap contrast page that frames the demo before the dashboard is shown. The page should compare the evidence picture **without** a deterministic policy/enforcement layer against the evidence picture **with AI PEL**, using at least five directly paired points. The "with AI PEL" side must point to concrete, already-built app surfaces or field names rather than vague claims. Add a global nav link so the page is reachable from any page, and update `DEMO_SCRIPT.md` with a new sub-minute Beat 0 that walks this contrast page before moving into the existing dashboard-calm beat.

## Non-negotiables
- Do not implement any schema, policy, pipeline, audit-store, scenario, or control-logic changes for T27. This is static/presentational framing over existing capabilities.
- Do not invent statistics, compliance outcomes, or assurance claims that are not immediately backed by the current demo. The tone must be matter-of-fact and regulator-literate, not salesy.
- The contrast must include at least five paired before/after points. Acceptable "without" pain points include: post-hoc-only visibility, implicit/non-standard decision semantics, context reconstruction after the fact, no tamper-evident chain of custody, no framework/control traceability, and unclear evidence sufficiency.
- The "with AI PEL" points must map to existing capabilities/fields/pages such as `/scenarios`, decision records, `decision.decision`, `decision.reason`, `context`, `evidence`, `record_hash`, `prev_hash`, framework mappings, approvals, or audit-chain verification.
- At least one link from a "with AI PEL" point must navigate to a real existing page that works without a prior scenario run. Prefer `/scenarios` for the cold-start live link because it is a populated, already-built surface.
- Do not link to a fabricated example record hash. A record-view link is only acceptable if the route can be backed by an existing record at render/test time without brittle fixture assumptions; otherwise link to existing durable pages such as `/scenarios`, `/audit`, or `/settings`.
- Preserve the existing UI style and base template conventions. Add only the minimum route/template/nav changes needed for T27.
- `DEMO_SCRIPT.md` must place Beat 0 before the existing dashboard-calm beat and update later beat headings/references so numbering remains internally consistent.
- Tests must be real pytest tests in `tests/T27_evidence_gap/`; include `__init__.py` and at least one `test_*.py` file.

## Verify step
Manual verification from `TASK_LEDGER.md`:

Open `/evidence-gap` cold. Click through to the linked live page and confirm it is a real, populated view, not a dead link. Read the updated demo script start-to-finish and confirm beat numbering is consistent throughout.

Required automated checks for this task:

- Run the T27 pytest folder, for example: `docker compose run --rm app pytest -q tests/T27_evidence_gap/`.
- Tests should cover that `/evidence-gap` renders successfully, contains at least five paired contrast points, includes a working nav/global link, includes at least one valid link to an existing live app page such as `/scenarios`, and that `DEMO_SCRIPT.md` contains Beat 0 with consistent subsequent beat numbering.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T27_architect_brief.md` and `briefs/T27_test_brief.md`. Implement exactly T27. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
