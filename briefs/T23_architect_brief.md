# Architect Brief — T23: Policy rule editor (extends T19)

## Task selected
- Task: T23 — Policy rule editor (extends T19)
- Current status: To do
- Dependencies checked: pass — T19 is marked Done and T10 is marked Done in `TASK_LEDGER.md`. T23 may run in parallel with T22 and T25 and must not start T24, T20, or T21.

## Source-of-truth references
- MASTER_SPEC.md: §6 Control library + decision precedence; §7 scenario table, especially Scenario 2; §8A item 7 Settings; §10 acceptance criteria for runtime settings and scenario outcomes.
- TASK_LEDGER.md: T23 full task definition, hard scope boundary, OPA integration notes, settings-store notes, UI notes, done criteria, verify step, and reviewer focus. T19 confirms the existing settings page baseline. T10 confirms existing Rego control behaviour and OPA ownership of decisions.
- AGENTS.md: work on exactly one task at a time; touch only the files listed for the current task plus the PM/BA-specified test file; do not change schemas, directory layout, control IDs, scenario outcomes, or policy logic outside the task; the model is not the judge; OPA/Rego makes binding decisions; payment scenarios must not invoke the semantic layer.

## Allowed files
- `app/settings_store.py`
- `opa/data/controls.json`
- `opa/policies/payment.rego`
- `opa/policies/email.rego`
- `app/web/templates/settings.html`
- `app/web/routes.py`
- `tests/T23_rule_editor/`

## Implementation objective
Extend the existing T19 settings page into a narrow policy rule editor for runtime control configuration. The implementer must add per-control enabled/disabled configuration for every control in `controls.json`, add runtime-editable parameters only where T23 permits them, and ensure OPA uses those settings on the next evaluation without a restart. The key demonstrable behaviour is FIN-PAY-002: disabling it makes Scenario 2 allow, enabling it restores escalation, raising its amount threshold to 1000 makes Scenario 2 allow, and restoring it to 500 restores escalation.

The implementation should preserve the current architecture: Python stores and passes runtime configuration; OPA/Rego remains the decision-maker. Do not filter out triggered controls in Python after OPA returns. Disabled controls must not trigger inside Rego.

## Non-negotiables
- Hard scope boundary: this is only a control enabled toggle plus permitted parameters. It is not a policy authoring tool, Rego editor, generic rule builder, or schema redesign.
- Editable parameters are limited to FIN-PAY-002's refund/payment amount threshold and the existing confidence threshold from T19. Do not add new configurable business parameters unless the spec is updated first.
- Every control must have an enabled/disabled toggle in the settings UI and a persisted runtime setting.
- `opa/data/controls.json` may expose defaults/metadata (`enabled`, `parameters`) but runtime changes must persist through the DB-backed settings store, not by editing the JSON file at runtime.
- Seed defaults must match existing behaviour: all currently active, non-proposed controls enabled; FIN-PAY-002 amount threshold 500; confidence threshold 0.75; existing per-control modes preserved.
- FIN-PAY-004 remains proposed and must not accidentally become an active scenario-affecting control. Preserve the existing proposed-control guard semantics.
- OPA input must include the runtime enabled flags and parameters under `input.config`; Rego must check `control_enabled("<ID>")` from runtime config and must read `FIN-PAY-002`'s threshold from `input.config.parameters["FIN-PAY-002"].amount_threshold` or an equivalently explicit config path with safe defaults.
- Python may assemble and validate config but must not make allow/block/escalate decisions or post-filter OPA results.
- Payment scenarios must continue to skip the semantic layer.
- Scenario outcomes must remain as specified by `MASTER_SPEC.md` except when the user deliberately changes T23 settings for the demo/verify cases.
- Preserve T19 behaviour: changing the confidence threshold to 0.60 still flips Scenario 5 to `allow_with_logging` without restart.
- Use inline editing below the existing confidence-threshold section; do not introduce modals.
- The settings page must show a clear confirmation that changes take effect on the next evaluation.
- Do not touch files outside the allowed list. If an implementation appears to require a migration file, new production module, schema file, or policy file outside the allowed list, stop and ask.

## Verify step
Primary ledger verify:
1. Toggle FIN-PAY-002 off, run Scenario 2, and confirm the decision is `allow`.
2. Toggle FIN-PAY-002 on, run Scenario 2, and confirm the decision is `escalate`.
3. Set FIN-PAY-002 amount threshold to 1000, run Scenario 2, and confirm the decision is `allow`.
4. Set FIN-PAY-002 amount threshold to 500, run Scenario 2, and confirm the decision is `escalate`.
5. Restart the app and confirm settings persisted.

Task-specific checks for the implementer/QA:
- Run the PM/BA-specified pytest file under `tests/T23_rule_editor/`.
- Run existing relevant settings/policy tests if practical: `tests/T19_settings_ui/` and `tests/T10_policy/`.
- Inspect the OPA input path or tests to prove FIN-PAY-002 reads the configured amount threshold and disabled controls are skipped in Rego, not filtered in Python.
- Reconfirm the T19 threshold demo remains valid: set confidence threshold to 0.60 and run Scenario 5; it should become `allow_with_logging` without restart.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T23_architect_brief.md` and `briefs/T23_test_brief.md`. Implement exactly T23. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
