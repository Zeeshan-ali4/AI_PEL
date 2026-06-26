# Test Brief — T21: README + demo script (narration)

## Spec references
- `MASTER_SPEC.md`: §1 (what the demo proves and deliberately-not-in-scope list), §1A (Head of Risk and Assurance value pillars), §1B (sensitivity/framing guidance), §3 (logical architecture), §5.5 (hash-chained evidence records), §6 (control library, decision precedence, configurable threshold), §7 (six narrative scenarios and exact outcomes), §8/§8A (enforcement modes and assurance UI), §9 (auditable surface counter), §12 (acceptance criteria), §13 (scope fences).
- `TASK_LEDGER.md`: T21 — README + demo script (narration), including the ten required beats in order, the three ledger-authorised demo-support additions, the `Done when` criteria, and the T21 Verify step.
- `briefs/T21_architect_brief.md`: required README/script content, allowed files, non-negotiable scenario outcomes, real-vs-stubbed honesty list, shadow-mode/fail-closed requirements, and the requirement for real pytest checks covering docs plus any T21 runtime/template additions.

## Target test location
- Folder: `tests/T21_readme_demo/`
- Suggested files:
  - `tests/T21_readme_demo/__init__.py` — empty package marker.
  - `tests/T21_readme_demo/test_readme_content.py` — README structure, run instructions, architecture, honesty list, scenario table, threshold/audit semantics.
  - `tests/T21_readme_demo/test_demo_script_content.py` — spoken narration, value pillars, ten-beat order, scenario walkthroughs, threshold/audit/fail-closed moments, sensitivity constraints.
  - `tests/T21_readme_demo/test_cross_doc_consistency.py` — README/DEMO_SCRIPT/spec consistency, port/URL consistency, no prohibited framing, illustrative-mapping caveats.
  - `tests/T21_readme_demo/test_demo_support_behaviour.py` — acceptance checks for any T21 runtime/template additions that are missing and therefore implemented: dashboard aggregate stats, shadow-mode callout, and one-shot OPA failure simulation.

## Test cases

### test_readme_states_audience_and_purpose
- **Traces to:** `MASTER_SPEC.md` §1A; Architect Brief implementation objective.
- **Input:** Full text of `README.md` read from repo root.
- **Expected outcome:** README identifies the product as a runtime policy enforcement gate demo and explicitly names the Head of Risk and Assurance, or an unambiguous equivalent risk/assurance buyer audience.
- **Notes:** Case-insensitive keyword assertions are acceptable; do not require exact prose.

### test_readme_leads_with_assurance_value_before_implementation_detail
- **Traces to:** `MASTER_SPEC.md` §1A; Architect Brief — explain assurance value before implementation detail.
- **Input:** `README.md` split by Markdown headings.
- **Expected outcome:** A value/assurance section referencing human oversight, evidential reliability, demonstrable control operation, governed/configurable policy, or proportionate deterministic enforcement appears before architecture and run-instruction sections.
- **Notes:** Assert section ordering rather than exact heading names.

### test_readme_documents_clean_checkout_run_instructions
- **Traces to:** `TASK_LEDGER.md` T21 Done when and Verify step.
- **Input:** `README.md`, `docker-compose.yml`, and any app config file that declares public ports.
- **Expected outcome:** README includes `docker compose up` or `docker compose up --build`, the app URL `http://localhost:8080`, and describes how to reach the dashboard, scenario runner/live feed, approval queue, evidence/audit records, audit log, and settings/control pages.
- **Notes:** Assert the documented app/OPA/Postgres ports do not contradict compose/config values: app `8080`, OPA `8181`, Postgres `5432`.

### test_readme_architecture_paragraph_matches_spec_pipeline
- **Traces to:** `MASTER_SPEC.md` §3.
- **Input:** Full text of `README.md`.
- **Expected outcome:** README names the pipeline stages in order: agent simulator or PEP interception, action normaliser, context resolver, semantic evidence layer, OPA/Rego policy decision, enforcement handler, Postgres/hash-chained audit or evidence store, assurance UI.
- **Notes:** Use ordered keyword positions; do not allow invented decision-making by the model.

