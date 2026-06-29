# Test Brief — T27: "Evidence gap" contrast page + demo Beat 0

## Spec references
- MASTER_SPEC.md: §1 "What the demo proves" — the page must frame pre-execution interception, normalised actions, bounded evidence, binding OPA decisions, enforcement, human routing, tamper-evident records, and visible controls without overstating the demo.
- MASTER_SPEC.md: §1A "Value pillars" — the page and Beat 0 should use assurance framing: human oversight, evidential reliability, demonstrable control operation, governed policy, and proportionate enforcement.
- MASTER_SPEC.md: §8A "UI / UX for assurance" — the page should behave as a risk-facing assurance surface rather than a developer/debug page.
- MASTER_SPEC.md: §9 "Log the gate, not the agent" — the contrast should emphasise structured gate evidence at decision time, not post-hoc reconstruction from agent logs.
- TASK_LEDGER.md: T27 acceptance criteria and Verify step — `/evidence-gap` renders at least five paired contrast points, nav link is present from any page, at least one "with AI PEL" point links to a live working page, and `DEMO_SCRIPT.md` has a new Beat 0 with consistent subsequent numbering/cross-references.

## Target test location
- Folder: `tests/T27_evidence_gap/`
- Suggested files:
  - `test_evidence_gap_page.py` — covers rendering, paired contrast content, non-salesy field/page-backed claims, and live app link behaviour.
  - `test_evidence_gap_navigation.py` — covers global nav availability from `/evidence-gap` and at least one existing page that extends `base.html`.
  - `test_demo_script_beat0.py` — covers Beat 0 insertion, sub-minute framing content, and consistent beat numbering/cross-reference references in `DEMO_SCRIPT.md`.

## Test cases

### test_evidence_gap_page_renders_cold
- **Traces to:** TASK_LEDGER.md T27 Done criteria 1 and Verify step; MASTER_SPEC.md §8A.
- **Input:** HTTP `GET /evidence-gap` against the FastAPI test client before running any scenarios or creating any audit records.
- **Expected outcome:** Response status is `200`; response HTML contains a clear page heading/title for the evidence gap contrast and does not require any pre-existing action record, approval, or audit row to render.
- **Notes:** This is a cold-start acceptance test. It must not depend on a seeded record hash or previous scenario execution.

### test_evidence_gap_contains_at_least_five_paired_without_with_points
- **Traces to:** TASK_LEDGER.md T27 Done criterion 1 and Key notes; MASTER_SPEC.md §1 and §9.
- **Input:** HTTP `GET /evidence-gap`.
- **Expected outcome:** The page exposes at least five directly paired contrast rows/items. Each pair has a "without a policy enforcement layer" side and a corresponding "with AI PEL" side. The without side should include concrete evidence-gap ideas such as post-hoc-only visibility, implicit/non-standard decision semantics, context reconstruction after the fact, lack of tamper-evident custody, unclear evidence sufficiency, or missing framework/control traceability.
- **Notes:** The Implementer may use stable test markers such as `data-testid="evidence-gap-pair"`, `data-testid="without-ai-pel"`, and `data-testid="with-ai-pel"` to make this functional test robust without asserting brittle copy.

### test_with_ai_pel_points_reference_existing_demo_surfaces_or_fields
- **Traces to:** TASK_LEDGER.md T27 Goal and Key notes; MASTER_SPEC.md §1, §1A, and §9.
- **Input:** HTTP `GET /evidence-gap`.
- **Expected outcome:** The "with AI PEL" side names concrete existing surfaces or field names rather than vague claims. Assertions should verify a representative set such as `/scenarios`, `/audit`, `decision.decision`, `decision.reason`, `context`, `evidence`, `record_hash`, `prev_hash`, `framework_mappings`, approvals, or audit-chain verification.
- **Notes:** Do not require every listed field, but require enough concrete references to prove the page is anchored to actual product evidence. The page must not claim certified compliance, production audit approval, or invented statistics.

