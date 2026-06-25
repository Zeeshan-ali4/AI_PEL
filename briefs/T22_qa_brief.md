# QA Report — T22: Live event feed with background traffic (headline demo moment)

## Verdict
INCONCLUSIVE

## Ledger verification
- Command run: `docker compose run --rm app pytest tests/T22_event_feed/ -v`
- Result: not run — Docker is not installed in this environment (`/bin/bash: line 1: docker: command not found`). I ran the closest available local check with `pytest tests/T22_event_feed/ -v`; it passed only the dependency-free tests and skipped the real OPA-backed acceptance tests.

## Test suite results
- Command run: `pytest tests/T22_event_feed/ -v`
- Total: 16 | Passed: 3 | Failed: 0 | Errors: 0 | Skipped: 13
- Output summary: `tests/T22_event_feed/test_background_events.py::{test_background_pool_contains_20_to_25_routine_templates,test_background_sampler_returns_8_to_12_events,test_background_sampler_can_produce_different_mixes}` passed. The remaining 13 tests skipped because the T22 fixture requires a real OPA endpoint and neither `OPA_URL` nor an `opa` binary was available locally.

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_background_events.py` | `tests/T22_event_feed/test_background_events.py` | ok |
| `test_event_stream.py` | `tests/T22_event_feed/test_event_stream.py` | ok |
| `test_pipeline_trace.py` | `tests/T22_event_feed/test_pipeline_trace.py` | ok |
| `test_event_feed_ui.py` | `tests/T22_event_feed/test_event_feed_ui.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| `test_background_pool_contains_20_to_25_routine_templates` | `test_background_pool_contains_20_to_25_routine_templates` | `tests/T22_event_feed/test_background_events.py` | yes | Passed locally. Checks pool size, supported canonical action kinds, tool names, resources, and parameters. |
| `test_background_sampler_returns_8_to_12_events` | `test_background_sampler_returns_8_to_12_events` | `tests/T22_event_feed/test_background_events.py` | yes | Passed locally. Checks sample size and that returned events are independent copies rather than mutating the pool. |
| `test_background_sampler_can_produce_different_mixes` | `test_background_sampler_can_produce_different_mixes` | `tests/T22_event_feed/test_background_events.py` | yes | Passed locally. Uses multiple seeded random samples and verifies mixes differ. |
| `test_all_background_events_resolve_to_allow_or_allow_with_logging_with_real_pipeline` | `test_all_background_events_resolve_to_allow_or_allow_with_logging_with_real_pipeline` | `tests/T22_event_feed/test_background_events.py` | inconclusive | Test exists and assertions match the brief, but it skipped locally because real OPA was unavailable. Must be run with Docker/OPA before this can pass QA. |
| `test_stream_endpoint_returns_sse_content_type` | `test_stream_endpoint_returns_sse_content_type` | `tests/T22_event_feed/test_event_stream.py` | inconclusive | Test exists and checks status, `text/event-stream`, and `data:` SSE payloads, but skipped locally due to missing OPA. |
| `test_stream_runs_background_events_then_focal_scenario_3_block` | `test_stream_runs_background_events_then_focal_scenario_3_block` | `tests/T22_event_feed/test_event_stream.py` | inconclusive | Test exists and checks 8–12 background events followed by focal Scenario 3 `block` / `FIN-PAY-001`, but skipped locally due to missing OPA. |
| `test_stream_payload_shape_matches_contract` | `test_stream_payload_shape_matches_contract` | `tests/T22_event_feed/test_event_stream.py` | inconclusive | Test exists and checks required event fields, indexes, totals, and trace only on focal events, but skipped locally due to missing OPA. |
| `test_focal_trace_contains_required_stage_sequence_for_payment` | `test_focal_trace_contains_required_stage_sequence_for_payment` | `tests/T22_event_feed/test_pipeline_trace.py` | inconclusive | Test exists and checks the exact payment trace stage sequence and semantic skip summary, but skipped locally due to missing OPA. |
| `test_focal_trace_contains_semantic_evidence_for_email_scenario_4` | `test_focal_trace_contains_semantic_evidence_for_email_scenario_4` | `tests/T22_event_feed/test_pipeline_trace.py` | inconclusive | Test exists and checks semantic evidence, detected entities, `nuance_stub`, confidence, and `threshold_used`, but skipped locally due to missing OPA. |
| `test_focal_trace_policy_and_audit_outputs_are_real` | `test_focal_trace_policy_and_audit_outputs_are_real` | `tests/T22_event_feed/test_pipeline_trace.py` | inconclusive | Test exists and checks Decision fields, audit record id/hash, and chain verification, but skipped locally due to missing OPA. |
| `test_existing_run_routes_still_return_compatible_results` | `test_existing_run_routes_still_return_compatible_results` | `tests/T22_event_feed/test_pipeline_trace.py` | inconclusive | Test exists and checks `POST /run/3` plus `POST /scenarios/1/run`, but skipped locally due to missing OPA. |
| `test_event_feed_page_loads_and_references_static_eventsource_js` | `test_event_feed_page_loads_and_references_static_eventsource_js` | `tests/T22_event_feed/test_event_feed_ui.py` | inconclusive | Test exists and checks page/static-JS contract, EventSource usage, and decision styling hooks, but skipped locally due to missing OPA. |
| `test_stream_writes_audit_record_for_every_event_and_chain_remains_valid` | `test_stream_writes_audit_record_for_every_event_and_chain_remains_valid` | `tests/T22_event_feed/test_event_stream.py` | inconclusive | Test exists and checks audit count growth and valid hash chain after a stream, but skipped locally due to missing OPA. |
| `test_stream_handles_each_canonical_focal_scenario_with_correct_final_decision` | `test_stream_handles_each_canonical_focal_scenario_with_correct_final_decision` | `tests/T22_event_feed/test_event_stream.py` | inconclusive | Test exists and checks all six canonical final scenario decisions/control IDs, but skipped locally due to missing OPA. |

### Extra tests (Implementer-added)
- `test_unknown_scenario_stream_returns_404` in `tests/T22_event_feed/test_event_stream.py`.
- `test_event_feed_is_discoverable_from_primary_nav_and_scenario_cards` in `tests/T22_event_feed/test_event_feed_ui.py`.

## Spec non-negotiable checks
- Evidence schema has no decision/enforcement/approval fields: passed by inspection; T22 did not alter `app/schemas/evidence.py`, and trace tests expect evidence summaries only.
- No policy logic in Python schemas or components: inconclusive at runtime because real OPA-backed tests skipped, but static test fixture design requires a real OPA endpoint (`OPA_URL` or local `opa`) rather than mocked policy decisions.
- Real components are real, stubs are labelled: inconclusive at runtime because real OPA/Presidio/audit acceptance tests skipped; test coverage does assert `nuance_stub` labelling and audit hash-chain verification when dependencies are available.
- Payment semantic layer skip: inconclusive at runtime because the trace acceptance test skipped; the test asserts a `semantic_skipped` stage with `evaluated=false` and “not invoked” text.
- Append-only audit/hash chain: inconclusive at runtime because the audit-writing stream tests skipped; the tests assert audit count increases by event count and chain verification remains intact.

## Failures
- The required ledger verification command could not run because Docker is unavailable.
- The local T22 suite is not sufficient for QA sign-off: 13 of 16 tests skipped, including all real pipeline/OPA/SSE/audit acceptance checks.

## Recommendation
Re-run verification after environment issue is resolved. T22 should not proceed to human approval until `docker compose run --rm app pytest tests/T22_event_feed/ -v` or an equivalent environment with a real OPA endpoint completes without skipped real-dependency acceptance tests.
