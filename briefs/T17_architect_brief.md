# Architect Brief — T17: Evidence record view + export

## Task selected
- Task: T17 — Evidence record view + export
- Current status: To do
- Dependencies checked: pass — `TASK_LEDGER.md` lists T17 as depending on T14, and T14 is marked Done. Earlier UI foundation tasks needed by T14/T17 are also present in the repo: the dashboard/base template and shared `app/web/routes.py` route module already exist.

## Source-of-truth references
- MASTER_SPEC.md: §5.5 Evidence Record schema and hash fields; §8A item 5 Evidence record view; §1/§1A evidential reliability and exportable audit record; §2 non-negotiable separation of evidence from policy decision.
- TASK_LEDGER.md: T17 task entry, especially Goal, Depends on, Files, Done when, Verify, and Reviewer focus.
- AGENTS.md: work on exactly one task; touch only task files plus the Test Brief test file; do not create extra files unless allowed; every task must produce committed pytest tests; do not change schemas, policy decisions, scenario outcomes, or append-only audit semantics.

## Allowed files
- `app/web/templates/record.html`
- `app/web/routes.py`
- `tests/T17_record_view/`

## Implementation objective
Add a single-record evidence view and audit export path for existing audit `EvidenceRecord` rows. A user must be able to open any audit record, read it as a clear non-technical assurance artefact, print it, and export it for audit in both JSON and a human-readable format. The page must show the fields called out by the spec: `record_hash`, `prev_hash`, approver, approval reason, execution status, plus the relevant action/context/evidence/decision details already persisted in the audit row.

The implementation should reuse existing route infrastructure in `app/web/routes.py`, existing schema/store types, existing Tailwind/base layout conventions, and existing T15/T16 helper patterns where useful. Keep this task focused on record display/export only; do not build the T18 chronological audit log, chain verification UI, or tampering UI.

## Non-negotiables
- Evidence remains evidence only. Do not add any allow/block/decision/approval/enforcement field to the Evidence schema or evidence payload.
- Do not alter audit records to support viewing or exporting. Reads and exports must be read-only operations against existing records.
- Approval rows must continue to be represented as separate `approval_decision` records linked by `correlation_id` and `references_hash`; do not mutate original `action_evaluation` rows.
- Preserve the existing Evidence Record schema names exactly, including `record_hash`, `prev_hash`, `references_hash`, `human_approver`, `approval_reason`, `executed`, and `record_type`.
- Exports must be genuinely useful to a risk/audit reviewer. The human-readable export must not be just an unformatted raw dump; use clear labels, sections, and printable styling.
- JSON export should serialize the persisted record faithfully using schema/model serialization rather than hand-built lossy fields.
- Human-readable export may be HTML if printable/downloadable; do not introduce a PDF generation dependency unless the PM/BA Test Brief or implementer has a very small, reliable approach within the allowed files.
- The record view must handle both `action_evaluation` and `approval_decision` rows. For approval rows, display the approver, reason, execution result, and link/reference hash to the original record.
- Missing/unknown record identifiers should return a clear 404, not a server error.
- Stay within the allowed files for T17 plus the test file path specified by the PM/BA Test Brief. If an implementation seems to require changes outside `record.html`, `app/web/routes.py`, or `tests/T17_record_view/`, stop and escalate.

## Suggested route shape
These are recommendations, not schema changes:
- `GET /records/{record_hash}` — render `record.html` for a single record found by `record_hash`.
- `GET /records/{record_hash}/export.json` — return a downloadable JSON export.
- `GET /records/{record_hash}/export.html` — return a printable/downloadable human-readable HTML export.

Use `record_hash` as the stable identifier because it is already central to the evidence record and approvals reference it. If the implementer chooses an ID-based route for practical reasons, they must still visibly show and export `record_hash` and `prev_hash`.

## Verify step
Ledger verify: open a record; export; open the exported file.

Programmatic checks expected for this task:
- Run the PM/BA-specified pytest file under `tests/T17_record_view/`.
- At minimum, tests should create or run a scenario to generate an audit record, assert the record page opens, assert key fields are visible (`record_hash`, `prev_hash`, execution status), assert JSON export is valid and faithful, and assert the human-readable export contains labelled sections suitable for a non-technical reviewer.
- Also run the broader relevant UI test subset if practical to ensure existing dashboard/scenario/approval routes were not regressed.

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T17_architect_brief.md and briefs/T17_test_brief.md. Implement exactly T17. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
