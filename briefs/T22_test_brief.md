# Test Brief — T22: Live event feed with background traffic (headline demo moment)

## Spec references
- MASTER_SPEC.md: §1, §1A, and §2 for assurance framing, real enforcement, model-is-not-judge, payment semantic-skip, and append-only evidence requirements.
- MASTER_SPEC.md: §5.1–§5.5 for Action, Context, Evidence, Decision, and Evidence Record contracts that streamed payloads and trace summaries must derive from.
- MASTER_SPEC.md: §6 for decision precedence, control IDs, framework mappings, and the configurable threshold echoed in decisions.
- MASTER_SPEC.md: §7 for the six canonical scenario outcomes, especially Scenario 3 `block` / `FIN-PAY-001`, Scenario 4 semantic evidence, and Scenario 6 `allow_with_logging`.
- MASTER_SPEC.md: §8 and §8A for enforcement-mode display, live UI expectations, evidence panel requirements, trace visibility, and assurance-oriented copy.
- MASTER_SPEC.md: §10–§12 for file layout, pipeline order, always-written audit records, payment semantic-skip, real Presidio entities, and valid audit chain acceptance criteria.
- TASK_LEDGER.md: T22 goal, key notes, Done when criteria, Verify step, and reviewer focus for live Server-Sent Events, 8–12 safe background events, focal trace expansion, real audit writes, and visibly different repeated runs.

## Target test location
- Folder: `tests/T22_event_feed/`
- Suggested files:
  - `test_background_events.py` — covers background pool size/shape, sample count/random mix, and safe decisions through the real pipeline.
  - `test_event_stream.py` — covers `GET /run/{scenario_id}/stream` SSE sequencing, final focal payload, content type, and trace inclusion/exclusion.
  - `test_pipeline_trace.py` — covers structured trace stages, payment semantic skip, email semantic evidence details, audit write stage, and compatibility with existing scenario run routes.
  - `test_event_feed_ui.py` — covers the live feed page/template contract and static JS behaviour markers without requiring a browser build step.

## Test cases

### test_background_pool_contains_20_to_25_routine_templates
- **Traces to:** TASK_LEDGER.md T22 Background event pool; MASTER_SPEC.md §10 file layout and §12 acceptance criteria.
- **Input:** Import the background-event pool from `app/scenarios/background_events.py`.
- **Expected outcome:** The pool contains between 20 and 25 templates; every template uses only supported canonical action types (`financial.payment.issue` or `communication.email.send` unless already supported by the normaliser); every template has enough data to be normalised and resolved against fixture-compatible clean customers/recipients.
- **Notes:** Do not accept unsupported examples such as case-note updates unless the existing normaliser and policy path already support them.

### test_background_sampler_returns_8_to_12_events
- **Traces to:** TASK_LEDGER.md T22 Done when #1 and #4.
- **Input:** Call the public background-event sampling function repeatedly with the default arguments.
- **Expected outcome:** Each sample contains 8–12 events, contains no duplicate object references that can be mutated across runs, and every returned event is a concrete runnable tool-call/action template.
- **Notes:** The test should not require a deterministic production ordering; it may set a test seed only if the implementation exposes one for testability without changing runtime randomness.

### test_background_sampler_can_produce_different_mixes
- **Traces to:** TASK_LEDGER.md T22 Done when #4 and Verify step.
- **Input:** Request two or more default samples from the full background pool.
- **Expected outcome:** The samples can differ in selected event IDs/summaries or ordering. The assertion should avoid flakiness by sampling enough times or by testing the sampler with controlled random instances if supported.
- **Notes:** This validates the demo visual requirement that repeated runs do not look identical.

### test_all_background_events_resolve_to_allow_or_allow_with_logging_with_real_pipeline
- **Traces to:** MASTER_SPEC.md §6 decision precedence, §11 pipeline order, §12 audit-chain acceptance; TASK_LEDGER.md T22 key note that background events must be boring.
- **Input:** Run every background template through the real pipeline using the normal app dependencies, including real OPA policy decisions and real audit-store writes.
- **Expected outcome:** Every background event returns decision `allow` or `allow_with_logging`; no background event returns `escalate`, `block`, or `fail_closed`; each result has an audit record written; the audit chain verifies after the batch.
- **Notes:** OPA and Postgres/audit storage must be real, not mocked. This is a functional acceptance test because accidental escalations dilute the headline demo moment.

