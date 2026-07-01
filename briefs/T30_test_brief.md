# Test Brief — T30: Reporting dashboard summary view

## Spec references
- MASTER_SPEC.md: §8B (reporting page — added in v1.3), §8A (UI/UX tone, labelling conventions), §5.5 (EvidenceRecord schema — read-only, no new fields), §6 (control library — names/tiers come from controls.json), §9 (assurance narrative), §12 (acceptance criteria)
- TASK_LEDGER.md: T30 — Done-when, Verify step, Reviewer focus
- briefs/T30_architect_brief.md: full implementation spec; five sections, allowed files, non-negotiables

## Target test location
- Folder: `tests/T30_reporting/`
- Suggested files:
  - `__init__.py` — empty init (required)
  - `test_reporting_data.py` — covers TC-01 through TC-09 (aggregation logic in `reporting.py`)
  - `test_reporting_routes.py` — covers TC-10 through TC-16 (HTTP routes and template rendering)

---

## Test cases

### TC-01 — Summary cards: correct KPI counts for a known record set
- **Traces to:** TASK_LEDGER.md T30 "Done when" item 1; architect brief §Summary cards
- **Input:** Write a controlled set of `EvidenceRecord` rows directly to the test DB — e.g. 2 `allow`, 1 `allow_with_logging`, 2 `escalate`, 1 `block`, 1 `fail_closed`. Call `get_report(session, "all")`.
- **Expected outcome:**
  - `summary["total_evaluated"]` == 7
  - `summary["total_allowed"]` == 3 (allow + allow_with_logging)
  - `summary["total_escalated"]` == 2
  - `summary["total_blocked"]` == 2 (block + fail_closed)
- **Notes:** Use real Postgres (not mocks). This tests the exact grouping logic described in the architect brief — `block` and `fail_closed` both count toward `total_blocked`.

### TC-02 — Decision breakdown table: correct rows and percentages
- **Traces to:** architect brief §Decision breakdown table
- **Input:** Same record set as TC-01. Read `report["decision_breakdown"]`.
- **Expected outcome:**
  - Contains a row for `allow` with count 2 and percentage 2/7 ≈ 28.6%
  - Contains a row for `allow_with_logging` with count 1
  - Contains a row for `escalate` with count 2
  - Contains a row for `block` with count 1
  - Contains a row for `fail_closed` with count 1
  - Each row has `count` and `percentage` fields
- **Notes:** All five decision types have counts > 0 in this set, so all five rows must appear. Percentages must sum to 100% (allow for floating-point rounding).

### TC-03 — Decision breakdown table: zero-count rows are omitted
- **Traces to:** architect brief non-negotiable "Omit zero-count rows"
- **Input:** Write only `allow` and `escalate` records. Call `get_report(session, "all")`.
- **Expected outcome:** `report["decision_breakdown"]` contains exactly 2 rows — no rows for `block`, `fail_closed`, or `allow_with_logging`.
- **Notes:** The brief explicitly requires omitting zero rows; this test guards against an implementation that always returns all five rows.

### TC-04 — Control activity table: correct firing counts and ordering
- **Traces to:** architect brief §Control activity table; MASTER_SPEC.md §6 (control IDs)
- **Input:** Write records where `decision.triggered_controls` includes `["FIN-PAY-002"]` three times and `["COMM-EMAIL-001"]` once. Call `get_report(session, "all")`.
- **Expected outcome:**
  - `report["control_activity"]` has two rows
  - FIN-PAY-002 row: count == 3, appears first (ordered by count descending)
  - COMM-EMAIL-001 row: count == 1, appears second
  - Each row includes `control_id`, `name` (from controls.json, not hardcoded), `tier`, `count`, and `most_recent` timestamp
- **Notes:** Control names must be sourced from `opa/data/controls.json` — the test can validate that the name matches what is in that file. Use real Postgres.

### TC-05 — Escalation resolution summary: pending vs resolved counts
- **Traces to:** architect brief §Escalation resolution summary; MASTER_SPEC.md §5.5 (append-only approvals)
- **Input:**
  - Write two `action_evaluation` records with `decision.decision == "escalate"`.
  - For one of them, write a linked `approval_decision` record with the same `correlation_id`.
  - Call `get_report(session, "all")`.
