# Architect Brief — T06: Presidio sensor (REAL)

## Task selected
- Task: T06 — Presidio sensor (REAL)
- Current status: To do
- Dependencies checked: **pass for ledger status** — T02 is marked Done and T01 is also marked Done, satisfying the stated dependency line for T06. T03–T05 are also marked Done in the current build sequence, so the scenario bodies needed for manual verification are available.
- Pipeline status: **BLOCKED for implementation until dependency-file scope is clarified** — T06 requires the real `presidio-analyzer` package, but the T06 allowed file list does not include `requirements.txt`, and the current dependency list does not include `presidio-analyzer`. The Implementer must not work around this by stubbing Presidio or silently editing files outside T06 scope.

## Source-of-truth references
- MASTER_SPEC.md: §2 requires deterministic tools before model stubs and says Presidio runs first; §4 selects real in-process `presidio-analyzer` with spaCy `en_core_web_sm`; §5.3 defines the Evidence output fields that later consume Presidio entities and spans; §7 requires Scenario 4 real Presidio detection on NHS/health content and Scenario 6 personal-data-only detection; §10 fixes the canonical file layout.
- TASK_LEDGER.md: T06 goal, dependencies, allowed files, key notes, done-when, verify step, and reviewer focus. T06 requires real PII/PHI detection, a custom UK NHS number recognizer, raw evidence only, and aligned spans.
- AGENTS.md: Work on exactly one task; touch only files listed for the current task; do not create extra files unless explicitly allowed; real components stay real; the Evidence schema must not contain decision/enforcement fields; if a task appears to require a file outside the allowed list, stop and ask.

## Allowed files
- `app/semantic/presidio_sensor.py`
- `tests/T06_presidio/`

Tests are required by AGENTS.md. The PM/BA Test Brief must name a concrete target test file under `tests/T06_presidio/`, and the Implementer must create `tests/T06_presidio/__init__.py` plus real pytest coverage there.

## Implementation objective
Build a real Presidio-based deterministic sensor for email body text. It should initialize and call Presidio AnalyzerEngine, register a custom UK NHS number recognizer, and return raw entity/span/score evidence for downstream T07 evidence assembly. It must not classify policy outcomes, infer allow/block/escalate, or populate any final Evidence decision fields. It should be usable by T07 as the deterministic first-stage sensor before the labelled nuance stub.

Because `presidio-analyzer` is absent from `requirements.txt` and `requirements.txt` is outside the T06 file list, implementation should not proceed until the human updates the task scope or confirms that dependency management was intentionally handled elsewhere. If scope is updated, keep the implementation narrowly limited to the two allowed paths plus any explicitly approved dependency file.

## Non-negotiables
- Presidio must be real. Do not hardcode scenario outputs and do not replace Presidio with regex-only detection.
- The custom NHS-number recognizer may use a deterministic pattern/checksum-style recognizer, but it must be registered with Presidio and returned as Presidio analyzer output, not as a separate policy judgement.
- Return bounded raw evidence only: entity type, score, source (`presidio`), and character spans with labels. No allow/block/escalate/approval/execution field may appear in this task.
- Scenario 4 must yield entities/spans that include the planted NHS number and health-related content from the real email body.
- Scenario 6 must yield only personal data from the customer-name-only body; it must not produce special-category/vulnerability policy conclusions in T06.
- Spans must line up with the original text using Python string offsets (`start` inclusive, `end` exclusive), so later UI highlighting can trust them.
- Payment scenarios are out of scope for T06; semantic skipping for payments is handled later in T07/T13.
- Do not edit schemas, scenario text, context fixtures, normaliser code, policy code, Dockerfile, or `requirements.txt` unless the human explicitly updates T06 allowed files.

## Verify step
Ledger verify step: run a script that runs the sensor on the three email bodies from Scenarios 4, 5, and 6 and prints detected entities plus spans.

Minimum implementation-time checks once the dependency scope is resolved:
- `docker compose run --rm app pytest -q tests/T06_presidio`
- A manual/one-off command that imports the scenario catalog, extracts the three email bodies, calls the Presidio sensor, and prints each detected entity with entity type, score, span offsets, and matched text.

Expected verification observations:
- Scenario 4 includes a Presidio-origin entity for NHS number `485 777 3456` and health-related evidence around the planted cancer/health content.
- Scenario 5 may detect personal data such as a name if Presidio finds it; it must not emit a policy decision.
- Scenario 6 detects the planted customer name only, with no health/NHS entity.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T06_architect_brief.md` and `briefs/T06_test_brief.md`. Implement exactly T06 only after the dependency-file blocker is resolved. Touch only the allowed files above plus the test file specified in the Test Brief, and any dependency file only if the human explicitly updates T06 scope. Do not start T07 or any other task. Report changed files and verification result.