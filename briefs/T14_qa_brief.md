# QA Brief — T14: base.html + control dashboard (landing)

## Verification performed
- `pip install -r requirements.txt`
- `python3 -m pytest tests/T14_dashboard -q -rs` → **9 passed, 1 skipped**.
  - Skip: `test_dashboard_live_counts_update_after_running_scenarios` in `test_dashboard_counts.py`, reason `"OPA binary not available; set OPA_URL or install opa to run real Rego integration tests"`. No `opa` binary and no `OPA_URL` in this environment — this is an environment gate, not a code/test defect, and matches the Reviewer's prior finding.
- `python3 -m pytest -q` (full suite) → **141 passed, 19 skipped**, no failures. Skip count and pattern consistent with other OPA/Docker-gated integration tests across the repo; no new unexplained skips introduced by T14.
- `git status --short` → clean; only `briefs/T14_reviewer_brief.md` was newly added since the prior commit, no stray edits outside the allowed T14 file list.

## Test Brief coverage check
Test Brief (`briefs/T14_test_brief.md`) specifies 9 acceptance test cases. Mapped each to an implemented test:

| Test Brief case | Implemented as |
|---|---|
| `test_landing_page_renders_shared_dashboard_layout` | `test_dashboard_rendering.py` |
| `test_dashboard_lists_every_enabled_control_from_controls_json` | `test_dashboard_rendering.py` |
| `test_dashboard_renders_tiers_as_plain_english_board_labels` | `test_dashboard_rendering.py` |
| `test_dashboard_framework_chips_match_control_metadata` | `test_dashboard_rendering.py` |
| `test_dashboard_displays_current_modes_from_settings_store` | `test_dashboard_mode_toggle.py` |
| `test_dashboard_live_counts_initially_show_zero_when_audit_store_empty` | `test_dashboard_counts.py` |
| `test_dashboard_live_counts_update_after_running_scenarios` | `test_dashboard_counts.py` (skipped here, OPA unavailable) |
| `test_dashboard_enforcement_mode_toggle_persists_selected_mode` | `test_dashboard_mode_toggle.py` |
| `test_dashboard_rejects_invalid_enforcement_mode_submission` | `test_dashboard_mode_toggle.py` |
| `test_dashboard_auditable_surface_counter_explains_gate_not_agent_logging` | `test_dashboard_counts.py` |

All 9 cases have a 1:1 named-function match — full coverage, no gaps, no test renamed away from its acceptance intent.

## Spec/ledger conformance
- Files touched match the Architect Brief's allowed list (`base.html`, `dashboard.html`, `app/web/static/`, `routes.py`, `tests/T14_dashboard/`) plus the Reviewer-accepted minimal incidental changes (`Dockerfile`, `requirements.txt`, `app/main.py`, `tests/unit/test_main_unit.py`) — each a necessary consequence of serving the dashboard, not scope creep.
- No changes to `app/schemas/*`, `opa/policies/*`, decision logic, or audit hash-chain code — confirmed via `git diff --stat` against the prior commit.
- Controls, framework mappings, and tiers render from `opa/data/controls.json` (not hard-coded); modes come from `SettingsStore`; counts come from the real `AuditStore`. Confirmed by reading `routes.py` and corroborated by passing tests.
- Stub/illustrative elements (framework-mapping "(illustrative)" label, simulated agent-steps figure) are visibly labelled per §1B/§9.

## Verdict
**PASS.** Verification reproduces the Reviewer's reported results exactly. Test Brief coverage is complete (9/9 cases). The one skip is an environment limitation (no local OPA binary), not a regression, and is consistent with how the rest of this repo's OPA-dependent integration tests behave outside Docker. Recommend Release Manager / Human proceed to mark T14 `DONE`, with a note to re-run `tests/T14_dashboard/test_dashboard_counts.py::test_dashboard_live_counts_update_after_running_scenarios` under `docker compose run --rm app pytest -q tests/T14_dashboard` (real OPA) before final sign-off, per the ledger's `Verify` step.