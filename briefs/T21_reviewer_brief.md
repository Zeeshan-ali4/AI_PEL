# Review Report — T21: README + demo script (narration)

## Verdict
APPROVE

## Critical findings
- None.

## Spec and ledger compliance
- Correct task only: yes
- Dependencies respected: yes (T19, T22, T23, T24, T25 all `Done` per ledger)
- Allowed files only: yes — `README.md`, `DEMO_SCRIPT.md`, `tests/T21_readme_demo/*`, plus the three ledger-authorised minor additions in `app/pipeline.py`, `app/settings_store.py`, `app/web/routes.py`, `app/web/templates/{dashboard,decision,settings}.html`. No schema, Rego, or other out-of-scope files touched.
- `Done when` satisfied: yes — README/DEMO_SCRIPT cover the ten beats in order, scenario outcomes match §7 exactly, real-vs-stubbed list present, shadow-mode callout renders, fail-closed simulation auto-resets, dashboard aggregate stats added.
- `Verify` satisfied: partial — ran `pytest tests/T21_readme_demo` directly (not via `docker compose run`, no Docker daemon available in this review environment); all 6 tests pass after installing missing deps locally. Full `docker compose up --build` manual walkthrough was not performed in this review session.
- Reviewer focus satisfied: yes — script reads as spoken narration (35+ sentences, no code fences), each beat answers a distinct buyer question, the three minor code additions are minimal and scoped.

## Product invariant checks
- Model is not judge: pass — README/script consistently state OPA/Rego is binding, model/stub is evidence only.
- OPA/PDP owns decisions: pass — `app/pipeline.py` change only adds a one-shot flag check that substitutes a `fail_closed` decision before calling OPA; this mirrors the existing `context_resolution_ok`/`sensor_error` fail-closed pattern already in the pipeline, not a new Python decision path.
- Evidence has no decision fields: pass/not applicable — no Evidence schema changes.
- Fail-closed preserved: pass — one-shot OPA failure simulation is clearly labelled as a demo control, consumes itself (`consume_opa_failure_simulation`), and is verified by `test_one_shot_policy_engine_failure_auto_resets` to reset after one use and not recur on the next run.
- Append-only audit preserved: pass — no audit/store changes.
- Stubs labelled: pass — README and DEMO_SCRIPT both explicitly label MCP interception, connectors, nuance stub, auth/multi-tenancy/scale, framework mappings, and the one-shot OPA failure simulation as demo-only/illustrative.
- Scenario outcomes preserved: pass — `test_scenario_outcomes_match_in_readme_and_script` asserts the literal §7 mapping for all six scenarios in both documents; no scenario/policy code was touched.

## Required changes
None.

## Non-blocking notes
- The PM/BA Test Brief suggested four target files (`test_readme_content.py`, `test_demo_script_content.py`, `test_cross_doc_consistency.py`, `test_demo_support_behaviour.py`); the Implementer consolidated the first three into a single `test_readme_demo_content.py`. Coverage of the brief's test cases is intact, but this departs from the suggested split-by-concern structure. Acceptable here since the brief labelled the file list as "suggested," but worth keeping single-file consolidation from becoming a habit on future doc-heavy tasks.
- Verification in this review was run directly with `pytest` after manually installing `httpx`, `psycopg[binary]`, `presidio-analyzer`, `click` (no Docker daemon in this environment) rather than via `docker compose run --rm app pytest -q`. Result was 6/6 passing, but the human gate should still run the full Docker-based Verify step and the manual 10-beat walkthrough before marking T21 `DONE`.
