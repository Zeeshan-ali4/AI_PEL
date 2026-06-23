# QA Brief — T12: Audit store + hash chain (tamper-evident)

## Verdict
**PASS** — verification step succeeds; tests cover the full T12 test brief; no spec/AGENTS.md violations found.

## Verification performed
- Built a clean venv (`/tmp/qa_venv`), installed `requirements.txt` + `pytest`.
- Ran `pytest tests/T12_audit -v` → **13 passed, 0 failed** (no Docker/Postgres needed — sqlite path per architect brief).
- Manually re-derived the ledger's literal verify step by reading `test_tampering.py`/`test_verify_chain.py`: write 3+ records → `verify_chain()` intact; tamper row 2 → `verify_chain()` reports row 2 specifically, not row 1 or 3/4.
- Read `app/audit/models.py` and `app/audit/store.py` in full and cross-checked against `app/schemas/audit.py::EvidenceRecord` — field names match exactly (`id, correlation_id, action, context_used, evidence, decision, enforcement_mode, executed, record_type, references_hash, human_approver, approval_reason, created_at, record_hash, prev_hash`).

## Test-brief coverage check
All 10 named test cases from `briefs/T12_test_brief.md` are present and pass, one-to-one:
- `test_hash_chain.py`: chain linkage, genesis 64-zero `prev_hash`, hash excludes `id`/`record_hash`, canonical JSON determinism — all present.
- `test_verify_chain.py`: intact-with-count, intact-on-empty-store — both present.
- `test_tampering.py`: exact-row break, earlier-rows-unaffected, stops-at-first-broken-row (4 records, only row 2 tampered) — all present.
- `test_record_types.py`: `action_evaluation` round-trip, `approval_decision` round-trip with `references_hash` + original-row-unchanged re-read — both present.
- `test_append_only.py`: no update path besides `simulate_tampering`, write never mutates existing rows — both present.

The one open ambiguity flagged in the test brief (exact attribute names on `verify_chain()`'s return type) is resolved cleanly: `ChainVerificationResult(intact, verified_count, broken_record_id, broken_reason)` is self-documenting and used consistently on both the pass and fail paths.

## Non-negotiables re-checked directly against code
- Genesis `prev_hash` = `"0" * 64` (`app/audit/models.py:14`, used by `_tail_hash`).
- `record_hash = sha256(canonical_json(row minus id/record_hash) + prev_hash)` — confirmed in `store.py::write_record` (`row_for_hash` excludes `id`/`record_hash`) and independently reproduced by `test_record_hash_excludes_id_and_record_hash_fields`.
- Canonical JSON = `sort_keys=True, separators=(",", ":")`, identical helper (`canonical_json`) used at write time (`write_record`) and verify time (`verify_chain`) — no spurious breakage from dict ordering.
- `write_record` only ever issues INSERTs (sqlite and Postgres paths both `INSERT`, no `UPDATE`). `simulate_tampering` is the sole exception, clearly named, docstring states "demo-only," and bypasses hashing — confirmed not called from any other code path in `app/audit/`.
- `verify_chain()` returns the **first** broken row, not a later one — confirmed by `test_verify_chain_stops_at_first_broken_row` (4 records, row 2 tampered, row 2 reported despite rows 3/4 also failing to re-link).
- Evidence/Decision schemas untouched; no decision/judgement logic in the store — it only persists what it's handed.
- Scope discipline: `git log` shows changes confined to `app/audit/models.py`, `app/audit/store.py`, `tests/T12_audit/**` (commit `077c0a0`). No edits to `app/schemas/audit.py`, no pipeline wiring, no UI files.

## Minor observations (non-blocking, carried from Reviewer Brief)
- `simulate_tampering` currently only flips/overrides the `executed` field. Sufficient for T12's verify step and the §5.5/§18 tamper-detection demo; a future UI task (T18) may want to tamper other fields for narrative variety — not a T12 defect.

## Recommendation
Mark T12 `DONE` in `TASK_LEDGER.md`. Hand off to Release Manager / next task (T13 — pipeline integration).