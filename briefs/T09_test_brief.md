# Test Brief — T09: OPA round-trip (prove the HTTP path before real policy)

## Spec references
- MASTER_SPEC.md: §3 (architecture), §4 (OPA technology choice), §5.4 (Decision schema), §6 (control library + framework mappings)
- TASK_LEDGER.md: T09 acceptance criteria and verify step
- AGENTS.md: non-negotiable — decision comes from OPA not Python; only Python-made decision is `fail_closed` when OPA unreachable

## Target test location
- Folder: `tests/T09_opa_client/`
- Suggested files:
  - `test_controls_json.py` — covers test cases: controls_json_structure, controls_json_framework_mappings, controls_json_fin_pay_004_proposed
  - `test_opa_roundtrip.py` — covers test cases: roundtrip_allow_decision, decision_schema_fields_complete, opa_input_contract_shape
  - `test_fail_closed.py` — covers test cases: opa_unreachable_fail_closed, fail_closed_decision_fields, opa_non_2xx_fail_closed

## Test cases

### controls_json_structure
- **Traces to:** §6 control library; T09 acceptance
- **Input:** Load `opa/data/controls.json`
- **Expected outcome:** All seven control IDs present (`FIN-PAY-001` through `FIN-PAY-004`, `COMM-EMAIL-001` through `COMM-EMAIL-003`). Each has `id`, `tier`, `decision`, `description`, `framework_mappings` (list), `required_approval_role`, `enabled`.
- **Notes:** Pure file validation — no running services needed.

### controls_json_framework_mappings
- **Traces to:** §6 framework mapping tables
- **Input:** Load `opa/data/controls.json`
- **Expected outcome:** `FIN-PAY-001` mappings include "Internal Fraud & Financial Crime Policy". `COMM-EMAIL-001` mappings include "UK GDPR Art.9 / DPA 2018". `COMM-EMAIL-003` mappings include "UK GDPR Art.5(2) accountability". Mappings match spec §6 verbatim.
- **Notes:** Spot-check representative controls across all tiers.

### controls_json_fin_pay_004_proposed
- **Traces to:** §6 FIN-PAY-004 PROPOSED note; §1B sensitivity guidance
- **Input:** Load `opa/data/controls.json`
- **Expected outcome:** `FIN-PAY-004` has `"proposed": true`. Other controls do not have a `proposed` field set to `true`.
- **Notes:** This flag is required so T10 can toggle FIN-PAY-004 without code changes.

### roundtrip_allow_decision
- **Traces to:** T09 "Done when" — client sends real request to OPA and gets back a parsed `allow` Decision
- **Input:** Any valid Action, Context, and Evidence objects (can use scenario 1 fixtures). OPA must be running.
- **Expected outcome:** Returns a `Decision` Pydantic model with `decision="allow"`.
- **Notes:** Requires real OPA container — do not mock the HTTP call.

### decision_schema_fields_complete
- **Traces to:** §5.4 Decision schema
- **Input:** Same as `roundtrip_allow_decision`.
- **Expected outcome:** Returned Decision has all required fields populated: `decision`, `control_id`, `triggered_controls`, `reason`, `required_approval_role`, `framework_mappings`, `failure_mode`, `logging_requirements`, `policy_version`, `threshold_used`. No field is missing or `None` where the trivial policy sets a value.
- **Notes:** Validates that the Rego policy returns all Decision fields and the client parses them correctly.

### opa_input_contract_shape
- **Traces to:** Architect brief — OPA input contract documented in `opa_client.py` docstring
- **Input:** Inspect the payload the client sends to OPA (can capture or reconstruct from code).
- **Expected outcome:** Payload is `{"input": {"action": {...}, "context": {...}, "evidence": {...}, "config": {"high_confidence_threshold": <number>, ...}}}`. All four top-level keys present under `input`.
- **Notes:** The contract must be stable — T10 depends on it.

### opa_unreachable_fail_closed
- **Traces to:** T09 "Done when" — killing OPA yields `fail_closed`; AGENTS.md non-negotiable
- **Input:** Any valid Action/Context/Evidence. OPA is not running (connection refused).
- **Expected outcome:** Returns `Decision(decision="fail_closed", failure_mode="fail_closed")`.
- **Notes:** Requires real connection failure — do not mock. Test can target a port where nothing listens (e.g. override OPA URL to `http://localhost:19999`).

### fail_closed_decision_fields
- **Traces to:** Architect brief fail-closed spec; §5.4
- **Input:** Same as `opa_unreachable_fail_closed`.
- **Expected outcome:** Decision has `reason` containing "unreachable" (or similar), `logging_requirements="enhanced"`, `framework_mappings` includes "Internal AI Governance Policy (safe-default)" and "ISO/IEC 42001 (robustness)", `policy_version="unknown"`, `threshold_used` equals the config threshold value.
- **Notes:** Validates the full fail-closed Decision, not just the decision field.

### opa_non_2xx_fail_closed
- **Traces to:** Architect brief — "non-2xx response" triggers fail_closed
- **Input:** Any valid inputs. OPA returns a non-2xx status (e.g. POST to an invalid OPA path, or use a mocked/bad endpoint).
- **Expected outcome:** Returns `Decision(decision="fail_closed")`.
- **Notes:** If difficult to trigger a real non-2xx from OPA, this test may use a deliberately wrong policy path or a lightweight HTTP stub. The key assertion is that the client does not silently allow on unexpected responses.

## Coverage checklist
- [x] Happy path covered (roundtrip_allow_decision, decision_schema_fields_complete)
- [x] Error/edge cases covered (opa_unreachable, non_2xx, fail_closed fields)
- [x] Spec non-negotiables verified (no Python-side decision except fail_closed; Decision schema fidelity)
- [x] Real dependencies flagged (OPA must be real for roundtrip tests; fail_closed tests use real connection failure)

## Gaps or ambiguities
- None identified. The T09 acceptance criteria are clear: prove the HTTP path works and fail-closed is real.