### test_readme_real_vs_stubbed_list_is_complete_and_accurate
- **Traces to:** `MASTER_SPEC.md` §1 and §13; AGENTS.md non-negotiable that stubs are visibly labelled.
- **Input:** Full text of `README.md`.
- **Expected outcome:** README has a clearly labelled real-vs-stubbed section. It lists as real: Presidio, OPA/Rego, Postgres-backed append-only SHA-256 hash chain, and configured controls/settings affecting policy input. It lists as stubbed/fixture/demo-only: MCP interception, enterprise connectors/context fixtures, nuance/model stub, production auth/multi-tenancy/scale, illustrative framework mappings/control packs, and the one-shot OPA failure simulation.
- **Notes:** This is a hard acceptance check; missing any required item fails.

### test_readme_summarises_six_scenarios_matching_spec_exactly
- **Traces to:** `MASTER_SPEC.md` §7; Architect Brief non-negotiables.
- **Input:** Full text of `README.md`.
- **Expected outcome:** README states the exact scenario outcomes:
  - Scenario 1: `allow`, no triggered control.
  - Scenario 2: `escalate`, `FIN-PAY-002`, required approval role `finance_supervisor`.
  - Scenario 3: `block`, `FIN-PAY-001`.
  - Scenario 4: `escalate`, `COMM-EMAIL-001`, required approval role `data_protection_approver`, stub confidence `0.88`.
  - Scenario 5: `escalate`, `COMM-EMAIL-002`, required approval role `vulnerable_customer_team`, stub confidence `0.62` at threshold `0.75`, and `allow_with_logging` at threshold `0.60`.
  - Scenario 6: `allow_with_logging`, `COMM-EMAIL-003`.
- **Notes:** Parametrize over a literal expected mapping in the test file; do not import app policy code for this doc-content assertion.

### test_readme_mentions_payment_semantic_skip_and_model_not_judge
- **Traces to:** `MASTER_SPEC.md` §2 and §3; Architect Brief non-negotiables.
- **Input:** Full text of `README.md`.
- **Expected outcome:** README states payment scenarios intentionally skip the semantic evidence layer, and states that the model/stub provides bounded evidence only while OPA/Rego is the binding decision-maker.
- **Notes:** Assert both claims separately.

### test_readme_mentions_threshold_audit_shadow_and_fail_closed_behaviour
- **Traces to:** `MASTER_SPEC.md` §6, §8A; `TASK_LEDGER.md` T21 beats 6, 8, 9, 10.
- **Input:** Full text of `README.md`.
- **Expected outcome:** README documents default semantic threshold `0.75`, lowering to `0.60` flipping Scenario 5 to `allow_with_logging`, shadow mode executing while showing the full-enforcement decision that would have applied, audit-chain verify/tamper/download features, and fail-closed behaviour when OPA/policy evaluation is unreachable.
- **Notes:** Numeric threshold values must appear verbatim.

### test_demo_script_leads_with_assurance_value_pillars
- **Traces to:** `MASTER_SPEC.md` §1A.
- **Input:** Opening section of `DEMO_SCRIPT.md` before the first scenario/beat walkthrough.
- **Expected outcome:** Opening narration references at least four of the five value pillars: human oversight/contestability, evidential reliability/integrity, demonstrable control operation, governed/configurable policy, proportionate/deterministic enforcement.
- **Notes:** Prefer all five; at least four prevents brittle wording failures.

### test_demo_script_contains_ten_beats_in_required_order
- **Traces to:** `TASK_LEDGER.md` T21 key notes.
- **Input:** Full text of `DEMO_SCRIPT.md`.
- **Expected outcome:** The ten beats appear in exactly this order: dashboard calm; routine live feed; enforcement live feed; human oversight; semantic evidence; shadow mode; policy control; confidence threshold; audit integrity; fail closed.
- **Notes:** Assert increasing text positions for beat headings/markers; the terms may be heading text or clear narration labels.

