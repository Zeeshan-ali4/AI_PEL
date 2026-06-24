# Test Brief — T21: README + demo script (narration)

## Spec references
- MASTER_SPEC.md: §1 (what the demo proves, deliberately-not-in-scope list), §1A (value pillars), §1B (sensitivity/framing — no Horizon hook or recommendation numbers), §3 (architecture), §6 (control library, threshold default), §7 (six narrative scenarios — exact decisions/controls/roles/confidences), §8/§8A (enforcement modes, assurance UI), §9 (auditable surface counter), §12 (acceptance criteria).
- TASK_LEDGER.md: T21 — "Done when: a stranger can `docker compose up` and run the demo from the script alone; the narration leads with assurance value." Verify: follow the README on a clean checkout; run the demo from the script.
- Architect Brief: `briefs/T21_architect_brief.md` — required README sections, required DEMO_SCRIPT.md content, non-negotiables on scenario outcomes and real-vs-stub honesty.

These are documentation artefacts, so "functional/acceptance tests" here are **content-presence and content-correctness assertions** against the rendered Markdown text of `README.md` and `DEMO_SCRIPT.md` — not behavioural tests of running code. Tests must read the actual files from the repo root (no mocking the file content) and assert on their text.

## Target test location
- Folder: `tests/T21_readme_demo/`
- Suggested files:
  - `tests/T21_readme_demo/__init__.py` — empty package marker
  - `tests/T21_readme_demo/test_readme_content.py` — covers test cases 1–9 (README structural/content checks)
  - `tests/T21_readme_demo/test_demo_script_content.py` — covers test cases 10–17 (DEMO_SCRIPT.md narration checks)
  - `tests/T21_readme_demo/test_cross_doc_consistency.py` — covers test cases 18–20 (README/DEMO_SCRIPT/spec consistency checks)

## Test cases

### test_readme_states_audience_and_purpose
- **Traces to:** Architect Brief — "State what the demo is and whom it is for"; MASTER_SPEC.md §1A
- **Input:** Full text of `README.md`
- **Expected outcome:** README mentions the product is a runtime policy enforcement gate demo, and explicitly names the Head of Risk and Assurance (or equivalent risk/assurance audience) as the intended audience.
- **Notes:** Case-insensitive substring/keyword check is acceptable; do not require exact phrasing.

### test_readme_leads_with_assurance_value_before_implementation_detail
- **Traces to:** Architect Brief — "Explain the assurance value before implementation detail"; MASTER_SPEC.md §1A
- **Input:** Full text of `README.md`, split into sections by Markdown headings
- **Expected outcome:** A value/assurance-oriented section (e.g., human oversight, evidential reliability, demonstrable control operation) appears before the architecture/run-instructions sections in document order.
- **Notes:** Assert relative ordering of heading indices, not exact wording.

### test_readme_documents_run_instructions
- **Traces to:** Architect Brief — "Document how to run the stack with `docker compose up`/`docker compose up --build`, including the app URL and key pages"
- **Input:** Full text of `README.md`
- **Expected outcome:** README contains the literal command `docker compose up` (or `--build` variant), the app URL `http://localhost:8080`, and references to at least the dashboard, scenario runner, approval queue, evidence record, audit log, and settings pages (by path or name).
- **Notes:** Verify ports match `docker-compose.yml`/`app/config.py` (8080 app, 8181 OPA, 5432 Postgres) so the README cannot silently drift from the real config.

