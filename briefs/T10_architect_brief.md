# Architect Brief — T10: OPA real policies + precedence (the heart)

## Task selected
- Task: T10 — OPA real policies + precedence (the heart)
- Current status: To do
- Dependencies checked: pass — T10 depends on T09, and `TASK_LEDGER.md` marks T09 as Done. Current build state says current task is T10 and last completed task is T09.

## Source-of-truth references
- `MASTER_SPEC.md` §2: preserve the core principles that the model is not the judge, Evidence carries no decision field, default to a human, uncertainty escalates, and sensor/context/OPA failures fail closed.
- `MASTER_SPEC.md` §5.4: OPA must return the binding `Decision` shape with `decision`, `control_id`, `triggered_controls`, `reason`, `required_approval_role`, `framework_mappings`, `failure_mode`, `logging_requirements`, `policy_version`, and `threshold_used`.
- `MASTER_SPEC.md` §6: implement the real control library, decision precedence, runtime `HIGH_CONFIDENCE` threshold from `config.high_confidence_threshold`, all listed controls, framework mappings, and global fail-closed behaviour.
- `MASTER_SPEC.md` §7: all six narrative scenarios must produce the exact expected decisions and controls in the table; lowering the threshold to `0.60` must flip scenario 5 from `escalate` to `allow_with_logging`.
- `MASTER_SPEC.md` §10: use the canonical file layout only.
- `MASTER_SPEC.md` §11: policy is called with `{action, context, evidence, config}` after settings are loaded; payment paths have `Evidence(evaluated=false)` and must not require semantic evidence.
- `MASTER_SPEC.md` §12: acceptance criteria include exact §7 decisions and the threshold flip for scenario 5.
- `TASK_LEDGER.md` T10: implement all controls in Rego across the allowed policy files, pull framework mappings from `controls.json`, implement precedence, and prove all six decisions plus the threshold flip.
- `AGENTS.md`: work on exactly one task; touch only files listed for this task plus the PM/BA-specified test file under `tests/`; do not change schemas, file layout, control IDs, scenario outcomes, or policy logic; if a needed file is outside the allowed list, stop and ask.

## Allowed files
- `opa/policies/payment.rego`
- `opa/policies/email.rego`
- `opa/policies/common.rego`
- `tests/T10_policy/`

The Architect Brief itself is written to `briefs/T10_architect_brief.md` for pipeline handoff. Implementer must not edit files outside the T10 allowed list above plus the target test file specified by the PM/BA Test Brief.

## Implementation objective
Replace the trivial T09 OPA policy with real deterministic Rego policy logic. OPA must evaluate the stable input contract from `app/policy/opa_client.py`:

```json
{
  "action": { "...": "Action" },
  "context": { "...": "Context" },
  "evidence": { "...": "Evidence" },
  "config": {
    "high_confidence_threshold": 0.75,
    "control_modes": { "<control_id>": "<mode>" }
  }
}
```

The returned object must validate against the `Decision` schema and include real triggered controls, selected top-precedence control, human approval role where applicable, framework mappings from `opa/data/controls.json`, enhanced logging for logging/fail-closed cases where appropriate, a real policy version, and `threshold_used` echoed from `input.config.high_confidence_threshold`.

Design guidance for the policy split:
- `payment.rego`: payment-specific controls only (`FIN-PAY-001`, `FIN-PAY-002`, `FIN-PAY-003`, and `FIN-PAY-004` if metadata says it is active). Payment controls must use only `action`, `context`, `config`, and `controls.json`; they must not depend on semantic evidence being evaluated.
- `email.rego`: email-specific controls (`COMM-EMAIL-001`, `COMM-EMAIL-002`, `COMM-EMAIL-003`) using `context.recipient`, `evidence`, and the runtime threshold.
- `common.rego`: shared result assembly, global fail-closed checks, control metadata lookup, precedence resolver, default allow, and the exported `policy.gate.decision` rule used by `opa_client.py`.

## Non-negotiables
- OPA/Rego is the decision-maker. Do not move policy decision logic into Python.
- Evidence remains evidence only. Do not add or rely on any Evidence allow/block/decision/approval/enforcement field.
- Precedence is exact: `fail_closed` > `block` > `escalate` > `require_evidence` > `modify` > `allow_with_logging` > `allow`.
- `block` is only for the clearly prohibited tier: `FIN-PAY-001`.
- All risky-but-legitimate controls escalate to named humans; scenario 4 special-category email escalates to `data_protection_approver`, not block.
- Global fail-closed in OPA must trigger when `context.context_resolution_ok == false` or `evidence.sensor_error == true`. OPA unreachable remains handled in Python by T09 `opa_client.py`; do not edit that file for T10.
- The high-confidence threshold must be read from `input.config.high_confidence_threshold`, not hard-coded. Default `0.75` may be used only as a safe fallback when the input omits it.
- Scenario 5 must escalate at threshold `0.75` and become `allow_with_logging` when threshold is `0.60` because its stub confidence is `0.62`.
- Pull framework mappings and control metadata from `opa/data/controls.json`; do not duplicate mappings in Rego unless unavoidable for fail-closed/default metadata.
- Do not edit `opa/data/controls.json` in T10. If the existing metadata prevents exact §7 outcomes (especially the proposed `FIN-PAY-004` flag), stop and ask rather than changing files outside scope or silently changing scenario outcomes.
- Do not create new policy files or test folders outside `tests/T10_policy/`.

## Verify step
Ledger verify step: run all six scenarios through `opa_client` and compare the resulting decision/control to the §7 table; then set `high_confidence_threshold` to `0.60` and confirm scenario 5 becomes `allow_with_logging`.

Task-specific checks the Implementer should support in pytest:
- Scenario 1: `allow`, `control_id == null`, no triggered controls that change the decision.
- Scenario 2: `escalate`, `control_id == "FIN-PAY-002"`, `required_approval_role == "finance_supervisor"`.
- Scenario 3: `block`, `control_id == "FIN-PAY-001"`.
- Scenario 4: `escalate`, `control_id == "COMM-EMAIL-001"`, `required_approval_role == "data_protection_approver"`.
- Scenario 5 at threshold `0.75`: `escalate`, `control_id == "COMM-EMAIL-002"`, `required_approval_role == "vulnerable_customer_team"`, `threshold_used == 0.75`.
- Scenario 5 at threshold `0.60`: `allow_with_logging`, expected logging control `COMM-EMAIL-003` if personal-data logging applies to the assembled evidence, and `threshold_used == 0.60`.
- Scenario 6: `allow_with_logging`, `control_id == "COMM-EMAIL-003"`, enhanced logging.
- Precedence regression: a synthetic payment that is both fraud-flagged and over £500 must resolve to `block`/`FIN-PAY-001`, not escalation.
- Fail-closed regression: `context_resolution_ok=false` or `sensor_error=true` must resolve to `fail_closed` with enhanced logging and safe-default mappings.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T10_architect_brief.md` and `briefs/T10_test_brief.md`. Implement exactly T10. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
