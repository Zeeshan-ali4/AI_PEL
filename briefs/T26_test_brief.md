# Test Brief — T26: "If a regulator asked..." evidence mapping

## Spec references
- MASTER_SPEC.md: §1 proof points 1, 4, 5, 6, and 7; §1A assurance value pillars; §2 product principles; §5.1–§5.5 Action/Context/Evidence/Decision/EvidenceRecord field sets; §6 control outcomes and illustrative framework mappings; §7 six narrative scenario outcomes; §8 enforcement modes; §8A decision view, approval queue, evidence record view, audit integrity UI requirements; §11 pipeline evidence/decision/audit flow; §12 acceptance criteria for scenario outcomes, payment semantic skipping, approval append-only records, and visible stub/illustrative labels.
- TASK_LEDGER.md: T26 goal, file list, key notes, Done criteria, Verify step, and reviewer focus for the regulator-question panel.
- briefs/T26_architect_brief.md: single-source mapping module, allowed files, suggested minimum question coverage, and edge-case expectations for payment, email, fail-closed, and approval-decision records.

## Target test location
- Folder: `tests/T26_regulator_questions/`
- Suggested files:
  - `__init__.py` — package marker for the task test folder.
  - `test_mapping.py` — covers the pure regulator-question mapping function, field-backed row shape, scenario/outcome variation, payment-vs-email semantic answers, fail-closed answers, and approval-decision answers.
  - `test_views.py` — covers the decision page and record page rendering the shared panel from route-provided rows without duplicating question definitions in templates.

## Test cases

### test_mapping_returns_ordered_minimum_question_rows_with_field_labels
- **Traces to:** TASK_LEDGER T26 Done criteria 1–2; MASTER_SPEC §1 proof points; MASTER_SPEC §5.1–§5.5 schemas; Architect Brief non-negotiable that mapping rows include `question`, `answer_field_label`, and `answer_value`.
- **Input:** A representative persisted `action_evaluation` evidence record for a normal scenario run with populated action, context, evidence, decision, enforcement mode, executed flag, record hash, and previous hash.
- **Expected outcome:** The mapping function returns an ordered list with at least six rows. Every row contains non-empty `question`, `answer_field_label`, and `answer_value` entries. Each `answer_field_label` names one or more existing record fields, such as `executed`, `enforcement_mode`, `decision.control_id`, `decision.framework_mappings`, `context_used.*`, `evidence.*`, `decision.reason`, `decision.policy_version`, `required_approval_role`, `record_hash`, or `prev_hash`.
- **Notes:** This is an acceptance test for the panel contract, not an implementation-unit test. It should not assert private helper behaviour.

### test_mapping_covers_interception_policy_evidence_judge_human_and_integrity_questions
- **Traces to:** TASK_LEDGER T26 minimum question set; MASTER_SPEC §1 proof points 1, 4–7; MASTER_SPEC §1A human oversight, evidential reliability, and demonstrable control operation; MASTER_SPEC §2 model-not-judge principle.
- **Input:** A representative `action_evaluation` evidence record.
- **Expected outcome:** The returned rows include regulator questions that cover all six required concerns: pre-execution interception/enforcement; applied policy/control and illustrative mappings; evidence/context that informed the decision; who/what made the binding decision; whether human involvement was required/evidenced; and tamper-evident integrity. The judge/decision row must state or clearly imply that the deterministic policy engine/OPA made the binding decision and evidence/sensors only informed it.
- **Notes:** Tests may match stable question fragments rather than the full final copy, but must fail if a required concern is missing.

### test_mapping_reflects_allow_block_escalate_and_allow_with_logging_outcomes
- **Traces to:** TASK_LEDGER T26 Done criterion 3; MASTER_SPEC §6 decision precedence and controls; MASTER_SPEC §7 scenario table.
- **Input:** Records representing the six narrative scenarios: Scenario 1 `allow`, Scenario 2 `escalate`, Scenario 3 `block`, Scenario 4 `escalate`, Scenario 5 `escalate`, and Scenario 6 `allow_with_logging`.
- **Expected outcome:** For each record, the panel rows are field-backed and sensible for that outcome: no-control `allow` records do not invent a control ID; `block` records cite `FIN-PAY-001` and executed/enforcement state; `escalate` records cite the required approval role; `allow_with_logging` records cite enhanced/standard logging and the relevant control/framework mappings.
- **Notes:** The test should use real scenario fixtures or persisted records where practical so it remains aligned with §7. If factory data is used, it must mirror the canonical §7 outcomes and schema fields exactly.

