# Test Brief — T15: Scenario runner + decision view

## Spec references
- MASTER_SPEC.md: §1 honesty principle; §2 model-is-not-judge / policy-engine-is-judge; §5.1–§5.5 canonical schemas; §6 control library, framework mappings, decision precedence, and configurable threshold; §7 six narrative scenarios and exact expected decisions; §8A items 2–3 Scenario runner and Decision view; §12 acceptance criteria for scenario decisions, payment semantic skip, real Presidio evidence, and visible stub labelling.
- TASK_LEDGER.md: T15 goal, allowed files, done condition, verify step, and reviewer focus.
- Architect brief: `briefs/T15_architect_brief.md` non-negotiables and handoff constraints.

## Target test location
- Folder: `tests/T15_scenarios_ui/`
- Suggested files:
  - `test_scenario_runner.py` — covers scenario-list rendering and all six Run affordances.
  - `test_decision_view_scenarios.py` — covers end-to-end scenario run pages for all six canonical scenarios and asserts decisions, controls, approval routing, context, and framework chips.
  - `test_evidence_panel.py` — covers payment semantic-layer skip, email evidence display, highlighted spans, labelled deterministic stub confidence, threshold display, and evidence-as-evidence wording.

## Test cases

### test_scenario_runner_renders_six_canonical_cards
- **Traces to:** MASTER_SPEC.md §7; §8A item 2; TASK_LEDGER T15 goal.
- **Input:** Browser-like `GET` request to the scenario runner route implemented for T15.
- **Expected outcome:** Response status is 200 and HTML contains exactly the six canonical scenario entries: payment £80, payment £850, payment £200 fraud-flag customer, external email with NHS/health/affordability content, external email with job-loss vulnerability phrase, and external partner email with customer name only. Each card has a visible `Run` action targeting its scenario id (`1` through `6`).
- **Notes:** This is a UI acceptance test, not a unit test. It should use FastAPI `TestClient` or equivalent route-level testing and should not inspect private template helper internals.

### test_scenario_runner_uses_calm_assurance_copy_not_debug_copy
- **Traces to:** MASTER_SPEC.md §8A accessibility/tone; Architect brief reviewer focus.
- **Input:** `GET` request to the scenario runner route.
- **Expected outcome:** Page contains assurance-oriented copy such as scenario purpose/summary and avoids developer-only raw dumps as the primary content. The page should not expose Python object repr strings or unformatted JSON as the main scenario card content.
- **Notes:** The assertion can be textual and structural, e.g. card headings plus readable descriptions are present and obvious debug markers are absent.

### test_each_run_opens_decision_view_with_expected_outcome
- **Traces to:** MASTER_SPEC.md §7; §8A item 3; §12 “All six scenarios produce exactly the §7 decisions”; TASK_LEDGER T15 done condition.
- **Input:** For each scenario id `1` through `6`, submit the T15 UI Run action (or follow it with `TestClient`) so the full pipeline is invoked and the result page is rendered.
- **Expected outcome:** Each response status is 200 and the decision view shows the exact expected decision/control/role:
  - Scenario 1: `allow`, no triggering control.
  - Scenario 2: `escalate`, `FIN-PAY-002`, required approval role `finance_supervisor`.
  - Scenario 3: `block`, `FIN-PAY-001`.
  - Scenario 4: `escalate`, `COMM-EMAIL-001`, required approval role `data_protection_approver`.
  - Scenario 5: `escalate`, `COMM-EMAIL-002`, required approval role `vulnerable_customer_team` at the default threshold.
  - Scenario 6: `allow_with_logging`, `COMM-EMAIL-003`.
- **Notes:** Tests should exercise the real route/pipeline path. Do not mock OPA, Presidio, the settings store, or the audit write path if those dependencies are available in the test environment. If the existing test setup provides isolated real DB/OPA fixtures, use them.

### test_decision_view_shows_plain_reason_headline_and_colour_state
- **Traces to:** MASTER_SPEC.md §8A item 3; TASK_LEDGER T15 goal.
- **Input:** Run at least one scenario for each displayed decision family in T15 scope: scenario 1 (`allow`), scenario 2 (`escalate`), scenario 3 (`block`), and scenario 6 (`allow_with_logging`).
- **Expected outcome:** Each rendered decision view includes a prominent headline decision, a one-line plain-English reason from the Decision, and a visual state/class or accessible label that distinguishes allow, escalate, block, and allow-with-logging. The reason must not be hidden only inside raw JSON.
- **Notes:** Colour can be asserted through stable semantic class names/text if exact Tailwind classes are implementation-specific.

### test_decision_view_shows_triggered_control_and_framework_chips
- **Traces to:** MASTER_SPEC.md §6; §8A item 3; TASK_LEDGER T15 goal.
- **Input:** Run scenarios 2, 3, 4, 5, and 6.
- **Expected outcome:** For each controlled decision, the page displays the triggered control id and framework mapping chips/text from the Decision. Scenario 1 should clearly show that no control was triggered, rather than inventing a control. Framework references should be presented as mappings/illustrative assurance chips and must not cite Horizon Inquiry recommendation numbers.
- **Notes:** This verifies the UI does not alter control IDs or framework wording into unsupported claims.

### test_decision_view_displays_resolved_context_used
- **Traces to:** MASTER_SPEC.md §5.2 Context schema; §8A item 3.
- **Input:** Run one payment scenario and one email scenario, preferably scenarios 2 and 4.
- **Expected outcome:** The decision view includes a resolved-context section with material fields used for the decision, such as customer status/flags, approval state, payment history for payment, and recipient externality/disclosure basis for email. The section is readable and not only a raw JSON dump.
- **Notes:** The test should assert stable field labels and values relevant to the scenario decision.

