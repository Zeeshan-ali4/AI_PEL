# Architect Brief — T07: Nuance stub + evidence builder

## Task selected
- Task: T07 — Nuance stub + evidence builder
- Current status: To do
- Dependencies checked: **pass** — T07 depends on T06, and T06 is marked Done in `TASK_LEDGER.md`. Earlier sequence tasks T02–T05 are also marked Done, so schemas, scenarios, normalisation, context resolution, and the Presidio sensor are available for this task.

## Source-of-truth references
- MASTER_SPEC.md: §1 and §1A require the nuance model to be a clearly labelled stub that provides bounded evidence only; §2 requires Presidio before the stub, no model-as-judge behaviour, human-default handling of uncertainty, and no decision fields in Evidence; §3 and §11 define that the semantic layer runs only for email actions while payments skip it; §4 fixes `app/semantic/nuance_stub.py` as a deterministic labelled stub; §5.3 defines the exact Evidence schema; §7 fixes the deterministic scenario confidences and expected evidence conditions for Scenarios 4–6; §10 fixes the canonical file layout; §12 acceptance criteria require payment scenarios to have `evidence.evaluated=false`, Scenario 4 to show real Presidio entities plus labelled stub confidence, and Scenario 5 to expose the 0.62 confidence used later by settings/policy.
- TASK_LEDGER.md: T07 goal, dependency, allowed files, key notes, done-when criteria, verify step, and reviewer focus. The task requires deterministic planted-phrase matching with fixed confidences `0.88`, `0.62`, and low/no-confidence output, plus an Evidence builder that assembles the full schema from Presidio output and stub output.
- AGENTS.md: Work on exactly one task; touch only files listed for the current task; tests are mandatory under the task test folder; do not silently change schemas, file layout, scenario outcomes, or policy logic; Evidence must not contain allow, block, decision, approval, or enforcement fields; payment scenarios must not invoke the semantic layer; stubs must be visibly labelled.

## Allowed files
- `app/semantic/nuance_stub.py`
- `app/semantic/evidence_builder.py`
- `tests/T07_evidence/`

Tests are required by AGENTS.md. The PM/BA Test Brief must name a concrete target test file under `tests/T07_evidence/`, and the Implementer must create `tests/T07_evidence/__init__.py` plus real pytest coverage there.

## Implementation objective
Build the T07 semantic evidence assembly layer without making any policy decision. Add a visibly labelled, deterministic-by-input nuance stub that maps the planted scenario phrases to fixed vulnerability signals, then add an evidence builder that combines T06 Presidio output and the stub output into the canonical `Evidence` schema.

The expected shape is:
- Email actions: run Presidio first, run the nuance stub, assemble `Evidence(evaluated=true, ...)`.
- Payment actions: skip Presidio and the nuance stub entirely, assemble `Evidence(evaluated=false, ...)` with empty entities/spans, no vulnerability present, low sensitivity, zero/low confidence as appropriate, `sensor_error=false`, and sensor versions still identifying the available components without implying sensors were executed.
- Sensor exceptions: return a valid fail-closed-ready Evidence object with `sensor_error=true`; do not raise through to policy callers in normal task usage.

The builder should be narrow and reusable by the later pipeline task. It may expose a simple function such as `build_evidence(action)` or equivalent, but it must accept enough information to determine email vs payment and to scan the original email body from the action content/parameters already established by earlier tasks. Keep implementation coupled to existing schemas and existing T06 Presidio adapter output rather than inventing a parallel semantic schema.

## Non-negotiables
- Evidence remains evidence only. Do not add or return allow/block/escalate/approval/enforcement/decision fields anywhere in T07 output.
- The nuance classifier is a **stub** and must be unmistakably labelled in code-level output with `source: "nuance_stub"` and `sensor_versions["nuance_stub"] == "stub-0.1"`.
- The nuance stub must be deterministic by input text. It must map Scenario 4 planted vulnerability phrase/content to `present=true`, confidence `0.88`, and relevant vulnerability categories; Scenario 5 planted phrase `"struggling a bit since losing my job"` to `present=true`, confidence `0.62`, and `financial_vulnerability`; Scenario 6 customer-name-only content to `present=false` with low/zero confidence and no categories.
- Presidio findings from T06 must remain Presidio-origin evidence (`source: "presidio"`) and should be converted into `DetectedEntity` and `EvidenceSpan` entries that validate against `app.schemas.evidence.Evidence`.
- `contains_personal_data` must be true when Presidio detects personal data. `contains_special_category_data` must be true for Scenario 4's NHS/health evidence and false for Scenarios 5 and 6.
- `sensitivity_level` must be high when special-category data is present, medium when non-special personal data or vulnerability indicators are present, and low for payment skip/no semantic findings unless the implementer documents a narrower schema-consistent mapping in code/tests.
- `overall_confidence` must preserve the scenario-relevant stub confidence values for policy: Scenario 4 `0.88`, Scenario 5 `0.62`, and Scenario 6 below the high-confidence threshold but not vulnerability-present. Do not let unrelated Presidio scores overwrite the required vulnerability confidence for Scenarios 4 and 5.
- Payment scenarios must not invoke the semantic layer. Tests should prove the payment path can assemble `evaluated=false` without calling Presidio or the nuance stub.
- On any Presidio or nuance-stub exception, set `sensor_error=true` in the returned Evidence object so later OPA logic can fail closed. Python must not make a non-fail-closed policy decision here.
- Do not edit schemas, scenario definitions, context fixtures, normaliser code, policy code, Dockerfile, requirements, or prior task tests for T07 unless the human explicitly updates the allowed file list.

## Verify step
Ledger verify step: run a script that prints the assembled Evidence for all six scenarios.

Minimum implementation-time checks:
- `docker compose run --rm app pytest -q tests/T07_evidence`
- A manual/one-off command that loops Scenarios 1–6, normalises or otherwise constructs the relevant Action input, calls the evidence builder, validates/prints each assembled `Evidence`, and confirms payment scenarios are `evaluated=false` while email scenarios are `evaluated=true`.

Expected verification observations:
- Scenario 1 payment: `evaluated=false`, no entities/spans, `sensor_error=false`.
- Scenario 2 payment: `evaluated=false`, no entities/spans, `sensor_error=false`.
- Scenario 3 payment: `evaluated=false`, no entities/spans, `sensor_error=false`.
- Scenario 4 email: `evaluated=true`, `contains_special_category_data=true`, Presidio-origin NHS/health entities or spans present, vulnerability source `nuance_stub`, confidence `0.88`, sensor version `stub-0.1`.
- Scenario 5 email: `evaluated=true`, vulnerability present with confidence `0.62`, category `financial_vulnerability`, no special-category flag.
- Scenario 6 email: `evaluated=true`, personal-data-only evidence, no special-category flag, vulnerability not present.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T07_architect_brief.md` and `briefs/T07_test_brief.md`. Implement exactly T07. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start T08 or any other task. Report changed files and verification result.