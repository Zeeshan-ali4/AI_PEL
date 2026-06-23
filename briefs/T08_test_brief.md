# Test Brief — T08: Settings store (runtime-editable)

## Spec references
- MASTER_SPEC.md: §4 technology decisions require `pydantic-settings + a DB-backed settings row` for config/settings; §6 requires `HIGH_CONFIDENCE` to be runtime-configurable with default `0.75`, stored in the settings row, passed later as `config.high_confidence_threshold`, and echoed later as `threshold_used`; §8 defines enforcement modes `shadow`, `soft`, and `full`; §8A item 7 requires settings changes to persist and take effect immediately; §11 requires the pipeline to load runtime settings before OPA decisioning; §12 requires moving the threshold to `0.60` to flip Scenario 5 in later integration.
- TASK_LEDGER.md: T08 acceptance criteria require a DB-backed settings row containing `high_confidence_threshold` and per-control mode, default seeding on first run, read/update helpers, threshold update persistence across app restart, and rejection of hard-coded threshold sources elsewhere.
- Architect Brief: `briefs/T08_architect_brief.md` confirms T08 depends only on T01, allowed files are `app/settings_store.py` and `tests/T08_settings/`, and the store must remain a simple one-row source of truth without OPA, pipeline, UI, or policy implementation.

## Target test location
- Folder: `tests/T08_settings/`
- Suggested files:
  - `__init__.py` — package marker for the T08 test folder.
  - `test_settings_store.py` — covers default seeding, read/update persistence, validation of threshold bounds and per-control modes, and the single-row source-of-truth behaviour.

## Test cases

### test_settings_seed_defaults_on_empty_store
- **Traces to:** MASTER_SPEC.md §4, §6; TASK_LEDGER.md T08 Key notes and Done when.
- **Input:** Start with an empty settings table/store using the T08 settings store API, then read settings without pre-existing data.
- **Expected outcome:** The store seeds exactly one settings row and returns `high_confidence_threshold == 0.75`. Per-control mode data is present and every stored mode is one of `shadow`, `soft`, or `full`.
- **Notes:** This is the happy-path default-seeding acceptance test. It should use a real database-backed store for persistence semantics; no in-memory mock that bypasses the store's DB code.

### test_threshold_update_persists_across_fresh_store_instance
- **Traces to:** MASTER_SPEC.md §6, §8A item 7, §12; TASK_LEDGER.md T08 Done when and Verify.
- **Input:** Read seeded settings, update `high_confidence_threshold` to `0.60`, then construct a fresh store/session/connection against the same database to simulate an app restart and read settings again.
- **Expected outcome:** The fresh store returns `high_confidence_threshold == 0.60`, proving the update persisted beyond the original store/session object.
- **Notes:** This is the core T08 acceptance test. It does not need to run Scenario 5 or call OPA; those are T10/T13/T19 responsibilities.

### test_threshold_update_rejects_invalid_values
- **Traces to:** MASTER_SPEC.md §6 threshold semantics; Architect Brief non-negotiable that runtime settings are authoritative and safe for later OPA input.
- **Input:** Attempt to update `high_confidence_threshold` to invalid values outside a confidence range, for example `-0.01` and `1.01`, and to a non-numeric value if the API surface permits such input.
- **Expected outcome:** The settings store rejects invalid threshold values with a clear exception or validation error, leaves the previously persisted valid threshold unchanged, and still reads the valid value afterwards.
- **Notes:** The spec defines confidence values as bounded 0..1 elsewhere in Evidence and uses threshold as a confidence cutoff. The store should protect downstream policy input from invalid runtime config.

### test_per_control_modes_accept_only_spec_modes
- **Traces to:** MASTER_SPEC.md §8 and §8A item 7; TASK_LEDGER.md T08 Goal.
- **Input:** Update one or more per-control mode values to each valid mode (`shadow`, `soft`, `full`), then attempt to update a control mode to an invalid value such as `monitor`, `disabled`, or an empty string.
- **Expected outcome:** Valid modes persist and are returned on read. Invalid mode values are rejected with a clear validation error, and the last valid persisted mode remains unchanged.
- **Notes:** Do not require policy execution or enforcement behaviour here. T08 only verifies persistence and validation of the modes that later tasks consume.

### test_settings_store_uses_single_authoritative_row
- **Traces to:** MASTER_SPEC.md §4 and §6; TASK_LEDGER.md T08 Key notes and Reviewer focus; Architect Brief non-negotiable source-of-truth requirement.
- **Input:** Perform repeated reads and updates through the public settings store helpers, including threshold and per-control mode updates.
- **Expected outcome:** The backing store contains exactly one active settings row after repeated operations, and all reads return values from that row. There must not be multiple competing rows with divergent thresholds.
- **Notes:** This test should assert observable database/store state through public or intentionally exposed helper APIs only. It should not require implementing unrelated migration infrastructure outside the T08 allowed files.

### test_settings_payload_ready_for_future_policy_config
- **Traces to:** MASTER_SPEC.md §6 and §11; TASK_LEDGER.md T08 Key notes that values feed OPA input in T10 and pipeline in T13.
- **Input:** Read settings after default seed and after updating threshold/modes.
- **Expected outcome:** The returned object or serialization includes a clearly named `high_confidence_threshold` value and per-control mode mapping suitable for later construction of OPA `config.high_confidence_threshold` input, without embedding any policy decision, scenario outcome, or OPA-specific control logic.
- **Notes:** This test guards scope. The settings store should expose runtime configuration only; it must not decide allow/block/escalate or evaluate scenarios.

## Coverage checklist
- [ ] Happy path covered: empty-store default seed and valid threshold/mode updates.
- [ ] Error/edge cases covered: invalid thresholds, invalid modes, repeated reads/updates, fresh-store persistence.
- [ ] Spec non-negotiables verified: one settings row, default `0.75`, runtime update to `0.60`, only `shadow`/`soft`/`full` mode values, no decision logic in the store.
- [ ] Real dependencies flagged: persistence tests should exercise a real database-backed store or an equivalent on-disk DB configured through the T08 store code; do not replace the settings store persistence layer with mocks that cannot prove restart persistence.

## Gaps or ambiguities
- The task does not enumerate exact control IDs that must have per-control defaults before `controls.json` exists in T09. Suggested clarification for the Implementer: provide a mapping shape that can store known spec control IDs from MASTER_SPEC.md §6 if practical, but do not create `controls.json` or policy metadata in T08.
- The task does not specify default per-control mode values. Suggested clarification for the Implementer: choose a simple, documented default consistent with safe adoption (`shadow` is the least disruptive initial mode), unless an existing config pattern in the repo already establishes a default.
- The task does not prescribe the DB access library or migration approach for `app/settings_store.py`. Tests should validate behaviour, not force an internal implementation, while respecting the allowed-file limit.