### test_readme_architecture_paragraph_matches_spec_pipeline
- **Traces to:** Architect Brief — "Summarise the architecture in one clear paragraph aligned to MASTER_SPEC.md §3"
- **Input:** Full text of `README.md`
- **Expected outcome:** README contains a paragraph naming the pipeline stages from §3 in order (agent simulator/PEP interception, normaliser, context resolver, semantic evidence layer, OPA policy decision, enforcement, audit/evidence store, assurance UI), without inventing extra stages.
- **Notes:** Use ordered keyword presence (each stage keyword found, and each subsequent stage's first occurrence is after the previous one).

### test_readme_real_vs_stubbed_list_is_complete_and_accurate
- **Traces to:** Architect Brief — "Include an explicit 'What is real vs stubbed' honesty list"; MASTER_SPEC.md §1, §13
- **Input:** Full text of `README.md`
- **Expected outcome:** README contains a clearly labelled section listing as REAL: Presidio sensor, OPA/Rego policy engine, Postgres-backed hash-chained audit store; and as STUBBED/FIXTURE: MCP interception, enterprise connectors/context, nuance/model stub, auth/multi-tenancy/production scale, illustrative framework mappings/control packs.
- **Notes:** This is a non-negotiable per AGENTS.md ("Stubs must be visibly labelled as stubs"). Fail the test if any required real or stubbed item is missing.

### test_readme_summarises_six_scenarios_matching_spec_exactly
- **Traces to:** MASTER_SPEC.md §7 (six narrative scenarios); Architect Brief non-negotiables
- **Input:** Full text of `README.md`
- **Expected outcome:** For each of the six scenarios, README states the correct decision and (where applicable) control ID/approval role, exactly matching: #1 allow/none; #2 escalate/finance_supervisor/FIN-PAY-002; #3 block/FIN-PAY-001; #4 escalate/data_protection_approver/COMM-EMAIL-001; #5 escalate/vulnerable_customer_team/COMM-EMAIL-002; #6 allow_with_logging/COMM-EMAIL-003.
- **Notes:** Parametrize over the six scenarios; assert presence of decision keyword and control ID/role token for each. This is the regression guard against the demo narrative drifting from §7, mirroring the spirit of T20's `test_policy_decisions.py`.

### test_readme_mentions_semantic_layer_skip_for_payments
- **Traces to:** Architect Brief — "Mention that payment scenarios intentionally skip the semantic layer... model/stub is not the judge"; MASTER_SPEC.md §2, §3
- **Input:** Full text of `README.md`
- **Expected outcome:** README states that payment actions do not invoke the semantic/evidence layer, and states plainly that the model/stub provides evidence only and is not the decision-maker (OPA is).
- **Notes:** Check for both the "payments skip semantics" claim and the "model is not the judge" claim as separate assertions.

### test_readme_mentions_threshold_behaviour
- **Traces to:** Architect Brief — "Mention settings/threshold behaviour: default threshold 0.75, lowering to 0.60 flips Scenario 5 to allow_with_logging"; MASTER_SPEC.md §6, §8A item 7
- **Input:** Full text of `README.md`
- **Expected outcome:** README states the default `high_confidence_threshold` is 0.75 and that lowering it to 0.60 changes Scenario 5's outcome from `escalate` to `allow_with_logging`.
- **Notes:** Numeric values must appear verbatim (0.75 and 0.60); do not accept paraphrase without the numbers.

### test_readme_mentions_audit_chain_verification_and_tamper_simulation
- **Traces to:** Architect Brief — "Mention audit-chain verification and tamper simulation"; MASTER_SPEC.md §5.5, §8A item 6
- **Input:** Full text of `README.md`
- **Expected outcome:** README references "Verify chain" and "Simulate tampering" (or equivalent named features) and states that tampering causes the chain check to fail and name the broken record.
- **Notes:** Keyword presence check; case-insensitive.

### test_demo_script_leads_with_assurance_value_pillars
- **Traces to:** Architect Brief — "Lead with assurance value, human oversight, evidential reliability, demonstrable control operation, risk-owned policy, and deterministic/proportionate enforcement"; MASTER_SPEC.md §1A
- **Input:** Full text of `DEMO_SCRIPT.md`
- **Expected outcome:** The opening section (before the first scenario walkthrough) contains references to at least 4 of the 5 value pillars in §1A (human oversight/contestability, evidential reliability/integrity, demonstrable control operation, governed/configurable policy, proportionate/deterministic enforcement).
- **Notes:** Locate the index of the first scenario-walkthrough heading/marker; restrict the pillar search to text before that index.

### test_demo_script_walks_through_six_scenarios_in_order_with_correct_outcomes
- **Traces to:** Architect Brief — "Walk through all six scenarios in order with the exact expected outcomes and controls from MASTER_SPEC.md §7"
- **Input:** Full text of `DEMO_SCRIPT.md`
- **Expected outcome:** Scenarios 1–6 appear in ascending numeric order in the document, and for each, the narration states the same decision/control/role values as `test_readme_summarises_six_scenarios_matching_spec_exactly` (same §7 mapping). Scenario 4 narration mentions stub confidence 0.88; Scenario 5 narration mentions stub confidence 0.62.
- **Notes:** Assert strictly increasing position of each scenario marker (e.g., "Scenario 1", "Scenario 2", ...) to enforce ordering, plus the decision/confidence keyword checks per scenario.

### test_demo_script_includes_tamper_evident_chain_moment
- **Traces to:** Architect Brief — "Include the tamper-evident audit chain moment: verify intact, simulate tampering, then show the named broken record"; MASTER_SPEC.md §8A item 6
- **Input:** Full text of `DEMO_SCRIPT.md`
- **Expected outcome:** Script narrates, in order: (1) running "Verify chain" showing intact, (2) running "Simulate tampering", (3) re-verifying and naming the broken record as the result.
- **Notes:** Assert the three beats appear with the verify-intact beat occurring before the tamper beat, and the tamper beat before the re-verify/broken-record beat.

### test_demo_script_includes_threshold_change_moment
- **Traces to:** Architect Brief — "Include the threshold-change moment: at 0.75 Scenario 5 escalates; at 0.60 it allows with logging"; MASTER_SPEC.md §8A item 7
- **Input:** Full text of `DEMO_SCRIPT.md`
- **Expected outcome:** Script states Scenario 5 escalates at threshold 0.75 and flips to `allow_with_logging` at threshold 0.60, narrated as a live settings change.
- **Notes:** Numeric values 0.75 and 0.60 must appear verbatim alongside Scenario 5 context.

### test_demo_script_explains_real_vs_stubbed_in_buyer_safe_language
- **Traces to:** Architect Brief — "Explicitly explain real vs stubbed components in honest buyer-safe language"; MASTER_SPEC.md §1, §13
- **Input:** Full text of `DEMO_SCRIPT.md`
- **Expected outcome:** Script contains a spoken-narration passage distinguishing real components (Presidio, OPA, hash chain/Postgres) from stubbed/fixture components (MCP interception, connectors, nuance stub, auth/scale), phrased as narration rather than a bare bullet/engineering list.
- **Notes:** At minimum assert presence of all required real/stub keywords (same set as the README real-vs-stubbed test) within `DEMO_SCRIPT.md`.

### test_demo_script_and_readme_omit_horizon_references
- **Traces to:** Architect Brief — "Honour the sensitivity guidance: do not use Horizon as the hook, do not cite Horizon Inquiry recommendation numbers"; MASTER_SPEC.md §1B, §13
- **Input:** Full text of `README.md` and `DEMO_SCRIPT.md`
- **Expected outcome:** Neither file contains the word "Horizon" (case-insensitive) nor any pattern resembling a Horizon Inquiry recommendation citation (e.g., "recommendation \d+" in proximity to Horizon-style phrasing).
- **Notes:** This is a hard negative-content assertion — fail on any match. Spec non-negotiable, not a style preference.

### test_demo_script_and_readme_label_illustrative_framework_mappings
- **Traces to:** MASTER_SPEC.md §6 (mappings are illustrative) and §1B labelling requirement
- **Input:** Full text of `README.md` and `DEMO_SCRIPT.md`
- **Expected outcome:** Wherever framework/control mappings (e.g., ISO/IEC 42001, UK GDPR, "3 Lines of Defence") are referenced, at least one nearby/explicit statement labels these mappings as illustrative — not asserted as certified/production-audited mappings.
- **Notes:** A single explicit caveat sentence covering all mappings in each document is sufficient; it does not need to be repeated per mention.

### test_readme_and_demo_script_scenario_tables_are_mutually_consistent
- **Traces to:** Internal consistency requirement implied by AGENTS.md ("Scenario outcomes must match MASTER_SPEC.md section 7 exactly") applied across both documents
- **Input:** Extracted per-scenario decision/control/role tokens from `README.md` and `DEMO_SCRIPT.md`
- **Expected outcome:** For each of the six scenarios, the decision/control/role extracted from README equals the decision/control/role extracted from DEMO_SCRIPT.md, and both equal the §7 table.
- **Notes:** Build the §7 expectations as a literal dict inside the test (mirroring the table) rather than importing from app code, since this task touches docs only.

### test_readme_run_instructions_are_followable_on_clean_checkout
- **Traces to:** TASK_LEDGER.md T21 "Done when" — "a stranger can `docker compose up` and run the demo from the script alone"
- **Input:** `README.md` text; `docker-compose.yml`; `app/config.py`
- **Expected outcome:** Every command and URL the README instructs the reader to run/visit is internally consistent with the actual `docker-compose.yml` service/port definitions (app 8080, opa 8181, postgres 5432) — i.e., no contradicting port/URL numbers.
- **Notes:** This guards against the README describing a setup that doesn't match the real compose file (e.g., a stale port from the T01 scaffold draft).

### test_demo_script_is_standalone_spoken_narration_not_engineering_notes
- **Traces to:** Architect Brief — "The demo script should be written as spoken narration, not engineering notes"
- **Input:** Full text of `DEMO_SCRIPT.md`
- **Expected outcome:** Document contains a reasonable proportion of full narrative sentences (ending in `.`/`?`/`!`) rather than being composed entirely of terse bullet fragments or code blocks; assert there is no fenced code block longer than a few lines and that prose sentence count exceeds a minimum threshold (e.g., at least 20 sentences across the document).
- **Notes:** This is a soft structural heuristic, not a strict grammar check — keep the threshold generous to avoid false failures on reasonable narration styles.

## Coverage checklist
- [x] Happy path covered (README/DEMO_SCRIPT contain all required sections and correct §7 outcomes)
- [x] Error/edge cases covered (negative checks: no Horizon hook, no missing real/stub labels, no port/URL drift, cross-document consistency)
- [x] Spec non-negotiables verified (model-not-judge framing, illustrative mapping labelling, append-only/tamper-evident narration, §7 exact outcomes, §1B sensitivity constraints)
- [x] Real dependencies flagged: not applicable in the literal sense (no OPA/Presidio/Postgres calls in these tests — they are pure text-content tests over committed Markdown files), but the tests explicitly assert the README labels OPA/Presidio/Postgres as real and not mocked in the product itself.

## Gaps or ambiguities
- The Architect Brief does not specify an exact required heading structure for either document, so tests above use keyword/ordering checks rather than exact-heading-match checks. If the Implementer wants stricter structural tests (e.g., exact `## Real vs Stubbed` heading text), that is an acceptable Implementer-level refinement consistent with this brief's intent, not a deviation from it.
- "At least 4 of the 5 value pillars" in `test_demo_script_leads_with_assurance_value_pillars` is a deliberately tolerant threshold since the architect brief lists pillars descriptively rather than as a strict checklist; if the Implementer/QA prefer requiring all 5, that is a stricter superset and still satisfies this brief.