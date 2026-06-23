# Architect Brief — T12: Audit store + hash chain (tamper-evident)

## Task selected
- Task: T12 — Audit store + hash chain (tamper-evident)
- Current status: TODO (ledger says "To do")
- Dependencies checked: T02 (schemas) = Done; T01 (Postgres/app scaffold) = Done. Both satisfied — task is unblocked.

## Source-of-truth references
- MASTER_SPEC.md §5.5 — EvidenceRecord schema, hash rule (`record_hash = sha256(canonical_json(row minus id/record_hash) + prev_hash)`), canonical JSON = sorted keys/no whitespace, genesis `prev_hash` = 64 zeros, append-only approvals.
- MASTER_SPEC.md §8A items 5–6 — Evidence record view ("Export for audit") and Audit log + integrity ("Verify chain", "Simulate tampering") are UI consumers of this store later (T17/T18); T12 only builds the underlying store, not UI.
- MASTER_SPEC.md §2 — audit records are append-only; never mutate an existing record in normal operation.
- TASK_LEDGER.md T12 entry — exact files, key notes, done-when, verify, reviewer focus (quoted below).
- AGENTS.md — non-negotiable: "Audit records are append-only", "Human approvals append a new approval_decision record", "Never mutate an existing audit record in normal operation", "Presidio, OPA, and the audit hash chain must be real."

## Allowed files
- `app/audit/models.py`
- `app/audit/store.py`
- `tests/T12_audit/` (new subfolder; Implementer adds `__init__.py` + `test_*.py`)

Do not touch any other file. In particular: do not modify `app/schemas/audit.py` (the `EvidenceRecord` Pydantic schema from T02 is already final — reuse it, don't change field names), do not wire this into `pipeline.py` (that's T13), do not build any UI (T17/T18).

## Implementation objective
Build the real, persistent audit store that the rest of the system will write every proposed action into.

1. `app/audit/models.py` — the persistence-layer representation of an audit row (e.g. a SQLAlchemy-free lightweight model, or a dataclass/Pydantic row model — follow the existing project convention of plain Python + psycopg rather than introducing an ORM, matching `app/settings_store.py`'s style: a dataclass-based store, dual sqlite/Postgres support so tests can run without Docker). The row shape must match spec §5.5 / `app/schemas/audit.py::EvidenceRecord` exactly: `id, correlation_id, action, context_used, evidence, decision, enforcement_mode, executed, record_type, references_hash, human_approver, approval_reason, created_at, record_hash, prev_hash`.
2. `app/audit/store.py` — the `AuditStore`:
   - `write_record(action, context_used, evidence, decision, enforcement_mode, executed, record_type, references_hash=None, human_approver=None, approval_reason=None) -> EvidenceRecord`: looks up the current chain tail's `record_hash` (or 64 zeros if the table is empty — genesis), computes `record_hash = sha256(canonical_json(row minus id/record_hash) + prev_hash)`, and INSERTs the new row. This is the **only** normal write path — it must never UPDATE an existing row.
   - `canonical_json(payload: dict) -> str` (or similar helper): sorted keys, no whitespace, used identically for hashing and for re-verification, so verification recomputes the exact same bytes that were hashed at write time.
   - `verify_chain() -> ChainVerificationResult` (or similar return type): walks all rows in insertion order, recomputes each row's expected `record_hash` from its stored fields + the previous row's `record_hash` (and checks `prev_hash` linkage), and returns either "intact" with the count verified, or the index/id of the first row that fails to match.
   - `simulate_tampering(record_id, ...) -> None`: a deliberately separate, clearly-named method (not used by any normal code path) that mutates a stored row in place — for the demo only. Keep it visually and structurally distinct from `write_record` (e.g. a docstring stating it exists only to demonstrate chain breakage) so a reviewer cannot mistake it for a normal write path.
   - `read_records()` / similar accessor(s) as needed to support verification and tests.
3. Follow the dual sqlite/Postgres pattern used in `app/settings_store.py` (accept an optional `database_url`; default to Postgres via `app.config.get_settings()`; allow a `sqlite:///` path for tests without Docker) so `tests/T12_audit/` can run without a live Postgres container.
4. EvidenceRecord's nested fields (`action`, `context_used`, `evidence`, `decision`) are Pydantic models from existing schemas — serialise them via their own canonical JSON (e.g. `model_dump(mode="json")`) before folding into the row's canonical JSON, so the hash is deterministic regardless of dict key insertion order.

## Non-negotiables
- Field names and types must match `app/schemas/audit.py::EvidenceRecord` / spec §5.5 exactly — do not rename, add, or remove fields.
- Genesis `prev_hash` is exactly 64 zero characters (`"0" * 64`).
- `record_hash` excludes `id` and `record_hash` itself from the hashed payload, per the spec's hash rule; it includes every other field plus the running `prev_hash`.
- Canonical JSON = sorted keys, no whitespace — and the exact same canonicalisation must be used both when writing and when verifying, or the chain will spuriously "break."
- The store must expose no method that updates/mutates a row except the explicitly-named `simulate_tampering` helper, which must be obviously separate from `write_record` and never called by any other production code path.
- Approval rows are still INSERTs of a *new* row (per §5.5/§8A item 4) — T12 does not need to special-case `record_type`; `write_record` must work identically for `action_evaluation` and `approval_decision` rows, since the caller (T13/T16) decides which to write.
- No allow/block/decision logic belongs in this module — it stores whatever `Decision` it's given; it does not interpret or re-judge it.
- Do not introduce a new ORM/dependency beyond what's already used elsewhere in the repo (psycopg is already a dependency via `settings_store.py`).
- Stay inside the three allowed files/paths. If you find you need a schema or file-layout change, stop and flag it — do not silently improvise.

## Verify step
From the ledger: "pytest `test_audit_chain.py` (built in T20) — but a quick manual run now: write 3, verify intact, tamper row 2, verify reports row 2."

For T12 itself (before T20's consolidated suite exists), the Implementer's `tests/T12_audit/test_*.py` must cover, at minimum:
- Writing N records (N ≥ 3) builds a valid chain (each `prev_hash` equals the prior row's `record_hash`; first row's `prev_hash` is 64 zeros).
- `verify_chain()` reports intact for an untampered chain, with the correct count verified.
- After `simulate_tampering()` mutates one stored row, `verify_chain()` reports that exact row as broken (and no earlier row).
- `write_record` round-trips through both an `action_evaluation` and an `approval_decision` record_type.
- Run via: `docker compose run --rm app pytest tests/T12_audit -q` (or equivalent local pytest invocation against a `sqlite:///` test database if Docker/Postgres is unavailable in the sandbox).

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T12_architect_brief.md and briefs/T12_test_brief.md. Implement exactly T12. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.