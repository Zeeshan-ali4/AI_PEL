# Review Report — T09: OPA round-trip (prove the HTTP path before real policy)

## Verdict
APPROVE

## Critical findings
- None

## Spec and ledger compliance
- Correct task only: yes
- Dependencies respected: yes (T02 DONE, T08 DONE)
- Allowed files only: yes — `app/policy/__init__.py` added as a package init, which is necessary for the module to import and consistent with how earlier tasks handled new packages
- `Done when` satisfied: yes — client sends real request to OPA and parses an `allow` Decision; OPA unreachable yields `fail_closed`
- `Verify` satisfied: yes — offline tests pass (7/7); OPA roundtrip tests correctly skip when OPA is not running and are structured to pass with a live OPA container
- Reviewer focus satisfied: yes — input contract is explicit and documented in docstring; fail-closed is a real try/except on the HTTP call with separate handling for connection errors, timeouts, non-2xx, missing result, and parse failures

## Product invariant checks
- Model is not judge: pass (not applicable — no semantic layer in this task)
- OPA/PDP owns decisions: pass — Python only produces `fail_closed` on OPA unreachable; all other decisions come from OPA
- Evidence has no decision fields: pass (not applicable — Evidence not modified)
- Fail-closed preserved: pass — connection error, timeout, network error, non-2xx, missing result, and parse failure all return `fail_closed`
- Append-only audit preserved: not applicable
- Stubs labelled: pass — trivial Rego policy has `policy_version: "0.1.0-trivial"` making it clearly a placeholder
- Scenario outcomes preserved: not applicable (trivial allow-all is intentional for T09)

## Required changes
None.

## Non-blocking notes
- `test_opa_non_2xx_fail_closed` has a fallback path that tests connection-refused rather than a true non-2xx when OPA is down. The OPA-up branch correctly monkey-patches `OPA_POLICY_PATH` to trigger a no-result response. Both paths ultimately assert `fail_closed`, and the underlying code handles non-2xx on line 112-113 of `opa_client.py`, so coverage is adequate.
- `controls.json` matches the architect brief's exact structure and all §6 framework mappings verbatim. FIN-PAY-004 carries `"proposed": true` as required.
- The trivial Rego policy hardcodes `threshold_used: 0.75` rather than reading `input.config.high_confidence_threshold` — this is explicitly acceptable for T09 per the architect brief; T10 will replace it.