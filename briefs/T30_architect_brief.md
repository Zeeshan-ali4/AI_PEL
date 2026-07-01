# Architect Brief — T30: Reporting dashboard summary view

## Task selected
- Task: T30 — Reporting dashboard summary view
- Current status: TODO (promoted from Backlog; spec addendum written as part of this brief — MASTER_SPEC.md v1.3)
- Dependencies checked: **PASS** — T28 (DONE), T29 (DONE)

## Source-of-truth references
- MASTER_SPEC.md §8B — new section added in v1.3; defines the page layout, period selector, five required sections, acceptance criteria, and the "no new schema" constraint
- MASTER_SPEC.md §8A — UI tone (calm, assurance dashboard), labelling conventions (illustrative disclaimer), accessibility requirements
- MASTER_SPEC.md §10 — canonical file layout; `app/audit/reporting.py` and `app/web/templates/reporting.html` are now listed; `app/web/routes.py` and `app/web/templates/base.html` are existing files extended here
- TASK_LEDGER.md — T30 entry (files, done-when, verify step, reviewer focus)
- AGENTS.md — Golden rule 2 (touch only listed files); Golden rule 4 (no decision logic in Python); Golden rule 6 (spec-first — followed: MASTER_SPEC.md §8B was written before this brief was finalised)

## Allowed files
- `app/audit/reporting.py` — **new file**
- `app/web/templates/reporting.html` — **new file**
- `app/web/routes.py` — extend (add `/reporting` route and "Verify now" action)
- `app/web/templates/base.html` — extend (add "Reporting" nav link after "Audit")
- `tests/T30_reporting/__init__.py` — **new file**
- `tests/T30_reporting/test_reporting.py` — **new file** (or additional test files as needed)

> The `tests/` directory is always allowed per AGENTS.md. Do not create any other files.

## Implementation objective

Build a `/reporting` page that gives a Head of Risk a period-level summary of the gate's activity — something they can present upward or to a regulator — without adding any new schema fields or business logic.

The page has five sections (see §8B for full detail):

1. **Summary cards** — four KPIs: total evaluated, total allowed (allow + allow_with_logging), total escalated, total blocked (block + fail_closed).
2. **Decision breakdown table** — one row per decision type with count and percentage. Omit zero-count rows.
3. **Control activity table** — one row per control that fired in the period (ID, name from `controls.json`, tier, count, most-recent timestamp), ordered by count descending.
4. **Escalation resolution summary** — resolved vs pending count; compact pending list linking to the approval queue.
5. **Chain-integrity status** — last verify result + timestamp; "Verify now" button that runs `store.verify_chain()` and refreshes.

A `period` query param (`today` / `7d` / `30d` / `all`, default `30d`) scopes all sections.

## Architecture notes for the Implementer

### `app/audit/reporting.py`

Create a single public function:

```python
def get_report(session: Session, period: str) -> dict:
    ...
```

`period` maps to a `cutoff` datetime: `today` = start of UTC today, `7d` = now − 7 days, `30d` = now − 30 days, `all` = no cutoff (datetime.min). Use parameterised SQLAlchemy filter expressions — never string interpolation.

Return a plain dict (or a small dataclass) with keys: `summary`, `decision_breakdown`, `control_activity`, `escalation_summary`, `chain_status`. The route passes this dict directly as template context. No business logic here — aggregation only.

For the control name lookup: `controls.json` is already read elsewhere in the app (e.g. the dashboard route reads it from `opa/data/controls.json`). Follow the same pattern — load it once in the route handler and pass the name map into `get_report` or look it up in the route after calling `get_report`. Either is acceptable; pick whichever keeps `reporting.py` free of file I/O.

For escalation resolution: a pending escalation is an `EvidenceRecord` with `decision.decision == "escalate"` and no linked `approval_decision` record with the same `correlation_id`. Use a LEFT JOIN or subquery — do not load all records into Python and filter in memory.

For "Verify now": call `store.verify_chain()` (already exists from T12). Store the result and timestamp in the session or return it as a query response. The simplest implementation is a `GET /reporting/verify` endpoint that calls `verify_chain()` and redirects back to `/reporting?verified=1` with the result in a flash message or query param. Do not introduce a background task or WebSocket.

### `app/web/templates/reporting.html`

Extend `base.html`. Follow the visual conventions of `dashboard.html` and `audit.html` — Tailwind utility classes, calm colours, large readable type. Decision badge colours must match the existing colour scheme used on `decision.html` (green = allow, amber = escalate, red = block/fail_closed, blue = allow_with_logging).

Period selector: a simple `<form method="get">` with a `<select name="period">` and four `<option>` values. Submitting the form reloads the page with the new param.

Empty state: if no records exist for the selected period, show a calm "No actions evaluated in this period" message in each section rather than leaving sections blank or erroring.

### `app/web/templates/base.html`

Add a "Reporting" nav link after the existing "Audit" link, following the same markup pattern as the other nav items.

### `app/web/routes.py`

Add:
- `GET /reporting` — load settings/session, call `get_report`, load `controls.json` for name lookup, render `reporting.html`
- `GET /reporting/verify` — call `store.verify_chain()`, redirect to `/reporting` with result in query params (e.g. `?chain_ok=true&chain_count=42` or `?chain_ok=false&chain_broken_at=<id>`)

Do not add a separate POST endpoint. The "Verify now" button is a `<form method="get" action="/reporting/verify">`.

## Non-negotiables
- No new fields on `EvidenceRecord` or any other schema — read-only aggregation over existing rows.
- `reporting.py` contains only SQLAlchemy aggregate queries — no policy logic, no scenario-number special-casing, no hardcoded control names.
- Control names come from `controls.json`, not hardcoded strings.
- Period filter uses parameterised queries (SQLAlchemy filter expressions), never f-string or `%`-style SQL interpolation.
- "Verify now" calls the existing `store.verify_chain()` — do not reimplement the chain logic.
- UI labelling: include "Illustrative period summary — covers actions evaluated by this demo deployment." at the top of the page.
- Decision colours must match the existing scheme used in `decision.html` and `event_feed.html`.
- Empty states must be handled gracefully (no 500 errors when no records exist).
- Touch only the six files/paths listed above. Do not create any other files.
- The `tests/` directory is always allowed.

## Verify step

From TASK_LEDGER.md T30:

1. Run all six scenarios via the scenario runner (or `/run/1` through `/run/6`).
2. Open `/reporting`. Confirm all five sections render with correct counts matching the scenarios run.
3. Change the period selector to `today`, `7d`, `30d`, `all`. Confirm counts update correctly.
4. Click "Verify now". Confirm a real chain-check result appears (green/red, count or broken record ID).
5. Run the scenario for #2 (escalation). Open `/reporting`. Confirm pending escalation count is 1. Approve it in the approval queue. Return to `/reporting`. Confirm it now shows resolved.
6. Run `pytest tests/T30_reporting/ -v` and confirm all tests pass.

## Handoff to Implementer

You are the Implementer Agent. Read `briefs/T30_architect_brief.md` and `briefs/T30_test_brief.md`. Implement exactly T30. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.