### test_payment_scenarios_show_semantic_layer_not_invoked
- **Traces to:** MASTER_SPEC.md §3 payment semantic-layer skip; §5.3 `evaluated=false`; §12 payment scenarios never invoke semantic layer; TASK_LEDGER T15 done condition.
- **Input:** Run scenarios 1, 2, and 3.
- **Expected outcome:** Each payment decision view includes clear text such as `Semantic layer not invoked` and/or `evidence.evaluated=false`. It must not display Presidio entities or stub confidence as if semantic evidence had been evaluated for payments.
- **Notes:** This is a non-negotiable product rule: payment scenarios must not invoke the semantic layer.

### test_email_scenario_4_shows_real_presidio_entities_and_highlighted_spans
- **Traces to:** MASTER_SPEC.md §7 scenario 4; §8A item 3; §12 real Presidio evidence; TASK_LEDGER T15 done condition.
- **Input:** Run scenario 4.
- **Expected outcome:** Decision view contains an evidence panel with detected entities whose source is `presidio`, and the scenario body renders highlighted spans corresponding to `evidence_spans`. The page should show the planted NHS number / health-condition evidence as highlighted or otherwise visibly marked spans in context.
- **Notes:** Do not satisfy this with hardcoded entity text alone. The test should verify rendered output is driven from the Evidence object returned by the real pipeline and that spans are visually marked with semantic markup/classes.

### test_email_stub_confidence_is_labelled_as_deterministic_model_stand_in
- **Traces to:** MASTER_SPEC.md §1 honesty principle; §7 deterministic nuance stub; §8A item 3 and accessibility/tone; §12 visible stub labels.
- **Input:** Run scenarios 4 and 5.
- **Expected outcome:** Scenario 4 displays vulnerability/stub confidence `0.88`; scenario 5 displays `0.62`; both are visibly labelled as a deterministic stub, model stand-in, or equivalent wording. The label must appear near the confidence value, not only in a footer.
- **Notes:** The UI must never imply that the stub is a production model or binding decision-maker.

### test_decision_view_displays_threshold_used_from_decision
- **Traces to:** MASTER_SPEC.md §5.4 `threshold_used`; §6 configurable threshold; §8A item 3.
- **Input:** Run scenarios 4 and 5 with the default settings row.
- **Expected outcome:** Decision view displays the `threshold_used` value returned in the Decision. At default settings this should be `0.75` unless earlier tests deliberately changed settings. The value must be displayed as part of decision/evidence context.
- **Notes:** Tests should avoid asserting implementation internals. If a settings fixture changes the threshold, assert the rendered value equals the Decision payload’s `threshold_used`, not a hard-coded template constant.

### test_escalated_decisions_show_human_routing_and_approval_link
- **Traces to:** MASTER_SPEC.md §1A human oversight; §8A item 3; TASK_LEDGER T15 goal.
- **Input:** Run scenarios 2, 4, and 5.
- **Expected outcome:** Each escalated decision page prominently states `Sent to {role} for human decision` or equivalent, using the exact required role returned by the Decision. The page includes a link to the approvals queue route for the forthcoming T16 view.
- **Notes:** The approvals destination does not need to be implemented in T15, but the route/link target must be visible and stable enough for T16 to complete.

### test_evidence_panel_states_policy_engine_is_judge_not_model
- **Traces to:** MASTER_SPEC.md §2 model-is-not-judge; TASK_LEDGER T15 reviewer focus.
- **Input:** Run one email escalation scenario, preferably scenario 4 or 5.
- **Expected outcome:** Evidence panel includes wording that makes evidence subordinate to the policy decision, e.g. “Evidence informs the policy engine” or “model/stub is a sensor, not the judge.” The page must not label evidence as the approval/blocking authority.
- **Notes:** This is a functional acceptance requirement because T15’s reviewer focus is visual proof of the product principle.

### test_existing_json_run_endpoint_remains_backward_compatible
- **Traces to:** Architect brief implementation objective; TASK_LEDGER T13 compatibility risk.
- **Input:** `POST /run/{scenario_id}` for at least scenarios 1 and 4 using the existing JSON endpoint contract.
- **Expected outcome:** Endpoint still returns machine-readable Decision data and record hash as it did for T13; adding the T15 HTML flow must not replace or break the JSON endpoint.
- **Notes:** This guards against a UI implementation that changes the integration contract. If content negotiation or redirects are introduced, the existing JSON path must remain directly testable.

## Coverage checklist
- [ ] Happy path covered: all six scenario cards and all six decision pages.
- [ ] Error/edge cases covered: no-control scenario, payment semantic skip, escalation routing, existing JSON endpoint compatibility, and non-debug readable rendering.
- [ ] Spec non-negotiables verified: exact §7 outcomes, no invented control for scenario 1, payment scenarios do not invoke semantics, stub is labelled, model is not presented as judge, threshold is shown from the Decision, and framework mappings do not cite unsupported Horizon recommendation numbers.
- [ ] Real dependencies flagged: scenario-run tests should use the real route/pipeline with real OPA policy decisions, real Presidio evidence for email scenarios, real settings value, and real audit record creation where available; do not mock these away for acceptance coverage.

## Gaps or ambiguities
- The exact route names/methods for the scenario runner and HTML Run action are not specified in MASTER_SPEC.md or TASK_LEDGER.md. Implementer should choose routes within `app/web/routes.py` while preserving the existing `POST /run/{scenario_id}` JSON endpoint.
- The exact approval queue URL is not defined until T16. For T15, tests should assert that an approvals link is present and clearly points to the intended approvals queue route, without requiring the target page to be implemented yet.
- Exact Tailwind colour classes are not specified. Tests should assert semantic decision state text/classes rather than brittle colour token names.
