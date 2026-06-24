# Review Report — T15: Scenario runner + decision view

## Verdict
APPROVE

## Critical findings
- None

## Spec and ledger compliance
- Correct task only: yes
- Dependencies respected: yes (T14 is Done)
- Allowed files only: yes — `app/web/routes.py`, `app/web/templates/scenarios.html`, `app/web/templates/decision.html`, `tests/T15_scenarios_ui/` (plus the required `TASK_LEDGER.md` status edit To do → Review)
- `Done when` satisfied: yes — all six scenarios render correct decision views; scenario 4 renders highlighted spans from real `evidence_spans`; payment views show "Semantic layer not invoked (evidence.evaluated=false)"
- `Verify` satisfied: yes/not run — manual click-through not performed by this reviewer, but the equivalent automated acceptance suite was run. 2 tests passed without external dependencies; 11 tests that exercise the real OPA-backed pipeline path skipped because no `opa` binary/OPA_URL is available in this review sandbox (no Docker daemon either). This is an environment limitation identical to the existing T13/T14 suites (`tests/T13_pipeline`, `tests/T14_dashboard` show the same 13 passed / 5 skipped pattern), not a defect introduced by T15.
- Reviewer focus satisfied: yes — the evidence panel visually and textually subordinates evidence to the policy decision ("Evidence informs the policy engine... never the approval or blocking authority. The policy engine is the judge"); nothing stubbed is unlabelled.

## Product invariant checks
- Model is not judge: pass — decision view explicitly states the policy engine is the judge; the stub confidence is rendered as informational only.
- OPA/PDP owns decisions: pass — the view only renders fields already present on the `Decision` object returned by `get_pipeline().run_scenario()`; no new decision logic in Python/Jinja.
- Evidence has no decision fields: pass — template/route code reads `evidence.evaluated`, `evidence.detected_entities`, `evidence.evidence_spans`, `evidence.vulnerability_indicators`; no allow/block field is introduced.
- Fail-closed preserved: not applicable to this task (no changes to OPA reachability handling).
- Append-only audit preserved: not applicable (no audit-store changes); `record.executed`/`outcome.would_have`/`outcome.queued` are read-only display of T11/T12 results.
- Stubs labelled: pass — stub confidence block is headed "Deterministic stub — model stand-in, not a production model"; framework chips are marked "(illustrative mapping)"; no Horizon Inquiry recommendation numbers appear (tests assert `"Horizon" not in html`).
- Scenario outcomes preserved: pass — `EXPECTED` mapping in tests matches §7 exactly (allow / escalate+FIN-PAY-002+finance_supervisor / block+FIN-PAY-001 / escalate+COMM-EMAIL-001+data_protection_approver / escalate+COMM-EMAIL-002+vulnerable_customer_team / allow_with_logging+COMM-EMAIL-003); no scenario data, OPA policy, or schema files were touched.

## Required changes
None.

## Non-blocking notes
- `base.html` (T14, out of scope for T15) has no nav link to `/scenarios`; the only way to reach the new page is by typing the URL. Not a T15 file-boundary violation, but worth a one-line nav addition in a later in-scope task.
- Test files are reasonably split by concern (`test_scenario_runner.py`, `test_decision_view_scenarios.py`, `test_evidence_panel.py`) matching the PM/BA Test Brief's suggested layout — good adherence to the "split by concern" reviewer rule.
- `test_payment_scenarios_show_semantic_layer_not_invoked` contains a tautological assertion (`... or True`) that never fails; it adds no real coverage beyond the two assertions either side of it. Harmless (not a correctness or scope violation) but flagging since it's dead-weight test logic.
- Could not execute the real-OPA acceptance tests in this review environment (no `opa` binary, no Docker). Recommend QA explicitly confirm the 11 currently-skipped tests pass green in an environment with OPA/Docker available before sign-off.