### test_payment_records_explain_semantic_layer_not_invoked_from_evidence_evaluated_false
- **Traces to:** TASK_LEDGER T26 key note on payment records; MASTER_SPEC §3 semantic layer only for email; MASTER_SPEC §11 pipeline step 4; MASTER_SPEC §12 payment semantic-layer acceptance criterion.
- **Input:** A payment `action_evaluation` record with `action.action_type` for payment and `evidence.evaluated=false`.
- **Expected outcome:** The evidence/context question answer explicitly indicates that the semantic layer was not invoked/not needed for the payment action type. The answer must be derived from the existing record shape, especially `action.action_type` and `evidence.evaluated=false`, and must not fabricate semantic evidence, detected entities, or model confidence.
- **Notes:** This is a critical payment-vs-email differentiation test.

### test_email_records_show_existing_semantic_evidence_and_stub_label_context
- **Traces to:** TASK_LEDGER T26 Done criterion 4; MASTER_SPEC §1 honesty principle; MASTER_SPEC §5.3 Evidence; MASTER_SPEC §7 email scenarios and deterministic nuance stub; MASTER_SPEC §8A visible labelled stub requirement; MASTER_SPEC §12 real Presidio + labelled stub acceptance criteria.
- **Input:** An email `action_evaluation` record with `evidence.evaluated=true`, detected entities, evidence spans, vulnerability indicators, overall confidence, and sensor versions.
- **Expected outcome:** The evidence/context question answer references existing semantic-evidence fields such as `evidence.detected_entities`, `evidence.vulnerability_indicators`, `evidence.overall_confidence`, `evidence.sensor_versions`, and relevant `context_used.recipient` fields. Copy must preserve that Presidio is real and the nuance model is a labelled stub/model stand-in where those values appear in the record.
- **Notes:** Tests should assert the panel does not say the model made the binding decision.

### test_fail_closed_record_renders_policy_engine_unreachable_or_required_context_failure_answer
- **Traces to:** TASK_LEDGER T26 fail-closed edge case; MASTER_SPEC §2 fail-closed principle; MASTER_SPEC §5.4 Decision failure fields; MASTER_SPEC §6 GLOBAL fail-closed; MASTER_SPEC §11 OPA failure/context/sensor failure flow.
- **Input:** A `fail_closed` `action_evaluation` record with either `context_used.context_resolution_ok=false`, `evidence.sensor_error=true`, or a decision reason/failure mode indicating OPA/policy unreachability.
- **Expected outcome:** The judge/decision answer is not blank when `decision.control_id` is absent. It explains from existing fields that required policy/context/sensor operation failed and the system defaulted to stop/fail closed. The row must cite fields such as `decision.decision`, `decision.reason`, `decision.failure_mode`, `context_used.context_resolution_ok`, and/or `evidence.sensor_error`.
- **Notes:** The exact failure source can vary by simulation, but the panel must not treat fail-closed as a normal allow/block/escalate control outcome.

### test_approval_decision_record_shows_human_approver_reason_and_referenced_original_hash
- **Traces to:** TASK_LEDGER T26 Done criterion 3; MASTER_SPEC §5.5 append-only approvals; MASTER_SPEC §8A approval queue; MASTER_SPEC §12 approval append-only acceptance criterion.
- **Input:** An `approval_decision` evidence record linked to an original escalation by `correlation_id` and `references_hash`, with populated `human_approver`, `approval_reason`, resulting `executed` state, `record_hash`, and `prev_hash`.
- **Expected outcome:** The human-oversight question answer cites `record_type=approval_decision`, `human_approver`, `approval_reason`, `references_hash`, and resulting `executed` state. The integrity question still cites the approval record's own `record_hash`/`prev_hash`. The test should also assert the answer frames the approval as a new appended record rather than a mutation of the original evaluation.
- **Notes:** Use real approval flow output if feasible; otherwise construct schema-faithful persisted record data.

