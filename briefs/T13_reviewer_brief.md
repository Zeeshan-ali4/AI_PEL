# Reviewer Brief — T13: pipeline.py (INTEGRATION MILESTONE)

## Scope reviewed
- `app/pipeline.py`
- `app/web/routes.py`
- `app/main.py` (router registration only)
- `tests/T13_pipeline/` (`__init__.py`, `conftest.py`, `test_pipeline_records.py`, `test_run_endpoint.py`, `test_pipeline_fail_closed.py`)

## Pipeline order vs MASTER_SPEC.md §11
`PolicyPipeline.run_raw_tool_call` follows the spec order exactly: intercept (via `sdk_wrapper.call_tool`, called in `run_scenario`) → `normalise()` → `context_resolver.resolve()` → evidence (`_build_evidence`, delegates to `evidence_builder.build_evidence`, which itself short-circuits to `evaluated=false` for non-email actions without invoking Presidio/stub) → load settings (`SettingsStore.read_settings()`) → `opa_client.decide()` → `enforce()` → `audit_store.write_record()`. A record is written unconditionally at the end of `run_raw_tool_call`, satisfying "every run writes a record regardless of decision."

Minor nit (non-blocking): `_build_evidence`'s `if/else` on `action.action_type` is redundant — `evidence_builder.build_evidence` already does the same dispatch internally, so both branches call the identical function. Harmless, but worth simplifying in a future cleanup pass; not a correctness issue and not worth blocking T13 over.

## Fail-closed paths (Python's only allowed decision authority)
`_decide()` correctly returns the single Python-made decision (`fail_closed`) only for the two spec-sanctioned cases — `context.context_resolution_ok is False` and `evidence.sensor_error is True` — then otherwise delegates to `opa_client.decide()`, which itself returns `fail_closed` on OPA unreachability. No other decision logic exists in Python. Confirmed no allow/block/escalate value is ever Python-originated.

## Schema/contract fidelity
- Evidence: no decision field added; payment path evidence has `evaluated=false`, `detected_entities=[]`, `evidence_spans=[]` (verified via `evidence_builder._payment_skip_evidence`).
- Decision: `threshold_used` is sourced from `settings.to_policy_config()` → passed to OPA → echoed back, not hardcoded.
- EvidenceRecord: written via the real T12 `AuditStore.write_record`, which is append-only and hash-chained; no mutation path is touched by T13 code.

## Enforcement / approval queue
`enforce()` (T11) is called with `control_modes` and `approval_queue` from the real settings/queue objects. Endpoint and unit tests confirm blocks do not enqueue and escalations do.

## Endpoint
`POST /run/{scenario_id}` is registered on the real `app` object in `app/main.py` (`app.include_router(t13_router)`), not just a test-local app, satisfying the architect brief's explicit requirement for ledger curl verification. Unknown scenario IDs return `404` via `UnknownScenarioError` and write no record (verified by test).

## Test review (`tests/T13_pipeline/`)
Coverage matches the Test Brief closely:
- `test_pipeline_records.py` — all six §7 scenarios with exact decision/control/role triples, hash presence, intact chain, payment evaluated=false, email evaluated=true with stub source/version, threshold flip to `allow_with_logging` at 0.60, escalation-queues-but-block-does-not.
- `test_run_endpoint.py` — endpoint coverage for all six scenarios against the real `app`, record-hash/response parity with persisted store, and the unknown-scenario 404 case with no record written.
- `test_pipeline_fail_closed.py` — context-resolution failure, sensor error, and OPA-unreachable paths, each asserting a `fail_closed` decision and a written, hashed record.
- Tests correctly avoid mocking the normal-path OPA/Rego decision; mocking is confined to the three sanctioned failure-boundary tests (sensor exception, OPA unreachable, forced context failure), matching the architect brief's non-negotiable.
- `conftest.py`'s `opa_url` fixture is well designed: prefers a live `OPA_URL`, falls back to spawning a local `opa run --server` against `opa/policies` + `opa/data`, and **skips** (not fails) the real-OPA-dependent tests when no OPA binary/URL is available.

## Verification actually performed in this review session
- Ran `pytest tests/T13_pipeline/` in a fresh venv with the pinned `requirements.txt`. Result: **4 passed, 4 skipped** — the three fail-closed tests and the unknown-scenario-ID test passed (these don't require live OPA); the four tests requiring a real OPA/Rego decision were **skipped**, not failed, because this review sandbox has neither a Docker daemon nor outbound network access to fetch an `opa` binary.
- Could not run the ledger's literal curl verification (`docker compose up` is unavailable here — no `/var/run/docker.sock`).
- Static review of `app/pipeline.py`, `app/web/routes.py`, `app/main.py`, and `app/semantic/evidence_builder.py` confirms the wiring, schemas, and decision provenance are correct and match T03–T12's real interfaces (no fakes/hardcoding introduced in T13).

## Outstanding action for the human gate
This review is **code-correct but not environment-verified**. Before marking T13 `DONE`, run the ledger's actual verify step in an environment with Docker (or a real OPA binary + Postgres/sqlite):
```bash
docker compose up --build
curl -X POST http://localhost:8080/run/1   # ... through /run/6
```
and confirm the six decisions match §7 and `verify_chain()` is intact, and additionally run the full `tests/T13_pipeline/` suite there to confirm the 4 currently-skipped real-OPA tests pass.

## Verdict
No code or scope violations found. Touches only the allowed files. No schema drift, no Python-made non-fail-closed decisions, no semantic-layer invocation on payments, append-only audit writes preserved. **Recommend REVIEW → QA**, contingent on the human/QA running the skipped real-OPA tests and the docker-based curl verification in an environment that has Docker/OPA available, since that could not be executed in this sandbox.