### test_evidence_gap_live_link_points_to_working_populated_page
- **Traces to:** TASK_LEDGER.md T27 Done criterion 3 and Verify step; Architect Brief non-negotiable live-link requirement.
- **Input:** Parse links from `/evidence-gap`, select at least one "with AI PEL" link intended to demonstrate the live product surface, and request it using the test client.
- **Expected outcome:** At least one linked live page returns `200` and contains populated, durable content available without a prior scenario run. `/scenarios` is the preferred target because it should list the built-in scenarios cold. `/audit` or `/settings` are acceptable only if they render useful cold-start content and are not dead links.
- **Notes:** The test must fail if the only links are anchors, fabricated record URLs, or routes requiring a pre-existing audit record.

### test_global_nav_includes_evidence_gap_link_from_existing_pages
- **Traces to:** TASK_LEDGER.md T27 Done criterion 2; MASTER_SPEC.md §8A.
- **Input:** HTTP `GET /` and HTTP `GET /evidence-gap`.
- **Expected outcome:** Both pages include a global navigation link whose `href` is `/evidence-gap` and whose visible label clearly identifies the evidence-gap/contrast page. The link should be part of the shared navigation, not only inline body copy on the new page.
- **Notes:** If the app uses named routes in templates, the test should assert the rendered URL and label, not implementation details.

### test_demo_script_adds_beat0_before_dashboard_calm
- **Traces to:** TASK_LEDGER.md T27 Done criterion 4 and Key notes; MASTER_SPEC.md §1A.
- **Input:** Read `DEMO_SCRIPT.md` from disk.
- **Expected outcome:** The script contains `## Beat 0` before the dashboard-calm beat. Beat 0 directs the presenter to open or walk the evidence-gap page and includes the required framing idea: before looking at the system, state the evidence problem it solves, then move from the contrast page to structural evidence in the live demo.
- **Notes:** Assertions should allow wording variation but require the concepts "before we look at the system"/problem framing, the contrast page, and structural evidence rather than reconstructed evidence.

### test_demo_script_beat_numbers_are_sequential_and_references_consistent
- **Traces to:** TASK_LEDGER.md T27 Done criterion 4 and Verify step.
- **Input:** Read `DEMO_SCRIPT.md` from disk and parse Markdown headings matching `## Beat <number> — ...`.
- **Expected outcome:** Beat headings begin at `0`, increment by exactly `1` with no gaps or duplicates, and the former dashboard-calm section appears as Beat 1 after Beat 0. Any in-script references to beat numbers must refer to headings that exist after renumbering.
- **Notes:** This should catch accidental duplicate Beat 1 headings or stale references introduced by inserting Beat 0.

### test_demo_script_beat0_is_short_framing_not_new_demo_flow
- **Traces to:** TASK_LEDGER.md T27 Key notes and Reviewer focus; MASTER_SPEC.md §1A and §8A.
- **Input:** Read only the Beat 0 section from `DEMO_SCRIPT.md`.
- **Expected outcome:** Beat 0 is concise enough to be a sub-minute framing beat. A practical assertion is that the Beat 0 body stays under a modest word limit such as 170 words and does not introduce scenario execution steps, invented statistics, or new product claims outside the existing demo.
- **Notes:** The purpose is to keep the page as a framing device, not a sales slide or a replacement for later scenario beats.

## Coverage checklist
- [ ] Happy path covered: cold render of `/evidence-gap`, live link returns `200`, nav link appears, Beat 0 inserted correctly.
- [ ] Error/edge cases covered: no pre-existing records required, fabricated/dead links fail, duplicate/gapped beat numbering fails, overlong Beat 0 fails.
- [ ] Spec non-negotiables verified: bounded assurance framing, concrete field/page-backed claims, no invented statistics or unsupported compliance claims, no schema/policy/control/scenario changes required.
- [ ] Real dependencies flagged (no mocks where forbidden): no OPA/Presidio/Postgres decisions are introduced by T27; route tests may use the FastAPI test client and should not mock page routing. If an automated test follows a live app link, it should exercise the real route handler/template rather than a mocked response.

## Gaps or ambiguities
- The ledger says "with a link into a live scenario run" while the Architect Brief prefers `/scenarios` as the durable cold-start link and warns against fabricated record links. For acceptance tests, treat `/scenarios` as satisfying the live-link requirement when it renders the built-in scenario runner cold; do not require a pre-run decision record link.
- The task does not prescribe exact copy or markup for paired contrast points. Tests should prefer stable semantic markers or resilient text assertions rather than brittle full-copy matching.