### test_demo_script_walks_through_six_scenarios_in_order_with_correct_outcomes
- **Traces to:** `MASTER_SPEC.md` §7; Architect Brief non-negotiables.
- **Input:** Full text of `DEMO_SCRIPT.md`.
- **Expected outcome:** Scenario markers 1–6 appear in ascending order. Each scenario states the same decision/control/role mapping as the README test above. Scenario 4 mentions stub confidence `0.88`; Scenario 5 mentions stub confidence `0.62`, default threshold `0.75`, and the threshold `0.60` flip to `allow_with_logging`.
- **Notes:** The six scenarios may be distributed across the ten beats, but each must be narratable from the script alone.

### test_demo_script_includes_shadow_mode_policy_control_threshold_audit_and_fail_closed_moments
- **Traces to:** `TASK_LEDGER.md` T21 beats 6–10; `MASTER_SPEC.md` §8A.
- **Input:** Full text of `DEMO_SCRIPT.md`.
- **Expected outcome:** Script narrates: shadow mode makes Scenario 3 execute while showing would-have-blocked `FIN-PAY-001`; disabling/re-enabling `FIN-PAY-002` and changing its threshold `500` → `1000` → `500`; changing semantic threshold `0.75` → `0.60`; verifying audit chain intact, simulating tampering, re-verifying broken record/mismatched hashes, downloading audit package; triggering one-shot policy-engine failure, seeing `fail_closed`, then seeing the following event run normally.
- **Notes:** Assert ordering within each moment where meaningful (e.g., verify intact before tamper before broken result).

### test_demo_script_explains_real_vs_stubbed_in_buyer_safe_spoken_language
- **Traces to:** `MASTER_SPEC.md` §1 and §13; Architect Brief implementation objective.
- **Input:** Full text of `DEMO_SCRIPT.md`.
- **Expected outcome:** Script contains spoken narration, not only a bare engineering list, that distinguishes real components (Presidio, OPA/Rego, Postgres/hash chain) from stubbed/fixture/demo-only parts (MCP interception, connectors/context, nuance/model stub, auth/multi-tenancy/scale, illustrative mappings/control packs, one-shot failure simulation).
- **Notes:** Keyword coverage plus a prose/sentence-count heuristic is acceptable.

### test_demo_script_is_standalone_spoken_narration_not_engineering_notes
- **Traces to:** `TASK_LEDGER.md` T21 demo-script pacing and reviewer focus.
- **Input:** Full text of `DEMO_SCRIPT.md`.
- **Expected outcome:** Script contains enough full sentences for a 12–15 minute spoken narration, has no long fenced code blocks, and does not read only as terse bullet fragments.
- **Notes:** Suggested heuristic: at least 20 prose sentences and no fenced code block longer than a few lines.

### test_readme_and_demo_script_omit_prohibited_horizon_framing
- **Traces to:** `MASTER_SPEC.md` §1B and §13; Architect Brief non-negotiables.
- **Input:** `README.md` and `DEMO_SCRIPT.md`.
- **Expected outcome:** Neither file contains the word `Horizon` case-insensitively or citation-like text that references Horizon Inquiry recommendation numbers.
- **Notes:** This is a hard negative-content assertion.

### test_readme_and_demo_script_label_framework_mappings_as_illustrative
- **Traces to:** `MASTER_SPEC.md` §6 and §1B.
- **Input:** `README.md` and `DEMO_SCRIPT.md`.
- **Expected outcome:** Each document explicitly labels framework/control mappings as illustrative/demo mappings, not certified or production-audited mappings.
- **Notes:** One clear caveat sentence per document is sufficient.

