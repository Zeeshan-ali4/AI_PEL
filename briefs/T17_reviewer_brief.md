# Review Report — T17: Evidence record view + export

## Verdict
APPROVE

## Critical findings
- None.

## Spec and ledger compliance
- Correct task only: yes
- Dependencies respected: yes (T14 is `Done`; route module and base template already existed)
- Allowed files only: yes (`app/web/routes.py`, `app/web/templates/record.html`, `tests/T17_record_view/` plus the `TASK_LEDGER.md` status line and the prior architect/test brief commits — no other files touched)
- `Done when` satisfied: yes — any record opens cleanly at `GET /records/{record_hash}`; JSON export (`/export.json`) and human-readable export (`/export.html`) both work and are reviewer-readable, not raw dumps
- `Verify` satisfied: not run — this environment has no Docker daemon and no `opa` binary/network access, so the real-OPA-backed pytest suite could only be collected, not executed (all 7 tests in `tests/T17_record_view/` report `skipped` via the `opa_url` fixture's `pytest.skip`). Code was reviewed statically instead; a human with Docker/OPA available must run `docker compose run --rm app pytest tests/T17_record_view -q` before this is truly verified end-to-end.
- Reviewer focus satisfied: yes — the export is genuinely sectioned (Action / Context used / Evidence / Binding decision / Execution status / Hash chain) with plain-English labels, not a raw JSON/preformatted dump; `test_human_readable_export_is_printable_and_non_technical` explicitly asserts the body does not contain a raw `{"action_id"` blob.

## Product invariant checks
- Model is not judge: pass — record view only displays `decision_label`/`control_id` sourced from the persisted `Decision`; no new decision logic in Python.
- OPA/PDP owns decisions: pass — no decision computation added; routes are read-only lookups against existing `EvidenceRecord` rows.
- Evidence has no decision fields: pass — `record.html` Evidence section only renders `contains_personal_data`, `contains_special_category_data`, `sensitivity_level`, `overall_confidence`; JSON export serializes the persisted `Evidence` model via `record.model_dump(mode="json")`, and the test asserts none of `decision/allow/block/approval/enforcement` appear in the exported evidence object.
- Fail-closed preserved: not applicable (no pipeline/OPA-path changes in this task).
- Append-only audit preserved: pass — `_get_record_or_404` / `_record_view_context` only read via `pipeline.audit_store.read_records()`; no write/update path added. Approval rows are displayed as a distinct, clearly-labelled "Appended approval decision" section referencing the original by `references_hash`, without mutating or re-rendering the original as edited.
- Stubs labelled: pass — Evidence section retains the existing "nuance_stub — model stand-in, not a production model" label and the "Evidence informs the policy decision... policy engine is the judge" framing; framework mappings are tagged "(illustrative mapping)".
- Scenario outcomes preserved: pass — no scenario, normaliser, context, policy, or enforcement logic was touched; `scenarios/scenarios.py` and Rego policies are untouched.

## Required changes
None.

## Non-blocking notes
- Test execution could not be confirmed in this sandbox (no Docker daemon, no `opa` binary, outbound download blocked) — tests collected without import errors and skip cleanly via the existing `opa_url` fixture pattern (consistent with T15/T16). A human with the full Docker/OPA toolchain should run the suite before marking T17 `DONE`, per `AGENTS.md`'s "Verify" gate.
- `record.html` is shared for both the on-page view and the `/export.html` download (toggled by `is_export`); this reuse is reasonable and keeps the task within its file allowance, but note it for QA as the single template serving two routes.