- **Expected outcome:**
  - `report["escalation_summary"]["resolved"]` == 1
  - `report["escalation_summary"]["pending"]` == 1
  - `report["escalation_summary"]["pending_items"]` contains exactly one item (the unresolved escalation's `correlation_id` and action summary)
- **Notes:** The pending check must use a DB-level join/subquery — not Python-side filtering. This is testable by confirming the correct pending count even with a large number of records.

### TC-06 — Period filter: `today` scopes records to current UTC date
- **Traces to:** TASK_LEDGER.md T30 Verify step item 3; architect brief §period param
- **Input:** Write one record with `created_at` = now (UTC), one with `created_at` = 8 days ago. Call `get_report(session, "today")`.
- **Expected outcome:** `summary["total_evaluated"]` == 1 (only the record from today).
- **Notes:** Use real Postgres with actual timestamp values. The cutoff for `today` is the start of the current UTC day.

### TC-07 — Period filter: `7d` and `30d` cutoffs are correct
- **Traces to:** TASK_LEDGER.md T30 Verify step item 3; architect brief §period param
- **Input:** Write records at now, 6 days ago, 8 days ago, 29 days ago, 31 days ago. Call `get_report` with each period value.
- **Expected outcome:**
  - `7d`: count == 2 (now + 6 days ago)
  - `30d`: count == 4 (now + 6 + 8 + 29 days ago)
  - `all`: count == 5
- **Notes:** Parameterised SQLAlchemy filters only — no string interpolation.

### TC-08 — Empty state: no records returns zero counts, not an error
- **Traces to:** architect brief non-negotiable "Empty states must be handled gracefully"; TASK_LEDGER.md T30 "Done when" item 5
- **Input:** Empty database (no records). Call `get_report(session, "all")`.
- **Expected outcome:**
  - `summary["total_evaluated"]` == 0
  - `report["decision_breakdown"]` == [] (empty list, not an error)
  - `report["control_activity"]` == []
  - `report["escalation_summary"]["resolved"]` == 0
  - `report["escalation_summary"]["pending"]` == 0
  - Function does not raise any exception
- **Notes:** This guards against division-by-zero on percentages and NULL-related DB errors when no rows exist.

### TC-09 — Chain integrity: `get_report` returns last verify result
- **Traces to:** architect brief §Chain-integrity status; TASK_LEDGER.md T30 Verify step item 4
- **Input:** Write 3 valid records (intact chain). Call `store.verify_chain()` externally. Then call `get_report(session, "all")`.
- **Expected outcome:** `report["chain_status"]` contains `intact=True` and a `verified_count` of at least 3 (or whatever `verify_chain()` returns).
- **Notes:** `get_report` itself does not call `verify_chain()` — it reads the status that the route has already obtained. This test should call `verify_chain()` and confirm its output shape so the route can pass it to the template. If `reporting.py` does not hold chain status internally, test the route instead (TC-15).

### TC-10 — GET /reporting renders 200 with all five sections
- **Traces to:** TASK_LEDGER.md T30 Verify step items 1–2; architect brief §routes
- **Input:** Run all six scenarios via `/run/1` through `/run/6` (real pipeline). Then `GET /reporting`.
- **Expected outcome:**
  - HTTP 200
  - Response HTML contains: summary card section, decision breakdown table, control activity table, escalation resolution summary, chain-integrity status section
  - HTML contains the text "Illustrative period summary — covers actions evaluated by this demo deployment."
  - Decision counts match the number of scenarios run (6 total evaluated)
- **Notes:** Uses a real running app (FastAPI TestClient or live server). Real Postgres, real OPA. This is the acceptance-level smoke test.

### TC-11 — GET /reporting?period= filters counts correctly
- **Traces to:** TASK_LEDGER.md T30 Verify step item 3
- **Input:** Write records across different timestamps (same approach as TC-07). `GET /reporting?period=today`, `GET /reporting?period=7d`, `GET /reporting?period=30d`, `GET /reporting?period=all`.
- **Expected outcome:** Each response's summary card shows the count matching the expected set for that period. The period selector `<select>` shows the active period as selected.
- **Notes:** Test with FastAPI TestClient against a real Postgres instance with seeded data.

### TC-12 — GET /reporting?period= defaults to 30d when param is absent
- **Traces to:** architect brief "default `30d`"
- **Input:** `GET /reporting` (no period param).
- **Expected outcome:** Response is 200; the `30d` option is shown as selected in the period selector; counts match the 30-day window.

### TC-13 — GET /reporting?period= rejects invalid values gracefully
- **Traces to:** architect brief non-negotiable on empty states / error handling
- **Input:** `GET /reporting?period=xyz`.
- **Expected outcome:** Either HTTP 200 (defaulting to `30d`) or HTTP 422 — but NOT a 500. No unhandled exception.

### TC-14 — GET /reporting/verify calls store.verify_chain() and redirects
- **Traces to:** TASK_LEDGER.md T30 Verify step item 4; architect brief §routes
- **Input:** Write 3 records (intact chain). `GET /reporting/verify`.
- **Expected outcome:**
  - HTTP 302/307 redirect to `/reporting` (with `chain_ok=true` and `chain_count=3` or similar query params)
  - Following the redirect: the page shows a green "chain intact" result with the count
- **Notes:** The "Verify now" form must use `method="get"` per the architect brief — no POST endpoint.

### TC-15 — GET /reporting/verify reports broken chain correctly
- **Traces to:** TASK_LEDGER.md T30 Verify step item 4; architect brief §Chain-integrity status
- **Input:** Write 3 records; use `store.simulate_tampering()` to alter record 2. `GET /reporting/verify`.
- **Expected outcome:**
  - Redirect to `/reporting` with `chain_ok=false` and `chain_broken_at=<id of broken record>` (or equivalent)
  - Following the redirect: the page shows a red "chain broken" result naming the broken record
- **Notes:** `store.simulate_tampering()` exists from T12. This verifies the "Verify now" button surfaces real tamper detection, not a hardcoded pass.

### TC-16 — Pending escalation count updates after approval
- **Traces to:** TASK_LEDGER.md T30 Verify step item 5; MASTER_SPEC.md §5.5 (append-only approvals)
- **Input:**
  1. Run Scenario #2 via `/run/2` (produces an `escalate` decision).
  2. `GET /reporting` → confirm "pending escalations" == 1.
  3. Approve the escalation via the approval queue (POST to the approval endpoint with a reason).
  4. `GET /reporting` → confirm "pending escalations" == 0 and "resolved escalations" == 1.
- **Expected outcome:** Counts update correctly between steps 2 and 4, reflecting the new `approval_decision` record. The original `action_evaluation` row is unchanged.
- **Notes:** This is an end-to-end acceptance test using the real pipeline and approval workflow. Validates that the escalation resolution query correctly picks up the newly appended approval record.

---

## Coverage checklist
- [x] Happy path covered (TC-01, TC-02, TC-04, TC-05, TC-10)
- [x] Error/edge cases covered (TC-03, TC-08, TC-13)
- [x] Spec non-negotiables verified (TC-03 zero-row omission; TC-08 empty state; TC-14/15 real chain check; TC-16 append-only approvals)
- [x] Real dependencies flagged (no mocks where forbidden — TC-01 through TC-09 use real Postgres; TC-10 through TC-16 use real FastAPI TestClient with real Postgres and OPA)

---

## Gaps or ambiguities

1. **`chain_status` ownership:** The architect brief states that `get_report` returns `chain_status`, but also says the route calls `store.verify_chain()` and the simplest implementation redirects with the result in query params. It is ambiguous whether `get_report` itself calls `verify_chain()` on every page load (expensive) or whether `chain_status` in the report reflects the last explicitly-triggered verify. The Implementer should clarify: if `verify_chain()` is called on every `GET /reporting`, TC-09 can be tested via `get_report` directly; if not, TC-09 should be replaced with testing the `/reporting/verify` redirect (TC-14/15 cover this). Either choice is acceptable; the test file should adapt accordingly. Recommend: only call `verify_chain()` on explicit `GET /reporting/verify`, and show "not yet verified" if no verify has run this session.

2. **`controls.json` tier field:** TC-04 asserts the `tier` field on control activity rows. Confirm that `opa/data/controls.json` carries a `tier` field per control (the dashboard already reads tiers from this file for T14, so it should be present — but worth confirming before the Implementer writes the query).

3. **`most_recent` timestamp source:** For control activity (TC-04), "most recent timestamp" should be the `created_at` of the latest record in the period where that control fired. Confirm this with the Implementer — it should be derivable as `MAX(created_at)` in the SQLAlchemy aggregation.

4. **`pending_items` shape:** TC-05 asserts `pending_items` contains a `correlation_id` and action summary. The exact shape (a list of dicts vs list of small dataclasses) is an implementation detail; the test should assert at minimum that each item has a `correlation_id` field and some human-readable action description, not a specific dict key name.
