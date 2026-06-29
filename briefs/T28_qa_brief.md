# QA Brief — T28: Evidence sufficiency checklist (record view)

## Verdict: PASS

## Scope check
Files touched match the architect brief exactly: `app/audit/sufficiency.py` (new, pure), `app/web/routes.py` (context wiring only), `app/web/templates/record.html` (new section), and `tests/T28_evidence_sufficiency/` (`__init__.py`, `conftest.py`, `test_sufficiency.py`, `test_record_view_sufficiency.py`). No schema, migration, policy/Rego, or persistence files touched. `git status` is clean — all T28 work already committed (`0a8c5bc`, `a17ef08`).

## Test execution
Docker/OPA/Postgres are not available in this QA sandbox (no Docker daemon), so ran via local Python 3.11 with dependencies installed from `requirements.txt`:

```
python3 -m pytest -q tests/T28_evidence_sufficiency/
11 passed, 1 warning in 0.45s
```

Full repo regression run:

```
python3 -m pytest -q tests/
185 passed, 103 skipped, 2 failed, 4 errors
```

The 2 failures (`tests/T15_scenarios_ui/test_scenario_runner.py`) and 4 errors (`tests/test_policy_decisions.py`) are all caused by missing live Postgres connectivity (`psycopg.OperationalError: Name or service not known`) in this sandbox, not by T28 code. None of the failing tests import or exercise `app/audit/sufficiency.py` or the record-view checklist. Pre-existing infra limitation, not a regression.

## Coverage against PM/BA Test Brief
All 10 specified test cases are present and pass:
- allow record → core items met, human oversight not-applicable
- allow_with_logging → framework mapping met via Decision fields
- clean allow, no triggered control → mapping not-applicable (not missing)
- pending escalation (no linked approval) → human oversight pending/missing
- approved escalation (real linked `approval_decision`, matched by `correlation_id` + `references_hash`) → human oversight met
- `approval_decision` record type → evaluated on its own fields, not penalised for action-only fields
- fail_closed → rationale/chain reported from real fields; not auto-failed for the component failure
- incomplete record → only genuinely absent fields reported missing
- purity test → no DB/OPA/Presidio calls, no mutation
- record-view rendering → checklist + "Illustrative sufficiency check, not a compliance certification" label present, alongside the preserved T26 regulator-questions panel; pending→met transition after a real approval append verified end-to-end through the route

## Non-negotiables verified
- No new `EvidenceRecord` schema field (reserved for T29) — confirmed, `sufficiency.py` only reads existing fields.
- No scenario-number special-casing in `sufficiency.py` — confirmed by code review, branching is only on `record_type`/`decision`/field presence.
- Illustrative/non-certification label is unmissable in `record.html:161`.
- T26 regulator-questions partial preserved, not duplicated or removed (`record.html:158`).

## Outstanding items
None. Recommend marking T28 `DONE` in `TASK_LEDGER.md` (human gate decision per `AGENTS.md`).
