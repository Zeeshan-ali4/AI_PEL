# PM/BA Test Brief — T22: Live event feed with background traffic

## Target test file
`tests/T22_event_feed/test_event_feed.py` (plus `tests/T22_event_feed/__init__.py` and a `conftest.py` mirroring the real-OPA `wired_pipeline` pattern used by `tests/T18_audit_ui/conftest.py`).

## Scenarios to cover

1. **Background pool sampling.**
   - `sample_background_events(n)` (or equivalent) returns between 8 and 12 events when called with no explicit count, and the requested count when given one.
   - Two independent samples of the full pool are not always identical (statistically different across repeated calls), proving the mix varies.

2. **Background events are boring.**
   - Every template in the background event pool, when run through the real pipeline (`wired_pipeline` + real OPA), resolves to `allow` or `allow_with_logging` only — never `escalate`, `block`, `require_evidence`, `modify`, or `fail_closed`.
   - Every background event run writes a real audit record (`record_type=action_evaluation`) and the chain stays intact (`verify_chain().intact is True`) after a full batch.

3. **SSE stream — fraud block (scenario 3).**
   - `GET /run/3/stream` returns `content-type: text/event-stream`.
   - Parsing the SSE body as a sequence of JSON payloads: there are multiple events; the final (`is_focal=True`) payload has `decision == "block"`, `control_id == "FIN-PAY-001"`.
   - The focal payload's `trace` includes stage names covering at least `intercept`, `normalise`, `resolve_context`, `policy_decision`, `enforce`, `audit_write`, and (for a payment) `semantic_skipped`.
   - Non-focal payloads do not include a `trace` key (or it is empty), keeping the stream lightweight.

4. **SSE stream — escalation with semantic evidence (scenario 4).**
   - Running `/run/4/stream` yields a focal payload with `decision == "escalate"`, `control_id == "COMM-EMAIL-001"`.
   - The focal trace's `semantic_evidence` stage summary reflects the real Evidence object: it shows at least one detected entity and the nuance stub confidence/source, not hardcoded prose.

5. **Trace does not break existing routes.**
   - `POST /run/{scenario_id}` (T13 JSON contract) still returns the same `response_payload()` shape (`decision`, `record_hash`, `record_id`, `correlation_id`, `executed`, `enforcement`) after the trace collector is added.
   - `POST /scenarios/{scenario_id}/run` (T15 decision view) still renders 200 OK with the decision banner present.

6. **Audit integrity after a full feed run.**
   - After streaming a full scenario run (background + focal), `AuditStore.verify_chain()` is intact and the count of new `action_evaluation` records equals the number of streamed events.

## Notes for Implementer
- Use the existing real-OPA `wired_pipeline`-style fixture (spin up a real `opa` binary against `opa/policies` + `opa/data`, as in `tests/T18_audit_ui/conftest.py`), not a mocked OPA — these are acceptance tests per AGENTS.md/spec §1 (Presidio/OPA/hash chain must stay real in tests that assert their behaviour).
- Use FastAPI's `TestClient.stream(...)` (or read `response.iter_lines()`) to consume the SSE body in tests rather than depending on real wall-clock delays; if delays are present, keep them short enough not to slow the suite materially, or make the delay configurable/skippable for tests.
- QA will check these tests run green via `docker compose run --rm app pytest tests/T22_event_feed/` (or `opa` binary available locally) and that they meaningfully cover the Done-when criteria in `briefs/T22_architect_brief.md`.