### test_stream_endpoint_returns_sse_content_type
- **Traces to:** TASK_LEDGER.md T22 SSE endpoint key note; MASTER_SPEC.md §8A UI expectations.
- **Input:** Use the FastAPI test client or an integration client to call `GET /run/3/stream`.
- **Expected outcome:** Response status is 200 and media type/content type is `text/event-stream`; the stream yields JSON payloads as SSE `data:` events.
- **Notes:** Tests should avoid real 200–400ms sleeps where possible, for example by injecting/setting a zero-delay option if the implementation provides one within the allowed files.

### test_stream_runs_background_events_then_focal_scenario_3_block
- **Traces to:** MASTER_SPEC.md §7 Scenario 3; TASK_LEDGER.md T22 Verify and Done when #1–#3.
- **Input:** Consume the full `GET /run/3/stream` SSE sequence.
- **Expected outcome:** The stream contains 9–13 total payloads: 8–12 background payloads followed by one focal payload. All background payloads have `is_focal=false`, compact `action_summary`, and decision `allow` or `allow_with_logging`. The final payload has `is_focal=true`, decision `block`, `control_id` `FIN-PAY-001`, and a non-empty `trace`.
- **Notes:** This is the primary headline acceptance test. It must use the real pipeline and real OPA decision path.

### test_stream_payload_shape_matches_contract
- **Traces to:** TASK_LEDGER.md T22 SSE endpoint JSON contract; MASTER_SPEC.md §5 schemas.
- **Input:** Consume any scenario stream, preferably `/run/1/stream` for allow and `/run/3/stream` for block.
- **Expected outcome:** Every payload includes at least `event_index`, `total_events`, `is_focal`, `action_summary`, `decision`, and `control_id`. `event_index` is sequential and `total_events` matches the number of emitted events. `trace` is absent or null for background events and present only for the focal event.
- **Notes:** The payload can include additional fields, but required fields must remain stable for the UI.

### test_focal_trace_contains_required_stage_sequence_for_payment
- **Traces to:** MASTER_SPEC.md §11 pipeline order; TASK_LEDGER.md T22 PipelineTrace key note and Done when #3/#6.
- **Input:** Run `/run/3/stream` or call the pipeline with trace enabled for payment Scenario 3.
- **Expected outcome:** The focal trace contains stages in order: `intercept`, `normalise`, `resolve_context`, `semantic_skipped`, `policy_decision`, `enforce`, `audit_write`. Each stage includes `stage_name`, `timestamp`, `duration_ms`, `inputs_summary`, and `outputs_summary`. The semantic stage summary indicates `evaluated=false` and clearly shows the semantic layer was not invoked for a structured payment action.
- **Notes:** Summaries must be serialisable and derived from real pipeline objects/results, not hardcoded demo prose.

### test_focal_trace_contains_semantic_evidence_for_email_scenario_4
- **Traces to:** MASTER_SPEC.md §7 Scenario 4, §8A Decision view evidence panel, and §12 real Presidio acceptance; TASK_LEDGER.md T22 Done when #6.
- **Input:** Consume `/run/4/stream` or call the pipeline with trace enabled for email Scenario 4.
- **Expected outcome:** The focal trace includes `semantic_evidence` rather than `semantic_skipped`; its outputs show `evaluated=true`, at least one Presidio-derived detected entity/evidence span when the fixture text contains NHS number/health data, labelled `nuance_stub` confidence/source details, and the policy decision output includes `threshold_used`.
- **Notes:** Presidio must be real, not mocked or hardcoded. The nuance sensor remains the labelled deterministic stub defined by the spec.

### test_focal_trace_policy_and_audit_outputs_are_real
- **Traces to:** MASTER_SPEC.md §5.4–§5.5, §11 steps 5–7, and §12 verify chain acceptance.
- **Input:** Run a focal scenario stream and inspect the focal trace plus audit store.
- **Expected outcome:** The `policy_decision` stage outputs the real Decision fields including `decision`, `triggered_controls`, `reason`, `framework_mappings`, `policy_version`, and `threshold_used`; the `audit_write` stage outputs a real audit record identifier/hash summary; the audit chain verifies after the stream completes.
- **Notes:** The test must not accept a trace-only fake audit marker. The record must exist in the append-only audit store.

