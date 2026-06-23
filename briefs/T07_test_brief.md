# Test Brief — T07: Nuance stub + evidence builder

## Spec references
- MASTER_SPEC.md: §1 and §1A for bounded evidence only and visibly labelled stubs; §2 for “model is not the judge”, Presidio-before-stub ordering, payment semantic skip, and fail-closed-ready sensor errors; §3 and §11 for semantic layer invocation only on email actions; §5.3 for the exact Evidence schema; §7 for the six scenario evidence expectations and fixed stub confidences; §12 acceptance criteria for payment `evaluated=false`, Scenario 4 real Presidio evidence plus labelled stub confidence, and Scenario 5 confidence `0.62`.
- TASK_LEDGER.md: T07 goal, files, key notes, done-when criteria, verify step, and reviewer focus. Acceptance requirements: stub is deterministic-by-input with fixed confidences `0.88`, `0.62`, and low/no confidence; output includes `source: "nuance_stub"` and version `stub-0.1`; evidence builder sets schema fields; emails evaluate semantics; payments do not; any sensor exception returns `sensor_error=true`; no Evidence decision field.
- Architect brief: `briefs/T07_architect_brief.md` non-negotiables, allowed files, verification observations, and handoff guidance.

## Target test location
- Folder: `tests/T07_evidence/`
- Suggested files:
  - `test_nuance_stub.py` — covers deterministic planted-phrase matching, fixed scenario confidences, labelled stub source/version expectations, low/no-vulnerability output, and absence of decision-like fields in stub output.
  - `test_evidence_builder.py` — covers assembled Evidence for all six scenarios, payment semantic skip, email Evidence schema validation, sensitivity classification, Presidio-origin entities/spans, stub-origin vulnerability indicators, overall confidence preservation, and no decision-like fields in Evidence output.
  - `test_sensor_error_handling.py` — covers fail-closed-ready Evidence when Presidio or the nuance stub raises, with `sensor_error=true` and a still-valid Evidence object.

## Test cases

### test_nuance_stub_scenario_4_health_affordability_phrase_returns_fixed_high_confidence
- **Traces to:** MASTER_SPEC.md §5.3 and §7; TASK_LEDGER.md T07 done-when; architect brief non-negotiables.
- **Input:** Scenario 4 email body containing the planted NHS/health content and affordability phrase, passed directly to the nuance stub classifier.
- **Expected outcome:** The stub result reports `present=true`, `confidence == 0.88`, `source == "nuance_stub"`, and categories include the relevant vulnerability categories for the planted health/affordability content. The output contains no `decision`, `allow`, `block`, `approval`, or enforcement field.
- **Notes:** This is a labelled deterministic stub test, not a model-quality test. The exact input should be the scenario body from the scenario fixture, not a newly invented phrase.

### test_nuance_stub_scenario_5_job_loss_phrase_returns_fixed_uncertain_confidence
- **Traces to:** MASTER_SPEC.md §5.3, §6 threshold behaviour, and §7 Scenario 5; TASK_LEDGER.md T07 done-when.
- **Input:** Scenario 5 email body containing the exact planted phrase `struggling a bit since losing my job`, passed directly to the nuance stub classifier.
- **Expected outcome:** The stub result reports `present=true`, `confidence == 0.62`, `source == "nuance_stub"`, and categories include `financial_vulnerability`. The output contains no decision-like fields.
- **Notes:** The `0.62` confidence is policy-relevant for later T08/T10/T19 work and must not drift.

### test_nuance_stub_scenario_6_name_only_returns_no_vulnerability
- **Traces to:** MASTER_SPEC.md §5.3 and §7 Scenario 6; TASK_LEDGER.md T07 done-when.
- **Input:** Scenario 6 customer-name-only email body, passed directly to the nuance stub classifier.
- **Expected outcome:** The stub result reports `present=false`, low or zero confidence below the default high-confidence threshold, `categories == []`, and `source == "nuance_stub"`. The output contains no decision-like fields.
- **Notes:** This guards against over-escalating benign personal-data-only content at the evidence layer.

### test_build_evidence_payments_skip_presidio_and_nuance_for_scenarios_1_to_3
- **Traces to:** MASTER_SPEC.md §3, §5.3, §7 Scenarios 1–3, §11 step 4, and §12 acceptance criteria; TASK_LEDGER.md T07 key notes.
- **Input:** Normalised Action objects or schema-valid equivalent Actions for Scenarios 1, 2, and 3. The test must instrument the Presidio sensor and nuance stub entry points so any call fails the test.
- **Expected outcome:** For each payment action, assembled Evidence validates against `app.schemas.evidence.Evidence` and has `evaluated=false`, `contains_personal_data=false`, `contains_special_category_data=false`, `sensitivity_level="low"`, `detected_entities == []`, `evidence_spans == []`, `vulnerability_indicators.present=false`, `vulnerability_indicators.categories == []`, `sensor_versions["nuance_stub"] == "stub-0.1"`, and `sensor_error=false`.
- **Notes:** This is the critical acceptance test that payment scenarios do not invoke the semantic layer. The instrumentation should prove both Presidio and the stub were not called.