### test_readme_and_demo_script_scenario_tables_are_mutually_consistent
- **Traces to:** AGENTS.md scenario-outcome non-negotiable; `MASTER_SPEC.md` §7.
- **Input:** Per-scenario tokens extracted from `README.md` and `DEMO_SCRIPT.md`.
- **Expected outcome:** For each scenario, both documents agree with each other and with the literal §7 expected mapping for decision, control ID, approval role, and relevant confidence/threshold values.
- **Notes:** Use a literal expected mapping in the test module rather than app code.

### test_dashboard_aggregate_stats_render_and_update_if_touched
- **Traces to:** `TASK_LEDGER.md` T21 beat 1 and demo-support addition 1.
- **Input:** Running app/database via the existing test harness or FastAPI test client with the real application code; create/run one or more scenario evaluations using existing scenario routes/helpers.
- **Expected outcome:** Dashboard exposes total evaluations, decision breakdown (% or counts for allowed/escalated/blocked), and action-type breakdown; after an evaluation is recorded, the displayed aggregate totals increase consistently.
- **Notes:** Required if T21 adds or changes dashboard stats. Do not mock the file content. Use the existing app/database testing pattern for this repo.

### test_shadow_mode_callout_renders_executed_shadow_would_have_decision_if_touched
- **Traces to:** `TASK_LEDGER.md` T21 beat 6; `MASTER_SPEC.md` §8.
- **Input:** A shadow-mode scenario/evidence record whose underlying policy decision would be `block` for `FIN-PAY-001`.
- **Expected outcome:** The decision/record/event-feed UI clearly renders that the action executed because mode is `shadow`, while also showing the full-enforcement result, e.g. `would have blocked` and `FIN-PAY-001`.
- **Notes:** Required if the existing UI did not already make shadow-mode state clear and T21 changes it.

### test_one_shot_policy_engine_failure_auto_resets_if_touched
- **Traces to:** `TASK_LEDGER.md` T21 beat 10; `MASTER_SPEC.md` §2 fail-closed principle.
- **Input:** Trigger the T21 one-shot policy-engine failure flag through the same route/store used by the UI, then evaluate two actions in sequence.
- **Expected outcome:** First evaluation returns/renders decision `fail_closed` with policy-engine-unreachable messaging and enhanced audit evidence; the failure flag is consumed/reset; the second evaluation calls the normal OPA path and returns its normal scenario decision.
- **Notes:** Required if T21 implements the one-shot failure button/flag. This is not a mock of OPA behaviour; it is a deliberate demo control that must auto-reset and must be visibly labelled as simulated.

## Coverage checklist
- [x] Happy path covered: README and DEMO_SCRIPT contain required sections, clean-checkout run instructions, six exact §7 outcomes, and the ten-beat script order.
- [x] Error/edge cases covered: no prohibited Horizon framing, no real-vs-stub omissions, no README/compose port drift, no README/DEMO_SCRIPT scenario drift, threshold flip documented, tamper/fail-closed moments documented.
- [x] Spec non-negotiables verified: model is not the judge, OPA/Rego is binding, payments skip semantics, shadow mode is honest, fail closed is default, stubs/fixtures are visibly labelled, mappings are illustrative, §7 outcomes are exact.
- [x] Real dependencies flagged: doc-content tests are pure file reads; runtime checks for T21 code additions should use the repo's real application/test database patterns and should not replace OPA/Presidio/Postgres behaviour with broad mocks. The one-shot failure simulation is allowed only as the ledger-authorised demo control and must auto-reset.

## Gaps or ambiguities
- T21's file list names only `README.md` and `DEMO_SCRIPT.md`, but the task notes authorise three minor runtime/template additions if missing. The Implementer must first inspect existing behaviour. If a capability already exists, do not touch its runtime code; keep the corresponding behaviour test as a regression check only if it can be written against the existing app without adding scope.
- The spec and architect brief do not require exact Markdown heading names, so tests should use robust keyword and ordering assertions rather than brittle heading equality.
- The manual Verify step (running the full 12–15 minute demo after `docker compose up --build`) remains required in addition to these pytest checks; pytest cannot prove the spoken pacing or buyer-room tone by itself.