### test_non_escalation_records_state_no_human_approval_required_from_decision_field
- **Traces to:** TASK_LEDGER T26 minimum question 5; MASTER_SPEC §5.4 `required_approval_role`; MASTER_SPEC §6 allow/block/allow_with_logging outcomes.
- **Input:** `allow`, `block`, and `allow_with_logging` action-evaluation records where `decision.required_approval_role` is null.
- **Expected outcome:** The human-oversight question answers that no human approval was required by the binding decision, citing `decision.required_approval_role` and `decision.decision`. It must not invent approver names or approval reasons.
- **Notes:** This complements the approval-decision and escalation coverage.

### test_decision_page_renders_regulator_panel_with_rows_after_scenario_run
- **Traces to:** TASK_LEDGER T26 Done criterion 1 and Verify step; MASTER_SPEC §8A Decision view; MASTER_SPEC §12 scenario acceptance criteria.
- **Input:** Run or request a scenario result that opens the post-run decision page using the existing app route and a record-backed decision context.
- **Expected outcome:** The decision page response contains the heading `If a regulator asked...` and renders at least six question rows with their field labels and answer values. The panel must appear alongside, not in place of, existing evidence and binding-decision sections.
- **Notes:** This should exercise route/template integration, not just call the mapping function. Where the app test stack supports it, use FastAPI/TestClient and real route context. Avoid mocks for OPA/Presidio/Postgres in end-to-end scenario tests if the existing test harness provides real service-backed flows.

### test_record_page_renders_same_regulator_panel_for_persisted_record
- **Traces to:** TASK_LEDGER T26 Done criterion 1 and Verify step; MASTER_SPEC §8A Evidence record view; MASTER_SPEC §5.5 persisted EvidenceRecord.
- **Input:** Open an existing persisted record view for a scenario run or created evidence record.
- **Expected outcome:** The record page response contains the heading `If a regulator asked...` and renders at least six mapped rows from the persisted `EvidenceRecord`. Values must match the persisted record rather than being recomputed from separate action/context/evidence/decision objects.
- **Notes:** This test ensures the record view and decision view both receive regulator-question context.

### test_templates_do_not_define_duplicate_question_text
- **Traces to:** TASK_LEDGER T26 reviewer focus; Architect Brief non-negotiable single source of truth in `app/web/regulator_questions.py`.
- **Input:** Source files `app/web/templates/_regulator_questions.html`, `app/web/templates/decision.html`, `app/web/templates/record.html`, and `app/web/regulator_questions.py`.
- **Expected outcome:** The shared partial iterates provided rows and renders row fields; `decision.html` and `record.html` include the partial but do not hardcode the regulator-question strings. The canonical question text is defined only in `app/web/regulator_questions.py`.
- **Notes:** It is acceptable for templates to contain the shared panel heading. They should not contain separate copies of the six question strings.

### test_panel_answers_are_conservative_when_optional_fields_are_missing
- **Traces to:** TASK_LEDGER T26 key note against hardcoded/invented answers; MASTER_SPEC §5 schemas with nullable fields; Architect Brief non-negotiable no fabricated answers.
- **Input:** A schema-valid record with optional nullable fields absent, such as `decision.control_id=null`, empty `framework_mappings`, `required_approval_role=null`, `human_approver=null`, and `references_hash=null`.
- **Expected outcome:** Rows still render non-empty conservative answers that cite the absence of the field or the relevant null/empty field state, without inventing controls, mappings, approvals, or evidence. No row should crash or render a misleading blank for required questions.
- **Notes:** This is the main edge-case acceptance test for field-backed wording.

## Coverage checklist
- [x] Happy path covered: representative normal action-evaluation records and both decision/record page rendering.
- [x] Error/edge cases covered: fail-closed, nullable/absent optional fields, non-escalation no-approval cases, and approval-decision records.
- [x] Spec non-negotiables verified: model/evidence is not the judge, payment semantic layer is not invoked, append-only approval evidence is shown, and hash-chain fields are cited.
- [x] Real dependencies flagged: scenario/route tests should use the existing real service-backed harness for OPA, Presidio, Postgres, and hash-chain records where practical; do not replace those dependencies with mocks in tests intended to validate end-to-end scenario behaviour.

## Gaps or ambiguities
- The T26 Verify step requires a manual UI check across six scenarios plus one approval and one fail-closed simulation. The automated tests above should cover as much as practical, but QA should still perform and report the manual/browser verification if the environment supports the running web app.
- The ledger does not prescribe exact question wording. Tests should verify required question coverage and field-backed answers using stable fragments/semantics rather than over-constraining copy, while still preventing duplicated hardcoded question text in page templates.
