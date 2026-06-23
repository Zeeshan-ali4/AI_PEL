# Test Brief — T12: Audit store + hash chain (tamper-evident)

## Spec references
- MASTER_SPEC.md §5.5 — EvidenceRecord row shape, hash rule (`record_hash = sha256(canonical_json(row minus id/record_hash) + prev_hash)`), canonical JSON = sorted keys/no whitespace, genesis `prev_hash` = 64 zeros.
- MASTER_SPEC.md §5.5 — append-only approvals: `approval_decision` rows are new INSERTs referencing the original via `references_hash`; the original row is never mutated.
- MASTER_SPEC.md §2 — audit records are append-only; never mutate an existing record in normal operation.
- TASK_LEDGER.md T12 — Done when: "writing N records builds a valid chain; `verify_chain` = intact; tampering one row makes `verify_chain` report that exact row." Verify: "write 3, verify intact, tamper row 2, verify reports row 2."
- briefs/T12_architect_brief.md — `AuditStore.write_record`, `canonical_json`, `verify_chain`, `simulate_tampering`, `read_records` interfaces; dual sqlite/Postgres support; `write_record` is the only normal write path (INSERT only).

## Target test location
- Folder: `tests/T12_audit/`
- Suggested files:
  - `test_hash_chain.py` — covers `chain_builds_with_correct_linkage`, `genesis_prev_hash_is_64_zeros`, `record_hash_excludes_id_and_record_hash_fields`, `canonical_json_is_deterministic_sorted_no_whitespace`
  - `test_verify_chain.py` — covers `verify_chain_reports_intact_with_correct_count`, `verify_chain_reports_intact_on_empty_store`
  - `test_tampering.py` — covers `simulate_tampering_breaks_chain_at_exact_row`, `tampering_does_not_affect_earlier_rows`, `verify_chain_stops_at_first_broken_row`
  - `test_record_types.py` — covers `write_record_round_trips_action_evaluation`, `write_record_round_trips_approval_decision_with_references_hash`
  - `test_append_only.py` — covers `store_exposes_no_update_path_besides_simulate_tampering`, `write_record_never_mutates_existing_rows`

## Test cases

### chain_builds_with_correct_linkage
- **Traces to:** §5.5 hash rule; TASK_LEDGER T12 Done-when
- **Input:** Call `write_record(...)` three times with distinct valid `Action`/`Context`/`Evidence`/`Decision` fixtures (reuse fixtures consistent with T02 schema tests), `enforcement_mode="full"`, `executed=True/False` mixed, `record_type="action_evaluation"`.
- **Expected outcome:** Row 1's `prev_hash` == `"0" * 64`. Row 2's `prev_hash` == row 1's `record_hash`. Row 3's `prev_hash` == row 2's `record_hash`. All three `record_hash` values are distinct, valid lowercase hex SHA-256 strings (64 chars).
- **Notes:** This is the core "write N records builds a valid chain" assertion from the Verify step.

### genesis_prev_hash_is_64_zeros
- **Traces to:** §5.5 — "genesis `prev_hash` = 64 zeros"
- **Input:** Fresh empty store (new sqlite test DB); call `write_record` once.
- **Expected outcome:** The returned/stored row's `prev_hash` is exactly `"0" * 64` (64 ASCII zero characters).
- **Notes:** Must use a freshly-initialised store (no prior rows) — not a reused fixture DB.

### record_hash_excludes_id_and_record_hash_fields
- **Traces to:** §5.5 hash rule — "row minus id/record_hash"
- **Input:** Write a record; independently recompute `sha256(canonical_json(row_with_id_and_record_hash_removed) + prev_hash)` using the same field values the store wrote.
- **Expected outcome:** The independently recomputed hash equals the stored `record_hash` exactly.
- **Notes:** This proves the hash payload genuinely excludes `id`/`record_hash` per the spec rule (not just that the chain "looks" linked) — guards against an implementation that includes `id` and only coincidentally passes the linkage test.

