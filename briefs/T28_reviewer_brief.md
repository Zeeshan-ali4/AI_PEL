# Reviewer Brief — T28: Evidence sufficiency checklist (record view)

## Verdict: APPROVE

## Files touched (matches architect brief exactly)
- `app/audit/sufficiency.py` (new)
- `app/web/routes.py` (context wiring only)
- `app/web/templates/record.html` (new section)
- `tests/T28_evidence_sufficiency/` (`__init__.py`, `conftest.py`, `test_sufficiency.py`, `test_record_view_sufficiency.py`)

No schema, migration, policy/Rego, or persistence files were touched. No scope creep.

## Purity check — `app/audit/sufficiency.py`
- `build_sufficiency_checklist(record, linked_approval_records=None)` is a pure function: no DB session, no OPA/HTTP calls, no Presidio, no mutation of inputs. Linked approvals are supplied by the caller (route), not queried internally.
- No scenario-number special-casing anywhere in the module — all branching is on `record_type`, `decision.decision`, presence/emptiness of fields, and matching `references_hash`/`correlation_id` for approval linkage.
- Five items returned: interception, decision rationale, control/framework mapping, chain position, human oversight — matches the architect brief's required minimum set.

## Correctness spot-checks
- Clean `allow` with no triggered control → control-mapping item is `not-applicable`, not `missing` (test confirms, code at `_control_mapping_item` checks `decision_value == "allow" and not control_id and not triggered`).
- `escalate` with no linked approval → `human_oversight` = `pending`, citing the required role; once a correctly-linked `approval_decision` (matching `references_hash` + `correlation_id`, with approver/reason/executed present) is supplied → `met`. This is exercised end-to-end through the real route in `routes.py:802-822`, which derives `linked_approvals` from the actual persisted record list rather than from any scenario logic.
- `approval_decision` records are evaluated on their own fields (`references_hash`, `human_approver`, `approval_reason`, `executed`) rather than being penalised for lacking action-only fields.
- `fail_closed` is not specially penalised — rationale/chain items are assessed from actual `decision.reason`/hashes; human oversight falls out of `required_approval_role`/`decision` value, not a fail-closed special case.

## Template / UX
- `record.html:160-179` adds a clearly bordered section with an unmissable eyebrow label: "Illustrative sufficiency check, not a compliance certification." — matches the existing framework-mapping disclaimer convention.
- The existing T26 regulator-questions partial (`_regulator_questions.html`) is preserved immediately above the new section, not duplicated or removed.
- Status colour-coding (met/not-applicable/pending/missing) is visually distinct and uses `data-sufficiency-status` attributes, which is what the route/template test asserts against.

## Test results
Ran the task's own test folder directly (Docker/Postgres unavailable in this review sandbox, so ran via local venv with `DATABASE_URL=sqlite:///:memory:`, which the test fixtures already support via `AuditStore`/`SettingsStore` sqlite URLs):

```
DATABASE_URL="sqlite:///:memory:" pytest -q tests/T28_evidence_sufficiency/
11 passed
```

Covers: allow (met + N/A human oversight), allow_with_logging via framework mapping, no-control allow (N/A), pending escalation, approved escalation via real linked approval, approval_decision record shape, fail_closed, incomplete record (missing fields reported honestly), purity/no-side-effects, and two route-level rendering tests (checklist + label present; pending→met transition after a real approval append).

Ran the full repo test suite for regression: 185 passed, 2 pre-existing failures in `T15_scenarios_ui` and 4 pre-existing errors in `test_policy_decisions.py` due to missing live Postgres/OPA infrastructure in this sandbox — unrelated to T28 and reproducible on `main` before this change (no sufficiency-related files involved in those failures).

## Outstanding items
None. Ready for QA.
