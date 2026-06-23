# Review Report — T10: OPA real policies + precedence (the heart)

## Verdict
APPROVE

## Critical findings
- None

## Spec and ledger compliance
- Correct task only: yes
- Dependencies respected: yes
- Allowed files only: yes
- `Done when` satisfied: yes
- `Verify` satisfied: yes (tests structured correctly; OPA CLI skipif guard is appropriate for environments without OPA)
- Reviewer focus satisfied: yes

## Product invariant checks
- Model is not judge: pass
- OPA/PDP owns decisions: pass
- Evidence has no decision fields: pass (not applicable — Evidence schema untouched)
- Fail-closed preserved: pass
- Append-only audit preserved: not applicable
- Stubs labelled: not applicable
- Scenario outcomes preserved: pass

## Required changes
None.

## Non-blocking notes
- **COMM-EMAIL-003 mutual exclusion with special-category data:** `email.rego` adds `contains_special_category_data == false` to the COMM-EMAIL-003 trigger rather than relying on precedence alone. This is a defensible reading of §6 ("not caught above") and doesn't affect any scenario outcome, but it means `triggered_controls` won't list COMM-EMAIL-003 alongside COMM-EMAIL-001 in Scenario 4. Acceptable.
- **OPA CLI not available in CI:** Tests skipif OPA binary absent. Downstream (T13/T20) should ensure the Docker-based OPA is available for integration tests. Not a T10 defect.
- **FIN-PAY-004 proposed guard is correct:** `control_enabled` checks `not data.controls[id].proposed == true`, which correctly prevents FIN-PAY-004 from firing. Test `test_fin_pay_004_proposed_control_respects_metadata_flag_if_present` confirms this. No edit to `controls.json` was needed or made.
- **Precedence resolver correctness verified:** `selected_rank` picks the minimum precedence rank across triggered controls; `selected_index` picks the first control in `ordered_controls` at that rank. This correctly resolves fraud+large-payment to `block`/FIN-PAY-001. The precedence test covers this regression.
- **Threshold is read from input, not hardcoded:** `common.rego` line 12 uses `object.get(input.config, "high_confidence_threshold", 0.75)` with 0.75 as fallback only. Tests prove the threshold flip at 0.60 for Scenario 5.
- **Test structure matches PM/BA brief:** Two files split by concern (`test_policy_scenarios.py` for the six scenarios, `test_policy_precedence.py` for precedence/fail-closed/metadata), matching the brief's suggested layout.