### canonical_json_is_deterministic_sorted_no_whitespace
- **Traces to:** §5.5 — "canonical JSON = sorted keys, no whitespace"
- **Input:** Call the store's canonical JSON helper twice on two dicts with identical keys/values but different insertion order (e.g. `{"b": 1, "a": 2}` vs `{"a": 2, "b": 1}`).
- **Expected outcome:** Both calls return byte-identical strings; the output contains no space/newline characters between tokens (e.g. no `", "` or `": "` separators — check for `" "` absence outside of string values, or assert output matches `json.dumps(d, sort_keys=True, separators=(",", ":"))`).
- **Notes:** Critical non-negotiable from the architect brief — write-time and verify-time canonicalisation must produce identical bytes or the chain spuriously breaks.

### verify_chain_reports_intact_with_correct_count
- **Traces to:** TASK_LEDGER T12 Done-when / Verify step
- **Input:** Write 3 valid records; call `verify_chain()`.
- **Expected outcome:** Result indicates intact/no break, and reports a verified count of 3.
- **Notes:** Assert on whatever the architect's `ChainVerificationResult`-equivalent return type exposes (e.g. `.intact is True`, `.verified_count == 3`, `.broken_record_id is None` or equivalent field names — Implementer documents exact field names; this test asserts the underlying truth values regardless of exact attribute naming, but the QA agent should confirm the attribute names match between brief and test).

### verify_chain_reports_intact_on_empty_store
- **Traces to:** §5.5 (degenerate case); general robustness
- **Input:** Fresh store with zero records; call `verify_chain()`.
- **Expected outcome:** Result indicates intact with a verified count of 0 (must not raise an exception or crash on empty chain).
- **Notes:** Edge case — empty chain must not be mistaken for a broken chain.

### simulate_tampering_breaks_chain_at_exact_row
- **Traces to:** TASK_LEDGER T12 Verify step — "tamper row 2, verify reports row 2"
- **Input:** Write 3 valid records (ids/positions 1, 2, 3). Call `simulate_tampering(record_id=<row2's id>, ...)` to mutate a field on row 2 (e.g. alter `executed` or a field inside `decision`/`evidence`). Call `verify_chain()`.
- **Expected outcome:** `verify_chain()` reports the broken record as exactly row 2's id/position — not row 1 or row 3, and not a generic "chain broken" with no row identified.
- **Notes:** This is the literal scenario from the ledger's Verify step and the single most important assertion in this task — must use a real mutation against the real stored row, not a mocked store.

### tampering_does_not_affect_earlier_rows
- **Traces to:** §5.5 — append-only / tamper-evidence semantics
- **Input:** Same setup as above; after tampering row 2, separately verify that row 1's stored `record_hash`/`prev_hash` are unchanged from what was originally written.
- **Expected outcome:** Row 1 is bit-for-bit identical to its pre-tampering state; only row 2's targeted field changed.
- **Notes:** Confirms `simulate_tampering` is scoped to the single targeted row and isn't, e.g., accidentally recomputing/rewriting the whole chain.

### verify_chain_stops_at_first_broken_row
- **Traces to:** §5.5; architect brief — "returns ... the index/id of the first row that fails to match"
- **Input:** Write 4 records; tamper row 2 only; call `verify_chain()`.
- **Expected outcome:** Reported broken row is row 2 (the first failure), not row 3 or row 4 even though their `prev_hash` linkage is now also technically inconsistent relative to a re-hashed row 2.
- **Notes:** Confirms the "first broken index" contract from the architect brief, not just "some row is broken."

### write_record_round_trips_action_evaluation
- **Traces to:** §5.5; AGENTS.md non-negotiable "Audit records are append-only"
- **Input:** Call `write_record(..., record_type="action_evaluation", references_hash=None, human_approver=None, approval_reason=None, executed=False)` with an `escalate` Decision fixture.
- **Expected outcome:** Stored/returned row has `record_type == "action_evaluation"`, `references_hash is None`, `human_approver is None`, `approval_reason is None`, and all other fields match the EvidenceRecord schema's field names from `app/schemas/audit.py` exactly.
- **Notes:** Validate the returned object can be parsed into/matches `EvidenceRecord` field-for-field (no renamed/missing/extra fields).

