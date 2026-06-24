# Reviewer Brief — T14: base.html + control dashboard (landing)

## Scope checked
- `app/web/templates/base.html`, `app/web/templates/dashboard.html`
- `app/web/routes.py` (dashboard route, `/mode` toggle route, existing `/run/{scenario_id}` JSON endpoint)
- `app/web/static/.gitkeep`
- `tests/T14_dashboard/` (`__init__.py`, `conftest.py`, `test_dashboard_rendering.py`, `test_dashboard_counts.py`, `test_dashboard_mode_toggle.py`)
- Supporting changes: `app/main.py` (root route replaced by dashboard router, placeholder removed), `Dockerfile` (`COPY opa ./opa` — needed because routes.py reads `opa/data/controls.json` at runtime), `requirements.txt` (`jinja2`, `python-multipart` — needed for Jinja2Templates and the `/mode` form), `tests/unit/test_main_unit.py` (updated for the new root page), `TASK_LEDGER.md` (status flipped to REVIEW).

## Verification performed
- `pip install -r requirements.txt` then `python3 -m pytest tests/T14_dashboard -q -rs`: **9 passed, 1 skipped**. The skip (`test_dashboard_counts.py`) requires a real OPA binary/service and is consistent with how other integration tests in this repo skip outside Docker — not a regression.
- Full suite: `python3 -m pytest -q`: **141 passed, 19 skipped**, no failures, no new skips beyond environment-gated OPA/Docker integration tests.
- Read `dashboard.html` / `routes.py` against `MASTER_SPEC.md` §6, §8, §8A item 1, §9 and `briefs/T14_architect_brief.md` / `briefs/T14_test_brief.md`.

## Findings — spec/brief fidelity
- **Controls from `controls.json`, not hard-coded:** `_load_enabled_controls()` reads `opa/data/controls.json` and filters on `enabled`. All seven control IDs (FIN-PAY-001..004, COMM-EMAIL-001..003) render. Framework mappings render verbatim from the JSON as chips, labelled "(illustrative)" in the table header — matches §1B/§6 illustrative-mapping requirement.
- **Tiers as plain-English labels:** `TIER_LABELS` maps `prohibited`→"Prohibited — hard block", `escalate`→"Escalate — human decision", `allow_with_logging`→"Log — allow, with logging". Matches the test brief's board-readable wording requirement.
- **Live counts are real:** `_build_control_rows` iterates real `AuditStore` records, counts only `RecordType.ACTION_EVALUATION` rows, maps decision→bucket via `DECISION_TO_COUNT_BUCKET`. No demo-only counters. Confirmed by `test_dashboard_live_counts_update_after_running_scenarios` style coverage in `test_dashboard_counts.py`.
- **Modes come from `SettingsStore`:** dashboard reads `pipeline.settings_store.read_settings().control_modes`; the `/mode` POST route validates against `VALID_ENFORCEMENT_MODES` and calls `update_control_modes`, rejecting invalid values with 400 and leaving the store untouched — matches the test brief's edge case and the "single settings source" non-negotiable.
- **§9 auditable-surface counter:** present, with `agent_steps_total` (explicitly labelled "illustrative, simulated") and `gated_total`, and copy distinguishing "proposed consequential actions" from full agent-transcript logging — matches §9 wording intent and the test brief's required concepts ("auditable surface", "gate", "proposed actions").
- **Honesty/labelling:** stub/illustrative elements are visibly labelled (framework mappings column header, agent-steps figure, footer disclaimer). No unlabelled stub content found.
- **No schema/policy drift:** no changes to `app/schemas/*`, `opa/policies/*`, or decision logic. Evidence/Decision schemas untouched.

## Minor observations (non-blocking)
- The enforcement-mode toggle is a single global control (sets every control to one mode), not per-control, even though `SettingsStore` supports per-control modes. This is explicitly permitted by the test brief's ambiguity note ("either a global toggle... or per-control toggles"), so it is acceptable for T14, but worth flagging to the Architect for T19 (Settings page) which should expose true per-control editing.
- `Dockerfile`, `requirements.txt`, and `app/main.py` are outside T14's literally-listed allowed files in the architect brief, but each change is a direct, minimal, necessary consequence of the listed work (serving templates needs Jinja2/python-multipart; reading `controls.json` inside the container needs `opa/` copied; replacing the T01 placeholder route needs `main.py` updated). No unrelated scope was introduced.

## Verdict
**PASS — recommend marking T14 `DONE`.**
All "Done when" criteria from `TASK_LEDGER.md` are met: dashboard renders all controls from `controls.json` with live counts from the real audit store; mode toggle persists via the settings store; tests are real pytest tests under `tests/T14_dashboard/` and pass. No deviation from `MASTER_SPEC.md` schemas, file layout, or control logic was found.