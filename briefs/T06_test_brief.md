# Test Brief — T06: Presidio sensor (REAL)

## Spec references
- MASTER_SPEC.md: §2 deterministic tools before general LLMs; §4 real in-process `presidio-analyzer` with spaCy `en_core_web_sm`; §5.3 `detected_entities` and `evidence_spans` evidence fields; §7 scenarios 4, 5, and 6 email bodies; §12 acceptance criterion that Scenario 4 shows real Presidio entities, not hardcoded.
- TASK_LEDGER.md: T06 goal, dependencies, allowed files, key notes, done-when, verify step, and reviewer focus.
- Architect brief: T06 must use real Presidio AnalyzerEngine, register a custom UK NHS-number recognizer, return raw entity/span/score evidence only, and must not proceed with implementation until the dependency-file blocker for `presidio-analyzer` is resolved.

## Target test location
- Folder: `tests/T06_presidio/`
- Suggested files:
  - `test_presidio_sensor_scenarios.py` — covers scenario-driven acceptance tests for email bodies from Scenarios 4, 5, and 6.
  - `test_presidio_sensor_contract.py` — covers raw-evidence contract, span alignment, source labelling, and no policy-decision leakage.

## Test cases

### test_scenario_4_detects_nhs_number_and_health_entities_with_spans
- **Traces to:** MASTER_SPEC.md §4, §5.3, §7 Scenario 4, §12; TASK_LEDGER T06 done-when and verify step.
- **Input:** The exact Scenario 4 email body from the scenario catalog/fixtures: external email containing NHS number `485 777 3456`, a health condition, and vulnerability wording.
- **Expected outcome:**
  - The real Presidio-backed sensor returns at least one detected entity whose text span corresponds exactly to `485 777 3456`.
  - The NHS-number finding is produced through the Presidio sensor path and is labelled with `source == "presidio"` in the returned entity representation.
  - The output includes one or more health/special-category-relevant raw findings or spans from the planted health content, without turning those findings into a policy decision.
  - Every returned span uses Python string offsets where `body[start:end]` equals the matched text and `start < end`.
  - Each score is numeric and bounded from `0.0` to `1.0`.
- **Notes:** Must exercise a real `presidio-analyzer` AnalyzerEngine with the custom UK NHS-number recognizer registered. Do not mock Presidio, do not hardcode Scenario 4 outputs, and do not use regex-only detection as a substitute for Presidio.

### test_scenario_5_returns_raw_presidio_findings_without_policy_judgement
- **Traces to:** MASTER_SPEC.md §2, §5.3, §7 Scenario 5; TASK_LEDGER T06 key notes.
- **Input:** The exact Scenario 5 email body from the scenario catalog/fixtures: external email containing the phrase `struggling a bit since losing my job`.
- **Expected outcome:**
  - The sensor can be called successfully on the Scenario 5 body and returns a collection of raw Presidio findings/spans, even if Presidio detects few or no entities in this body.
  - The output contains no decision, enforcement, approval, escalation, allow, block, or policy outcome field.
  - If any entities are returned, each entity has only raw evidence attributes such as type/label, score, source, and span offsets, and all returned spans align to the original input text.
- **Notes:** Vulnerability classification for Scenario 5 belongs to the later nuance stub/evidence-builder task, not T06. This test should prevent T06 from inferring `COMM-EMAIL-002`, escalation, or vulnerability policy outcomes.

### test_scenario_6_detects_customer_name_only_no_health_or_nhs_entity
- **Traces to:** MASTER_SPEC.md §5.3 and §7 Scenario 6; TASK_LEDGER T06 done-when.
- **Input:** The exact Scenario 6 email body from the scenario catalog/fixtures: external partner email with a customer name only and no special-category or vulnerability content.
- **Expected outcome:**
  - The sensor detects the planted customer name/personal-data entity from the body when Presidio identifies it.
  - The output does not include an NHS-number entity, health/special-category entity, or vulnerability/policy conclusion for this body.
  - Any returned spans align exactly to the original text and are labelled as Presidio-origin findings.
- **Notes:** This is the principal negative scenario for the custom NHS recognizer and health-related detection.

