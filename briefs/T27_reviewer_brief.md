# Reviewer Brief — T27: "Evidence gap" contrast page + demo Beat 0

## Scope checked
Diff range `fa2d0f3..dfd8194` against `briefs/T27_architect_brief.md` and `briefs/T27_test_brief.md`.

## Files touched (matches allowed list exactly)
- `app/web/templates/evidence_gap.html` (new)
- `app/web/routes.py` (`GET /evidence-gap` only, no other route logic changed)
- `app/web/templates/base.html` (one nav link added)
- `DEMO_SCRIPT.md` (new Beat 0, renumbered nothing else since old beats already started at 1 and shift up by zero — old Beat 1 stays Beat 1, content unchanged)
- `tests/T27_evidence_gap/` (`__init__.py`, `conftest.py`, `test_demo_script_beat0.py`, `test_evidence_gap_navigation.py`, `test_evidence_gap_page.py`)

No schema, policy, control-logic, audit-store, or scenario-outcome files were touched. No stray files outside the allowed list.

## Findings

### Contrast content
- 6 paired `data-testid="evidence-gap-pair"` rows, each with `without-ai-pel` / `with-ai-pel` sub-blocks — exceeds the 5-pair minimum.
- "Without" side: post-hoc-only visibility, implicit decision semantics, context reconstructed later, no chain of custody, unclear control traceability, thin human-oversight evidence. All match the architect brief's acceptable pain-point list.
- "With AI PEL" side anchors to real fields/pages: `/scenarios`, `decision.decision`, `decision.reason`, `control_id`, `threshold_used`, `context`, `evidence`, `/audit`, `record_hash`, `prev_hash`, `triggered_controls`, `framework_mappings`, `approval_decision`. No invented statistics or compliance claims — tone is matter-of-fact, consistent with reviewer focus.
- Live link requirement satisfied: `/scenarios` link is present and the route renders the built-in scenario list cold (verified by test and by reading `routes.py`).

### Navigation
- `base.html` adds a single `Evidence Gap` nav link with the existing active-state pattern, present on every page since it's in the shared nav block. Matches Done criterion 2.

### Demo script
- Beat 0 inserted before Beat 1 (Dashboard calm), narration matches the brief's suggested framing ("Before we look at the system...", "structural rather than reconstructed"), and stays short (well under the 170-word ceiling enforced by tests).
- Beat numbers 0–10 are sequential with no gaps or duplicates; no later cross-references needed renumbering since none referenced beat numbers by index.

### Tests
- `python3 -m pytest -q tests/T27_evidence_gap/` → 8 passed, 0 failed. Covers cold render, paired-points count, field/page anchoring, live-link behavior, nav presence on `/` and `/evidence-gap`, and Beat 0 structure/length/sequencing — matching the PM/BA Test Brief's seven scenarios.
- Full repo suite run for regression check: pre-existing unrelated failures only (`T15_scenarios_ui` assertions and `test_policy_decisions.py` errors due to missing `POSTGRES_PASSWORD` env in this sandbox) — not caused by this change; no T27 file is implicated.

### Reviewer focus item (no overclaiming)
No certification, audit-approval, or statistical claims found. Copy is scoped to what the demo actually shows. Reads as a one-minute framing device, not a sales slide.

## Issues
None blocking. One administrative gap: `TASK_LEDGER.md` T27 status is still `To do` despite implementation and tests being complete and passing — should be moved to `REVIEW`/`DONE` per the pipeline once QA signs off, per `AGENTS.md` ("Only mark a task DONE after the Verify step passes").

## Verdict
**Approve.** Implementation matches both briefs and `MASTER_SPEC.md` §1/§1A/§8A/§9 framing requirements. Ready to hand to QA.
