# QA Brief — T13: pipeline.py (INTEGRATION MILESTONE)

## What was verified
Unlike the reviewer's sandbox, this QA session had `docker` (binary, no daemon) but was able to assemble equivalent real infrastructure without Docker:
- Built a Python 3.11 venv from the pinned `requirements.txt`, plus the `en_core_web_sm` spaCy model (required by Presidio).
- Fetched a real OPA v0.70.0 static binary (GitHub release) and ran it as `opa run --server` against `opa/policies` + `opa/data` on `127.0.0.1:8181`.
- Started the system's installed PostgreSQL 16 server, created the `ai_pel` database/user matching `app/config.py` defaults.
- Ran the real FastAPI app (`uvicorn app.main:app`) on port 8080 against the real OPA and real Postgres — i.e. the actual ledger-specified environment, not a test-local app.

## Test suite results
- `pytest tests/T13_pipeline/` → **8 passed, 0 skipped** (previously 4 passed / 4 skipped in the reviewer's sandbox without an OPA binary). All four real-OPA/Rego tests that the reviewer could not exercise now pass against the live OPA server.
- `pytest tests/` (full repo) → **148 passed, 2 skipped** (pre-existing, unrelated skips), no regressions.

## Ledger verify step — executed literally
`GET /health` → `{"app":"ok","opa":"ok","db":"ok"}`.

`POST /run/1` → `allow`, no control — matches §7 #1.
`POST /run/2` → `escalate`, `FIN-PAY-002`, `finance_supervisor`, not executed, queued — matches §7 #2.
`POST /run/3` → `block`, `FIN-PAY-001`, not executed, not queued — matches §7 #3.
`POST /run/4` → `escalate`, `COMM-EMAIL-001`, `data_protection_approver`, not executed, queued — matches §7 #4.
`POST /run/5` → `escalate`, `COMM-EMAIL-002`, `vulnerable_customer_team`, not executed, queued — matches §7 #5 (default threshold 0.75).
`POST /run/6` → `allow_with_logging`, `COMM-EMAIL-003`, executed, enhanced logging — matches §7 #6.

All six responses included a non-empty `record_hash` and `correlation_id`.

`POST /run/999` → `404 {"detail":"Unknown scenario number: 999"}`; no successful record written for the invalid ID.

Chain verification (`get_audit_store().verify_chain()` against the same Postgres instance the app wrote to) → `intact=True, verified_count=6, broken_record_id=None`. No tampering induced in this run, as expected.

## Coverage vs Test Brief
All test-brief scenarios are present and now exercised against real OPA: six-scenario decisions, hash-chained records, intact chain, payment semantic skip (`evaluated=false`), email evidence with real Presidio + labelled stub, threshold flip to `allow_with_logging` at 0.60, enforcement/queue side effects (block does not queue, escalate does), endpoint success/failure paths, and all three fail-closed paths (context failure, sensor error, OPA unreachable).

## Findings
No defects found. No deviation from MASTER_SPEC.md §5, §6, §7, §11 observed. No Python-made non-fail-closed decision. Payment path never invokes the semantic layer. Audit writes are append-only and hash-chained; no mutation path touched.

## Verdict
**PASS.** T13 verification (ledger curl steps + full real-OPA pytest suite + repo regression suite) succeeds in an environment with real OPA, real Postgres, and real Presidio. Recommend marking T13 `DONE` and proceeding to Release Manager / T14.