### test_custom_nhs_number_recognizer_is_registered_with_presidio
- **Traces to:** MASTER_SPEC.md §4; TASK_LEDGER T06 goal; Architect brief non-negotiables.
- **Input:** A minimal email string containing only a valid UK NHS-number-shaped value, including `485 777 3456`, plus neutral surrounding text.
- **Expected outcome:**
  - The sensor returns an NHS-number entity/finding for the NHS value.
  - The finding comes through the Presidio analyzer result structure/adapter used by the sensor, not through a separate post-processing policy judgement.
  - The entity includes a bounded score and span offsets matching the NHS-number substring exactly.
- **Notes:** This test may use the scenario NHS value directly to keep the acceptance fixture stable. It should fail if the custom recognizer is not registered with the Presidio AnalyzerEngine.

### test_output_contract_contains_raw_evidence_only
- **Traces to:** MASTER_SPEC.md §2 and §5.3 Evidence non-decision rule; AGENTS.md non-negotiable product rules; TASK_LEDGER T06 key notes.
- **Input:** A representative email body containing a name, email address, NHS number, and health wording.
- **Expected outcome:**
  - Returned top-level data and per-entity/per-span data contain raw evidence only: entity type/label, score, source, start/end offsets, and matched label/span information as applicable.
  - The output does not contain any of these forbidden decision/enforcement keys at any level: `decision`, `allow`, `block`, `escalate`, `approval`, `approved`, `required_approval_role`, `executed`, `control_id`, `triggered_controls`, `failure_mode`, or `threshold_used`.
  - No final Evidence-level classifications from T07, such as `contains_special_category_data`, `sensitivity_level`, `overall_confidence`, or `vulnerability_indicators`, are required from T06 unless the implementer explicitly documents they are raw placeholders rather than policy conclusions; preferred T06 output is raw Presidio results for T07 assembly.
- **Notes:** This protects the product rule that the model/sensor is not the judge and that T06 must not leak policy logic into Python.

### test_all_returned_spans_are_valid_for_original_text
- **Traces to:** MASTER_SPEC.md §5.3 `evidence_spans`; TASK_LEDGER T06 reviewer focus.
- **Input:** Scenario 4, Scenario 5, and Scenario 6 email bodies from fixtures.
- **Expected outcome:**
  - For every returned span across all three bodies, `start` and `end` are integers, `0 <= start < end <= len(body)`, and slicing `body[start:end]` returns non-empty source text.
  - Span labels correspond to the associated entity type/label returned by the sensor.
  - The same original body text is used for offset validation; no normalized or redacted copy is used for offsets.
- **Notes:** This acceptance test supports the later UI requirement to highlight real Presidio spans accurately.

### test_sensor_handles_empty_or_whitespace_body_without_policy_decision
- **Traces to:** MASTER_SPEC.md §2 and §5.3; TASK_LEDGER T06 raw-evidence scope.
- **Input:** Empty string and whitespace-only string.
- **Expected outcome:**
  - The sensor returns an empty raw-finding collection or an equivalent successful no-findings result.
  - It does not raise an unhandled exception for empty/whitespace input.
  - It does not emit `sensor_error`, `fail_closed`, or any policy decision; fail-closed handling is owned by later pipeline/evidence tasks.
- **Notes:** This is an edge-case acceptance test for sensor robustness while preserving T06 scope.

## Coverage checklist
- [ ] Happy path covered: Scenario 4 real NHS/health detection and Scenario 6 customer-name personal-data detection.
- [ ] Error/edge cases covered: empty/whitespace input and no/low-entity Scenario 5 behaviour.
- [ ] Spec non-negotiables verified: real Presidio use, custom NHS recognizer, span alignment, raw evidence only, no decision/enforcement fields.
- [ ] Real dependencies flagged: tests must use real `presidio-analyzer` and the registered custom recognizer; do not mock Presidio or hardcode scenario outputs.

## Gaps or ambiguities
- The Architect brief identifies a current implementation blocker: `presidio-analyzer` is required by T06 but the T06 allowed file list does not include `requirements.txt`, and the current dependency list may not include the package. The Implementer must not edit dependency files unless the human updates T06 scope or confirms dependency management was handled elsewhere.
- The exact T06 sensor return shape is not fully specified beyond raw entities, spans, scores, and source. Tests should assert the required contract and forbidden fields while allowing reasonable implementation naming for raw entity type/label fields.
- Presidio's built-in health/medical entity coverage can vary by analyzer configuration. The mandatory deterministic requirement is the custom NHS-number recognizer; health-related body evidence should be asserted only to the extent supported by the selected real Presidio recognizers and documented by the Implementer.