### test_build_evidence_scenario_4_email_combines_real_presidio_with_labelled_stub
- **Traces to:** MASTER_SPEC.md §1, §2, §5.3, §7 Scenario 4, and §12 acceptance criteria; TASK_LEDGER.md T07 done-when.
- **Input:** Scenario 4 normalised email Action, using the real T06 Presidio sensor and the T07 nuance stub.
- **Expected outcome:** Evidence validates against `app.schemas.evidence.Evidence` and has `evaluated=true`, `contains_personal_data=true`, `contains_special_category_data=true`, `sensitivity_level="high"`, at least one Presidio-origin detected entity or span aligned to the NHS/health content, every detected entity has `source == "presidio"`, `vulnerability_indicators.present=true`, `vulnerability_indicators.confidence == 0.88`, `vulnerability_indicators.source == "nuance_stub"`, `overall_confidence == 0.88`, `sensor_versions["nuance_stub"] == "stub-0.1"`, and `sensor_error=false`.
- **Notes:** Presidio must be real, not mocked, for this functional test. The test should not require a specific Presidio score, only that real Presidio-origin entities/spans exist and line up with the planted content.

### test_build_evidence_scenario_5_email_preserves_uncertain_vulnerability_confidence
- **Traces to:** MASTER_SPEC.md §5.3, §6 threshold behaviour, and §7 Scenario 5; TASK_LEDGER.md T07 done-when.
- **Input:** Scenario 5 normalised email Action, using the real T06 Presidio sensor and T07 nuance stub.
- **Expected outcome:** Evidence validates and has `evaluated=true`, `contains_special_category_data=false`, `vulnerability_indicators.present=true`, `vulnerability_indicators.confidence == 0.62`, `vulnerability_indicators.categories` includes `financial_vulnerability`, `vulnerability_indicators.source == "nuance_stub"`, `overall_confidence == 0.62`, `sensor_versions["nuance_stub"] == "stub-0.1"`, and `sensor_error=false`.
- **Notes:** This test exists to prevent unrelated Presidio scores from overwriting the policy-relevant stub confidence.

### test_build_evidence_scenario_6_email_personal_data_only_allows_logging_evidence_shape
- **Traces to:** MASTER_SPEC.md §5.3 and §7 Scenario 6; TASK_LEDGER.md T07 done-when.
- **Input:** Scenario 6 normalised email Action, using the real T06 Presidio sensor and T07 nuance stub.
- **Expected outcome:** Evidence validates and has `evaluated=true`, `contains_personal_data=true`, `contains_special_category_data=false`, `sensitivity_level="medium"`, at least one Presidio-origin detected entity or span for the customer name/email content, `vulnerability_indicators.present=false`, `vulnerability_indicators.confidence` below the default high-confidence threshold, `vulnerability_indicators.categories == []`, and `sensor_error=false`.
- **Notes:** This confirms the evidence layer identifies personal data without inventing vulnerability or special-category signals.

### test_build_evidence_output_has_no_policy_decision_fields
- **Traces to:** MASTER_SPEC.md §2 and §5.3; AGENTS.md non-negotiable product rules; TASK_LEDGER.md T07 key notes.
- **Input:** Built Evidence for one payment scenario and one email scenario, serialised to a dictionary via the Pydantic model.
- **Expected outcome:** Neither serialised Evidence dictionary contains any of these keys at any level where the Evidence schema could express policy judgement: `decision`, `allow`, `block`, `escalate`, `approval`, `approved`, `enforcement`, `executed`, `required_approval_role`, or `control_id`.
- **Notes:** Evidence is only evidence. OPA/Rego remains the binding judge in later tasks.

### test_build_evidence_presidio_exception_returns_valid_sensor_error_evidence
- **Traces to:** MASTER_SPEC.md §2 fail-closed principle, §5.3 `sensor_error`, and §11 step 4; TASK_LEDGER.md T07 key notes.
- **Input:** An email Action where the Presidio sensor call is patched to raise an exception.
- **Expected outcome:** The builder returns, rather than raises, an `Evidence` instance/dict that validates against `app.schemas.evidence.Evidence`, has `evaluated=true`, `sensor_error=true`, and contains no decision-like fields.
- **Notes:** This does not require Python to make a policy decision; it only prepares the `sensor_error=true` fact for later OPA fail-closed handling.

### test_build_evidence_nuance_exception_returns_valid_sensor_error_evidence
- **Traces to:** MASTER_SPEC.md §2 fail-closed principle, §5.3 `sensor_error`, and §11 step 4; TASK_LEDGER.md T07 key notes.
- **Input:** An email Action where the nuance stub call is patched to raise an exception.
- **Expected outcome:** The builder returns, rather than raises, an `Evidence` instance/dict that validates against `app.schemas.evidence.Evidence`, has `evaluated=true`, `sensor_error=true`, retains schema-valid defaults for entities/spans/vulnerability indicators, and contains no decision-like fields.
- **Notes:** This ensures both semantic sensor failure paths are fail-closed-ready for the later policy engine.

## Coverage checklist
- [x] Happy path covered: all three email scenarios and all three payment scenarios are covered.
- [x] Error/edge cases covered: Presidio exception, nuance stub exception, benign name-only content, and payment semantic skip are covered.
- [x] Spec non-negotiables verified: Evidence has no decision fields; stub is labelled; fixed scenario confidences are preserved; payment path does not invoke semantics; sensor errors surface as `sensor_error=true`.
- [x] Real dependencies flagged: Scenario 4–6 evidence-builder tests must use the real T06 Presidio sensor, not mocked Presidio, except the explicit exception-path tests.

## Gaps or ambiguities
- The ledger Verify step asks for “a script that prints the assembled Evidence for all six scenarios” but does not name a committed script file, and T07 allowed files do not include a scripts directory. Implementer should satisfy this with a one-off command in verification output, not by creating an extra file.
- The spec fixes Scenario 4 confidence `0.88` and Scenario 5 confidence `0.62`; it only says Scenario 6 is low/no-confidence. Tests should require Scenario 6 confidence to be below the default high-confidence threshold and not vulnerability-present, without inventing an exact confidence unless the implementation documents one in the allowed T07 files.
