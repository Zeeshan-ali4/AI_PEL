# QA Brief — T27: "Evidence gap" contrast page + demo Beat 0

## Scope verified
Implementation at `dfd8194` (T27 add evidence gap contrast page), reviewer-approved at `8cae3c7`.

## Test execution
- `pytest tests/T27_evidence_gap/` → **8 passed, 0 failed** (cold render, paired-points count ≥5, field/page-backed "with AI PEL" claims, live-link to `/scenarios` returns 200 with real content, nav link present on `/` and `/evidence-gap`, Beat 0 inserted before Beat 1 with correct framing, beat numbers sequential 0–10 with no gaps/duplicates, Beat 0 under word ceiling and free of new demo-flow steps).
- Full repo suite: `2 failed, 174 passed, 103 skipped, 4 errors`. All failures/errors are pre-existing and infra-related (no live Postgres/OPA service in this sandbox — `tests/test_policy_decisions.py` needs OPA+Postgres; `tests/T15_scenarios_ui` failures predate this task). None touch T27 files. Confirmed via `grep` that no T27-owned file (`evidence_gap.html`, the `/evidence-gap` route, `base.html` nav block, `DEMO_SCRIPT.md`) is implicated in any failing test.

## Manual verification against TASK_LEDGER.md Done-when criteria
1. `/evidence-gap` renders 6 paired without/with contrast rows (exceeds the 5-pair minimum) — confirmed by reading `app/web/templates/evidence_gap.html`.
2. Nav link present in `base.html` shared block (`href="/evidence-gap"`, label "Evidence Gap") — rendered on every page that extends `base.html`.
3. "With AI PEL" side links to live, working, cold-populated pages: `/scenarios` and `/audit` — both real routes, not dead links or fabricated record URLs.
4. `DEMO_SCRIPT.md` has `## Beat 0 — Evidence gap framing` ahead of `## Beat 1 — Dashboard calm`; beats run sequentially `0` through `10` with no gaps or duplicates.

## Coverage against PM/BA Test Brief
All 7 specified test cases in `briefs/T27_test_brief.md` are implemented and passing: cold render, ≥5 paired points, field/page-anchored claims, live link to a working populated page, global nav presence, Beat 0 insertion + framing, sequential beat numbering, and Beat 0 brevity/no-new-demo-flow check.

## Issues
None blocking. Same sandbox limitation noted by the Reviewer (no live OPA/Postgres) affects unrelated pre-existing tests only.

## Verdict
**PASS.** T27 meets all Done-when criteria and TASK_LEDGER.md Verify step. Recommend marking `DONE`.
