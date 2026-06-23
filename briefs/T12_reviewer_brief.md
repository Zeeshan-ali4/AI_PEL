# Reviewer Brief — T12: Audit store + hash chain (tamper-evident)

## Verdict
**APPROVE** — implementation matches the architect brief, the spec (§5.5), and AGENTS.md non-negotiables. All 13 tests from `tests/T12_audit/` pass.

## Files reviewed
- `app/audit/models.py`
- `app/audit/store.py`
- `tests/T12_audit/__init__.py`, `conftest.py`, `test_hash_chain.py`, `test_verify_chain.py`, `test_tampering.py`, `test_record_types.py`, `test_append_only.py`

## Verification performed
- No Docker daemon available in this sandbox (Postgres/OPA containers can't start), so verified against the dual sqlite path the architect brief explicitly designed for testability without Docker.
- Built a clean venv, installed `requirements.txt` + `pytest`, ran:
  - `pytest tests/T12_audit -v` → **13 passed**, covering: chain linkage, genesis 64-zero `prev_hash`, hash excludes `id`/`record_hash`, canonical JSON determinism, intact-chain verification (incl. empty store), tamper detection at the exact broken row (and that it doesn't blame earlier/later rows), both `action_evaluation` and `approval_decision` round-trips with `references_hash` linkage, and append-only enforcement (no update path besides `simulate_tampering`).

## Spec/AGENTS.md compliance checks
- **Field fidelity**: `EvidenceRecord` fields in `app/schemas/audit.py` (`id, correlation_id, action, context_used, evidence, decision, enforcement_mode, executed, record_type, references_hash, human_approver, approval_reason, created_at, record_hash, prev_hash`) are reproduced exactly in `models.AuditRow` and `store.py` — no renames, additions, or removals.
- **Hash rule**: `_hash_payload` hashes `canonical_json(row minus id/record_hash) + prev_hash`; confirmed by `test_record_hash_excludes_id_and_record_hash_fields`, which independently recomputes the hash and matches.
- **Genesis**: `GENESIS_PREV_HASH = "0" * 64` in `models.py`, used by `_tail_hash()` when the table is empty.
- **Canonical JSON**: `sort_keys=True, separators=(",", ":")` — identical helper used at write time and verify time, so verification recomputes the exact bytes hashed at write (no spurious breaks from dict ordering or whitespace).
- **Append-only**: `write_record` only ever INSERTs (confirmed structurally — no UPDATE call in that path) and `simulate_tampering` is the sole, clearly-named, separately-documented exception (docstring explicitly states demo-only, bypasses hashing, never called by other code paths). `test_write_record_never_mutates_existing_rows` and `test_store_exposes_no_update_path_besides_simulate_tampering` confirm this behaviourally.
- **Tamper detection**: `verify_chain()` walks rows in insertion order, recomputes each hash from stored fields + previous record_hash, and returns the **first** broken index/id — confirmed by `test_verify_chain_stops_at_first_broken_row` (4 records, only row 2 tampered, row 2 reported even though rows 3/4 would also fail to re-link).
- **No decision logic leaked**: the store has no allow/block/judgement logic; it stores whatever `Decision` it's handed, matching "the policy engine is the judge."
- **Dual sqlite/Postgres**: both paths implemented in parallel (`_sqlite_connection`/`_postgres_connection`, mirrored `_ensure_table`, `_insert_row`, `_fetch_all_rows`); sqlite path is what tests exercise; Postgres path follows the same column shape and `Jsonb` wrapping for jsonb columns, consistent with `settings_store.py`'s convention.
- **Scope discipline**: changes are confined to `app/audit/models.py`, `app/audit/store.py`, and `tests/T12_audit/` — no edits to `app/schemas/audit.py`, no pipeline wiring, no UI. Matches the architect brief's allowed-files list.

## Minor observations (non-blocking)
- `simulate_tampering` only supports flipping the `executed` field (or an explicit override of it). This satisfies the ledger's verify step ("tamper row 2") and the brief's intent, but if T18's UI demo wants to tamper a different field (e.g. inside `decision` or `evidence`) for narrative variety, a follow-up task may need to extend it — not a defect for T12 itself, since the brief only required *a* mutation that breaks the chain.
- `verify_chain`'s return type (`ChainVerificationResult` with `intact`, `verified_count`, `broken_record_id`, `broken_reason`) is self-documenting and consistent across pass/fail paths, resolving the one ambiguity flagged in the test brief.

## Recommendation
Pass to QA. No changes requested.