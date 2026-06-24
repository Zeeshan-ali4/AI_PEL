# QA Report — T15: Scenario runner + decision view

## Verdict
PASS (with one environment caveat — see below)

## Ledger verification
- Command run: `python -m pytest tests/T15_scenarios_ui/ -v` (no Docker daemon and no `opa` binary available in this QA environment, so the ledger's literal `docker compose run --rm app pytest ...` step could not be executed; ran the closest equivalent directly against the host Python env, which is the same fallback the Reviewer used)
- Result: 2 passed, 11 skipped — all 11 skips are the `wired_pipeline`/`opa_url` fixture skipping with reason `"OPA binary not available; set OPA_URL or install opa to run real Rego integration tests"`. Confirmed this is an environment-wide limitation, not specific to T15: `tests/T13_pipeline` and `tests/T14_dashboard` show the identical pattern (13 passed, 5 skipped) when run in this same environment. No `docker`/`opa` binary could be installed (no network egress to download OPA; no Docker daemon running in this sandbox).

## Test suite results
- Command run: `pytest tests/T15_scenarios_ui/ -v`
- Total: 13 | Passed: 2 | Failed: 0 | Errors: 0 | Skipped: 11
- Output summary:
  - `test_scenario_runner.py::test_scenario_runner_renders_six_canonical_cards` — PASSED
  - `test_scenario_runner.py::test_scenario_runner_uses_calm_assurance_copy_not_debug_copy` — PASSED
  - All 6 tests in `test_decision_view_scenarios.py` and all 5 in `test_evidence_panel.py` — SKIPPED (real OPA unavailable)
- No failures or errors were produced by any test that *did* run.

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---|---|---|
| `test_scenario_runner.py` | `tests/T15_scenarios_ui/test_scenario_runner.py` | ok |
| `test_decision_view_scenarios.py` | `tests/T15_scenarios_ui/test_decision_view_scenarios.py` | ok |
| `test_evidence_panel.py` | `tests/T15_scenarios_ui/test_evidence_panel.py` | ok |
| (supporting) | `tests/T15_scenarios_ui/conftest.py`, `__init__.py` | present, not requested by brief but required infra |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|---|---|---|---|---|
| test_scenario_runner_renders_six_canonical_cards | same name | test_scenario_runner.py | yes | Asserts all 6 titles, run links, "Run scenario N" labels |
| test_scenario_runner_uses_calm_assurance_copy_not_debug_copy | same name | test_scenario_runner.py | yes | Checks assurance copy present, no `object at 0x` / raw JSON |
| test_each_run_opens_decision_view_with_expected_outcome | same name | test_decision_view_scenarios.py | yes (asserted via `EXPECTED` map matching §7 exactly) | Skipped at runtime here for lack of OPA; logic inspected and matches brief |
| test_decision_view_shows_plain_reason_headline_and_colour_state | same name | test_decision_view_scenarios.py | yes | Uses `data-decision="..."` attribute as stable semantic state; reason not buried in raw JSON |
| test_decision_view_shows_triggered_control_and_framework_chips | same name | test_decision_view_scenarios.py | yes | Checks control id, "illustrative mapping", absence of "Horizon"; scenario 1 checked separately for "No control was triggered" |
| test_decision_view_displays_resolved_context_used | same name | test_decision_view_scenarios.py | yes | Checks payment (status/approval/30d history) and email (external/disclosure basis) context labels |
| test_payment_scenarios_show_semantic_layer_not_invoked | same name | test_evidence_panel.py | yes | Checks "Semantic layer not invoked" + "evidence.evaluated=false"; no stub block rendered |
| test_email_scenario_4_shows_real_presidio_entities_and_highlighted_spans | same name | test_evidence_panel.py | yes | Checks `source: presidio`, `<mark` highlighted span markup, NHS-number text |
| test_email_stub_confidence_is_labelled_as_deterministic_model_stand_in | same name | test_evidence_panel.py | yes | Checks 0.88 (#4) and 0.62 (#5) each paired with "Deterministic stub" / "model stand-in" |
| test_decision_view_displays_threshold_used_from_decision | same name | test_evidence_panel.py | yes | Compares rendered HTML value against the live JSON `threshold_used`, not a hardcoded constant |
| test_escalated_decisions_show_human_routing_and_approval_link | same name | test_decision_view_scenarios.py | yes | Checks "Sent to {role} for human decision" + `href="/approvals"` link for scenarios 2, 4, 5 |
| test_evidence_panel_states_policy_engine_is_judge_not_model | same name | test_evidence_panel.py | yes | Checks "policy engine is the judge" + "never the approval or blocking authority" |
| test_existing_json_run_endpoint_remains_backward_compatible | same name | test_decision_view_scenarios.py | yes | Confirms `POST /run/{id}` JSON contract (decision, control_id, role, record_hash) still works alongside the new HTML route |

All thirteen brief-listed test cases have a 1:1 corresponding implemented test function with matching inputs and assertions. None were skipped, combined away, or watered down by the Implementer — the runtime skips observed are fixture-level (`opa_url` unavailable in this sandbox), not Implementer omissions.

### Extra tests (Implementer-added)
- None beyond the brief's 13 specified cases — the Implementer mapped the brief 1:1 without adding extra unit tests in this task.

## Spec non-negotiable checks
- Evidence schema has no decision/enforcement/approval fields: passed (in scope only as read-only display; route/template code reads `evidence.evaluated`, `evidence.detected_entities`, `evidence.evidence_spans`, `evidence.vulnerability_indicators` — confirmed via `grep` of `decision.html`, no allow/block field referenced or introduced).
- No policy logic in Python/templates (decisions come from OPA only): passed — `decision.html` only renders fields already present on the `Decision` object returned by `get_pipeline().run_scenario()`; no new branching that re-derives allow/block/escalate.
- Real components are real, stubs are labelled: passed — `decision.html` headers the stub confidence block "Deterministic stub — model stand-in, not a production model" (verified at line 93); Presidio section labelled "Detected entities (Presidio — real sensor)" (line 76); framework chips marked "(illustrative mapping)" (line 33); no "Horizon" text present in templates.
- Payment scenarios never invoke the semantic layer: passed — `decision.html` line 64-66 gates on `semantic_evaluated` and renders "Semantic layer not invoked (evidence.evaluated=false)" for payment actions; test asserts no "Deterministic stub" block appears for scenarios 1-3.
- Model-is-not-judge statement visible: passed — line 61 of `decision.html`: "policy engine is the judge — the sensors below only supply bounded evidence."

## Failures
None. (The 11 skipped tests are an environment limitation — no `opa` binary and no Docker daemon available in this QA sandbox, with no network egress permitted to fetch one — not a test or implementation failure. This mirrors the identical, pre-existing skip pattern in `tests/T13_pipeline` and `tests/T14_dashboard`, confirming it predates T15 and is not introduced by it.)

## Recommendation
Proceed to human approval, **conditional on** the human (or an environment with Docker/OPA available) running `docker compose run --rm app pytest tests/T15_scenarios_ui/ -v` to confirm the 11 currently-skipped real-OPA acceptance tests pass green — this QA pass could not execute that real-pipeline path and is therefore a logic/static review plus a partial green run (2/13 executed, 11/13 inspected-only), not a full green run. The Reviewer flagged this same caveat in `briefs/T15_reviewer_brief.md` and it remains outstanding.