### write_record_round_trips_approval_decision_with_references_hash
- **Traces to:** §5.5 — "Human approvals append a new `approval_decision` record"; AGENTS.md non-negotiable
- **Input:** Write an initial `action_evaluation` record (escalate, `executed=False`). Then call `write_record(..., record_type="approval_decision", references_hash=<first record's record_hash>, human_approver="finance_supervisor", approval_reason="approved per policy exception", executed=True, correlation_id=<same correlation_id as the original>)`.
- **Expected outcome:** Second row is a new row (new `id`, new `record_hash`, `prev_hash` == first row's `record_hash`) with `references_hash` equal to the first row's `record_hash`, same `correlation_id` as the original, and the first row's stored fields are completely unchanged (re-read it and diff against what was written initially).
- **Notes:** This is the literal "append-only approval" non-negotiable from AGENTS.md and §5.5/§8A item 4 — must prove via re-read, not just by trusting the return value, that the original row was not mutated.

### store_exposes_no_update_path_besides_simulate_tampering
- **Traces to:** AGENTS.md — "Never mutate an existing audit record in normal operation"; architect brief — "store must expose no method that updates/mutates a row except the explicitly-named `simulate_tampering` helper"
- **Input:** Inspect `AuditStore`'s public method surface (e.g. via `dir()` or `inspect`).
- **Expected outcome:** No method other than `simulate_tampering` (by name, clearly labelled per the architect brief) performs an UPDATE/mutation of an existing row. `write_record` only INSERTs.
- **Notes:** This can be a structural/behavioural test (e.g. assert calling `write_record` twice never changes a previously-written row's hash) combined with a name-based sanity check that `simulate_tampering` is distinctly named and documented as demo-only (e.g. assert its docstring is non-empty and mentions tampering/demo).

### write_record_never_mutates_existing_rows
- **Traces to:** §2 non-negotiable
- **Input:** Write 5 records sequentially, capturing a full snapshot (all fields) of every row after each write.
- **Expected outcome:** After each new `write_record` call, all previously-captured snapshots remain byte-identical to their current stored state.
- **Notes:** Regression guard against any write path that re-touches prior rows (e.g. an off-by-one update during chain-tail lookup).

## Coverage checklist
- [x] Happy path covered (chain build, verify intact, both record types round-trip)
- [x] Error/edge cases covered (empty store verify, tamper detection at exact + first-broken row, append-only enforcement)
- [x] Spec non-negotiables verified (genesis 64 zeros, canonical JSON determinism, hash excludes id/record_hash, append-only approvals, no mutation outside `simulate_tampering`)
- [x] Real dependencies flagged (see below)

## Real-dependency note
Per AGENTS.md ("Presidio, OPA, and the audit hash chain must be real") and the architect brief's dual sqlite/Postgres pattern: these tests must run against a real `AuditStore` instance backed by a real database connection (sqlite file or in-memory `sqlite:///` for CI/sandbox speed is acceptable per the architect brief — this is a real DB engine, not a mock of the store's hashing/verification logic). Do not mock `write_record`, `verify_chain`, or `simulate_tampering` — the hashing and chain-walking logic itself must execute for real in every test.

## Gaps or ambiguities
- The architect brief leaves the exact return-type shape of `verify_chain()` (attribute names for "intact", "verified count", "broken row id") to the Implementer's discretion ("or similar return type"). Test cases above are written against the underlying truth values the Implementer must expose; QA should confirm the Implementer's chosen attribute names are self-documenting and consistent across `verify_chain`'s passing and failing return paths before signing off.
- No ambiguity in the core hash-chain/tamper-detection acceptance criteria — these are explicit and unambiguous in TASK_LEDGER.md's Verify step and MASTER_SPEC.md §5.5.