# Architect Brief — T08: Settings store (runtime-editable)

## Task selected
- Task: T08 — Settings store (runtime-editable)
- Current status: TODO / To do
- Dependencies checked: PASS — T08 depends on T01, and T01 is marked Done in `TASK_LEDGER.md`.

## Source-of-truth references
- MASTER_SPEC.md: §4 technology decisions require `pydantic-settings + a DB-backed settings row`; §6 requires runtime-configurable `HIGH_CONFIDENCE` defaulting to `0.75`, stored in the settings row, passed to OPA as `config.high_confidence_threshold`, and echoed as `threshold_used`; §8 defines enforcement modes `shadow`, `soft`, and `full`; §11 states the pipeline must load runtime settings before OPA decisioning; §12 acceptance criteria require changing the threshold to `0.60` to affect Scenario 5 later.
- TASK_LEDGER.md: T08 goal, dependencies, allowed files, key notes, done criteria, verify step, and reviewer focus.
- AGENTS.md: work on exactly one task; touch only files listed for the current task plus the task test folder; do not start the next task; do not change schemas, file layout, control logic, scenario outcomes, or policy logic; every task must produce committed pytest tests under its listed `tests/T<XX>_<feature>/` folder.

## Allowed files
- `app/settings_store.py`
- `tests/T08_settings/`

## Implementation objective
Implement a simple, persistent settings store backed by the existing Postgres database. It must expose read/update helpers for one settings row containing the runtime confidence threshold and per-control enforcement modes. On first use it should seed defaults, including `high_confidence_threshold = 0.75`. Updates must persist in the database so that reading settings after an app/process restart returns the updated values.

## Non-negotiables
- Keep scope to T08 only. Do not implement OPA integration, policy logic, pipeline wiring, UI routes, or settings page behaviour; those belong to later tasks.
- Use one authoritative settings row. Do not introduce multiple competing sources of the threshold.
- Default threshold must be `0.75`; updating to `0.60` must persist and be readable after restart.
- Per-control mode values must be constrained to the spec modes: `shadow`, `soft`, and `full`.
- Do not hard-code policy decisions or scenario outcomes in this store. It only stores runtime configuration for later OPA/pipeline use.
- Do not touch files outside `app/settings_store.py` and `tests/T08_settings/`. If a database helper outside this file seems necessary, stop and ask rather than broadening scope.
- Tests must be real pytest tests in `tests/T08_settings/`, including `__init__.py` and at least one `test_*.py` file.
- Do not mark T08 as DONE. Human final verification marks task completion.

## Verify step
Ledger verify: update threshold to `0.60`, restart app, confirm it reads `0.60`.

Task-specific checks for the Implementer:
- Run the T08 pytest tests, e.g. `pytest tests/T08_settings -q` or the repository's Docker equivalent if local dependencies require it.
- Demonstrate default seeding by reading settings from an empty settings table/store and confirming `high_confidence_threshold == 0.75`.
- Demonstrate persistence by updating `high_confidence_threshold` to `0.60`, constructing a fresh store/session/connection to simulate restart, and confirming the read value remains `0.60`.
- Demonstrate per-control modes reject values outside `shadow`, `soft`, and `full`.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T08_architect_brief.md` and `briefs/T08_test_brief.md`. Implement exactly T08. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.