### test_existing_run_routes_still_return_compatible_results
- **Traces to:** Architect brief compatibility requirement; MASTER_SPEC.md §8A Scenario runner and Decision view.
- **Input:** Call existing scenario run routes, including `POST /run/{scenario_id}` and `POST /scenarios/{scenario_id}/run` if both exist in the current app.
- **Expected outcome:** Existing routes still return their prior response shape/status/redirect behaviour and scenario decisions after trace support is added. Scenario 3 still resolves to `block` / `FIN-PAY-001`; Scenario 1 still resolves to `allow`.
- **Notes:** Trace support must be additive and must not break existing UI/API flows.

### test_event_feed_page_loads_and_references_static_eventsource_js
- **Traces to:** MASTER_SPEC.md §8A UI/UX for assurance; TASK_LEDGER.md T22 Frontend key note.
- **Input:** Request the live feed page route selected by the implementer for a scenario, then request `/static/event_feed.js` or the configured static URL.
- **Expected outcome:** The HTML response renders successfully, references the event-feed JavaScript, includes a scenario identifier or stream URL for `GET /run/{scenario_id}/stream`, and contains UI affordances for a vertical feed plus focal trace expansion. The JS includes EventSource usage and renders decision-specific styling hooks for green/neutral background rows and red/amber focal rows.
- **Notes:** This is a server-rendered/Jinja + static JS contract test, not an end-to-end browser test. Do not require a JS build step.

### test_stream_writes_audit_record_for_every_event_and_chain_remains_valid
- **Traces to:** MASTER_SPEC.md §5.5 append-only evidence records, §11 step 7, and §12 verify chain acceptance; TASK_LEDGER.md T22 Done when #5.
- **Input:** Record audit count/hash-chain status, consume a full scenario stream, then inspect the audit store.
- **Expected outcome:** Audit record count increases by exactly `total_events` action-evaluation records for the stream; records include both background and focal correlations; no historical records are mutated; chain verification passes.
- **Notes:** Postgres/audit store must be real. If tests use an isolated test database, it should still exercise the actual store implementation and hash computation.

### test_stream_handles_each_canonical_focal_scenario_with_correct_final_decision
- **Traces to:** MASTER_SPEC.md §7 all six narrative scenarios; TASK_LEDGER.md T22 Done when #2.
- **Input:** Consume the focal payload from `/run/{scenario_id}/stream` for scenario IDs 1–6.
- **Expected outcome:** Final focal decisions exactly match §7: #1 `allow` with no control, #2 `escalate` / `FIN-PAY-002`, #3 `block` / `FIN-PAY-001`, #4 `escalate` / `COMM-EMAIL-001`, #5 `escalate` / `COMM-EMAIL-002`, and #6 `allow_with_logging` / `COMM-EMAIL-003`.
- **Notes:** This may be one parametrized acceptance test. It guards against T22 tracing/streaming changes altering existing scenario outcomes.

## Coverage checklist
- [x] Happy path covered: scenario streams, 8–12 background events, focal event last, trace expansion contract, UI page/static JS contract.
- [x] Error/edge cases covered: accidental background escalation/block/fail-closed, sampler non-randomness, missing trace fields, compatibility regressions, and audit-chain drift.
- [x] Spec non-negotiables verified: real pipeline, OPA as judge, payment semantic-skip, real Presidio evidence for email, append-only audit writes, correct §7 scenario outcomes, and no fake trace/audit markers.
- [x] Real dependencies flagged: OPA, Presidio, Postgres/audit hash chain, normaliser, context resolver, enforcement handler, and audit store must be exercised through real implementations for acceptance tests.

## Gaps or ambiguities
- TASK_LEDGER.md mentions adding a “Reset demo data” button only if existing capabilities allow it, but `app/audit/store.py` or other storage primitives are not in T22's allowed file list. Treat reset as optional/out of scope unless it can be implemented entirely in the listed files without new storage behaviour.
- TASK_LEDGER.md examples include “case note update,” but the canonical schemas and scenario table only require payment and email actions. Background tests should reject unsupported action types unless the existing normaliser already supports them.
- The ledger does not name the route that serves `event_feed.html`; the Implementer should choose a route within `app/web/routes.py` that does not require modifying unlisted templates. Tests should discover or target that route once implemented.
- The ledger allows visual pacing delays, but acceptance tests should not be slow or flaky. The Implementer should provide a test-safe way to avoid real sleeps if possible within the allowed files.
