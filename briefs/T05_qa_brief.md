# QA Report — T05: Context resolver + fixtures

## Verdict
PASS

## Ledger verification
- Command run: `docker compose run --rm app python - <<'PY' ... PY`
- Result: not run — `docker` CLI is unavailable in this environment (`/bin/bash: line 1: docker: command not found`). Closest inspection performed with the same Python scenario-print script locally, which passed and printed resolved Context objects for scenarios 1–6. Spot checks passed: scenario 3 has `customer.fraud_flag=True`; scenarios 4, 5, and 6 have `recipient.is_external=True`; all six have `context_resolution_ok=True`.

## Test suite results
- Command run: `pytest tests/T05_context/ -v`
- Total: 11 | Passed: 11 | Failed: 0 | Errors: 0
- Output summary: `collected 11 items`; all tests in `test_context_failure.py`, `test_context_resolution.py`, and `test_fixture_labels.py` passed; final line: `11 passed in 0.25s`.

## Test brief coverage

### File structure
| Brief suggested file | Actual file | Status |
|---------------------|-------------|--------|
| `test_context_resolution.py` | `tests/T05_context/test_context_resolution.py` | ok |
| `test_context_failure.py` | `tests/T05_context/test_context_failure.py` | ok |
| `test_fixture_labels.py` | `tests/T05_context/test_fixture_labels.py` | ok |

### Case-by-case coverage
| Brief test case | Implementing test function | File | Covered? | Notes |
|----------------|--------------------------|------|----------|-------|
| `test_resolves_clean_low_value_payment_context_for_scenario_1` | `test_resolves_clean_low_value_payment_context_for_scenario_1` | `tests/T05_context/test_context_resolution.py` | yes | Uses `get_raw_tool_call(1)`, normalises it, resolves context, asserts `Context`, clean `CUST-100`, payment-history threshold, no approval, financial-standing flag, deterministic business hours, and `context_resolution_ok=True`. |
| `test_resolves_high_value_payment_without_approval_for_scenario_2` | `test_resolves_high_value_payment_without_approval_for_scenario_2` | `tests/T05_context/test_context_resolution.py` | yes | Uses scenario 2, asserts clean `CUST-100`, no fraud/sanctions/blocked status, absent approval fields, successful context, and payment amount remains on `action.parameters`. |
| `test_resolves_fraud_flag_payment_for_scenario_3` | `test_resolves_fraud_flag_payment_for_scenario_3` | `tests/T05_context/test_context_resolution.py` | yes | Uses scenario 3, asserts `CUST-300`, valid flagged status, `fraud_flag=True`, financial-standing flag, and successful context without asserting any decision output. |
| `test_resolves_external_gmail_without_disclosure_basis_for_scenario_4` | `test_resolves_external_gmail_without_disclosure_basis_for_scenario_4` | `tests/T05_context/test_context_resolution.py` | yes | Uses scenario 4, asserts `CUST-200`, external Gmail domain, no approved disclosure basis, email financial-standing flag false, and successful context. |
| `test_resolves_external_adviser_disclosure_basis_for_scenario_5` | `test_resolves_external_adviser_disclosure_basis_for_scenario_5` | `tests/T05_context/test_context_resolution.py` | yes | Uses scenario 5, asserts `CUST-250`, external `example.org`, approved disclosure basis preserved as true, email financial-standing flag false, and successful context. |
| `test_resolves_known_partner_recipient_for_scenario_6` | `test_resolves_known_partner_recipient_for_scenario_6` | `tests/T05_context/test_context_resolution.py` | yes | Uses scenario 6, asserts external known-partner domain, approved disclosure basis true, `CUST-100`, email financial-standing flag false, and successful context. |
| `test_all_scenarios_return_schema_valid_context_objects` | `test_all_scenarios_return_schema_valid_context_objects` | `tests/T05_context/test_context_resolution.py` | yes | Loops scenarios 1–6, asserts each result is canonical `Context` and that dumped top-level keys exactly match §5.2. |
| `test_forced_resolution_failure_returns_valid_fail_closed_context` | `test_forced_resolution_failure_returns_valid_fail_closed_context` | `tests/T05_context/test_context_failure.py` | yes | Calls `resolve(action, force_failure=True)`, asserts valid `Context`, `context_resolution_ok=False`, nested placeholders are present, and payment financial-standing flag remains correct. |
| `test_unknown_customer_or_missing_required_fixture_returns_failed_context` | `test_unknown_customer_or_missing_required_fixture_returns_failed_context` | `tests/T05_context/test_context_failure.py` | yes | Copies a valid Action with unknown `resource.id`, resolves it, and asserts valid failed Context with requested unknown id preserved and nested objects validating. |
| `test_no_policy_decision_fields_or_decision_logic_in_context_output` | `test_no_policy_decision_fields_or_decision_logic_in_context_output` | `tests/T05_context/test_context_failure.py` | yes | Resolves payment and email contexts, asserts no decision/enforcement-style keys, and confirms resolver returns `Context` objects rather than policy tuples. |
| `test_fixtures_are_labelled_as_demo_enterprise_stand_ins` | `test_fixtures_are_labelled_as_demo_enterprise_stand_ins` | `tests/T05_context/test_fixture_labels.py` | yes | Inspects concrete fixture metadata constants and verifies demo-fixture/stand-in labels for IAM, CRM, fraud, sanctions, payment history, approval, and disclosure-basis systems. |

### Extra tests (Implementer-added)
- None beyond the PM/BA brief cases; the Implementer mapped all 11 brief cases one-to-one.

## Spec non-negotiable checks
- Exact Context schema use: passed — resolver returns `app.schemas.context.Context` objects and tests assert the exact §5.2 top-level fields.
- No decision/enforcement/approval leakage in context output: passed — tests assert no `decision`, `allow`, `block`, `escalate`, `control_id`, `approval_role`, `required_approval_role`, `executed`, or `enforcement` keys.
- No policy logic in Python context resolver: passed — resolver only composes fixture-backed context and failure state; no Decision object or policy decision strings are returned.
- Fixture-backed resolution is visibly labelled: passed — fixture module exposes `DEMO_FIXTURE_NOTICE` and `FIXTURE_SYSTEM_LABELS` naming stand-ins for IAM, CRM, fraud, sanctions, payment-history, approval, and disclosure-basis systems.
- Forced failure / fail-closed context path: passed — `resolve(action, force_failure=True)` returns a valid Context with `context_resolution_ok=False`.
- Unknown or missing required fixture path: passed — unknown customer id returns a valid failed Context instead of a fabricated successful clean context.
- Real component boundary: passed — T05 intentionally uses fixtures only and does not require OPA, Presidio, Postgres, enforcement, audit, UI, network calls, or enterprise connectors.

## Failures
- None.

## Recommendation
Proceed to human approval. Do not mark T05 `DONE` until the human gate accepts the task and the unavailable Docker-based verification is either accepted as an environment limitation or rerun in an environment with Docker.
