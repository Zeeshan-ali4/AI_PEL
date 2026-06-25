# Architect Brief — T22: Live event feed with background traffic (headline demo moment)

## Task selected
- Task: T22 — Live event feed with background traffic (headline demo moment)
- Current status: TODO
- Dependencies checked: pass — T22 depends on T13 and T05; both are marked Done in `TASK_LEDGER.md`. T13 provides the integrated full pipeline and audit write path, and T05 provides fixture data used for safe background events.

## Source-of-truth references
- MASTER_SPEC.md: §1 proves interception, real policy decisions, enforcement, and hash-chained audit records; §1A frames the demo around assurance, visible control operation, human oversight, and evidential integrity; §2 preserves the model-is-not-judge rule, default-to-human, fail-closed, and payment semantic-skip requirements; §5.1–§5.5 define the Action, Context, Evidence, Decision, and Evidence Record contracts; §6 defines control precedence, control IDs, and framework mappings; §7 defines the six scenario outcomes that the focal event must preserve; §8 and §8A define the server-rendered assurance UI, decision view expectations, evidence presentation, and audit integrity story; §10 is the canonical file layout; §11 is the pipeline order and must not be restructured; §12 acceptance criteria require correct scenario decisions, payment semantic skip, real Presidio entities for email, and intact audit chain.
- TASK_LEDGER.md: T22 goal, dependencies, allowed files, key notes, Done when, Verify, Reviewer focus, and estimate. Parallelisation notes say T22 can run alongside T23 and T25, but this brief covers T22 only.
- AGENTS.md: work exactly one task; do not start the next task; touch only listed files plus the task test folder; do not silently change schemas, directory layout, control IDs, scenario outcomes, policy logic, or audit semantics; every task must produce committed pytest tests under its task test folder.

## Allowed files
- `app/scenarios/background_events.py`
- `app/pipeline.py`
- `app/web/routes.py`
- `app/web/templates/event_feed.html`
- `app/web/static/event_feed.js`
- `tests/T22_event_feed/`

## Implementation objective
Build T22's live event feed demo moment. A user should be able to run any canonical scenario through a new live feed page/stream so that 8–12 randomly sampled, safe background events pass through the real pipeline first and render as compact green/neutral rows, followed by the focal scenario as the final, visually emphasized row. The focal row must include a real structured pipeline trace showing each stage's inputs/outputs summary and timing. All events — background and focal — must be evaluated by the existing pipeline, enforced by OPA/handler logic, written to the real audit store, and leave the hash chain valid.

## Non-negotiables
- Do not implement a fake feed. Background events and focal events must use the real pipeline path: intercept/normalise, context resolve, semantic evidence only where applicable, OPA decision, enforcement, and audit write.
- Do not restructure the pipeline. Add a lightweight trace collector/wrapper around the existing steps in `app/pipeline.py`; preserve existing `PipelineResult.response_payload()` compatibility for current JSON and template routes.
- The pipeline trace must contain these stage names exactly unless there is a compelling compatibility reason to add aliases: `intercept`, `normalise`, `resolve_context`, `semantic_evidence` or `semantic_skipped`, `policy_decision`, `enforce`, `audit_write`.
- Each trace stage should include `stage_name`, `timestamp`, `duration_ms`, `inputs_summary`, and `outputs_summary`. Summaries must be compact serialisable data derived from real objects/results, not hardcoded demo prose.
- Payment focal events must show that the semantic layer was not invoked. This must reflect the real Evidence object (`evaluated=false`) and should appear in the trace as `semantic_skipped` with clear copy such as “Semantic layer not invoked — structured action.”
- Email focal events must show semantic evidence from the real evidence builder, including Presidio-detected entities where present, the labelled nuance stub confidence/source, and the OPA threshold used in the Decision.
- Background events must be boring by design: use existing action types and clean fixture-compatible data, and ensure they resolve only to `allow` or `allow_with_logging`. They must never accidentally escalate, block, or fail closed under default T22 conditions.
- Create `app/scenarios/background_events.py` with a pool of 20–25 routine templates. Each run must randomly sample 8–12 events so repeated runs produce a visibly different mix. Use deterministic-safe values (for example small clean payments, partner/internal emails with no special-category data, and no fraud/sanctions/blocked customers). Do not invent a new canonical action type unless the existing normaliser/policy path already supports it; TASK_LEDGER examples like “case note update” should be skipped if unsupported by the schema/normaliser.
- The new SSE endpoint must be `GET /run/{scenario_id}/stream` and return `text/event-stream` via FastAPI `StreamingResponse`. It should synchronously run one event at a time and yield one JSON payload per event with at least `{event_index, total_events, is_focal, action_summary, decision, control_id, trace}` where `trace` is only included for the focal event.
- Keep the stream simple: no WebSockets, no background worker, no persistent event bus, no JS build step. A 200–400ms delay between events is acceptable for visual pacing but tests should not become slow/flaky because of real sleeps.
- Add `app/web/templates/event_feed.html` as the live feed UI and `app/web/static/event_feed.js` for EventSource rendering. The focal event must be visually unmistakable: red for `block`/`fail_closed`, amber for `escalate`/other human-review decisions, and green/neutral for allowed decisions.
- Ensure the UI is reachable from the existing scenario runner/dashboard flow without modifying unlisted templates. If a nav link or scenario-card change appears necessary in an unlisted template, stop and ask; do not touch unlisted files.
- All audit records written by T22 must use normal append-only semantics. Do not mutate historical records and do not bypass the existing audit store.
- Do not change Rego policies, `controls.json`, schemas, scenario fixtures, expected §7 outcomes, settings semantics, approval workflow, or audit hash computation.
- A “Reset demo data” affordance is only allowed if it can be implemented entirely in the allowed files and uses existing audit-store capabilities. Do not broaden scope to add reset storage primitives in unlisted files.
- Every task produces tests. The Implementer must create `tests/T22_event_feed/__init__.py` and at least one real `test_*.py` file covering the Test Brief.

## Verify step
Ledger manual verification: Run scenario #3 (fraud block). Watch 8+ green `allow`/safe rows stream in. See the final row turn red with `BLOCK — FIN-PAY-001`. Expand it. Confirm the trace shows all pipeline stages. Switch to audit log and confirm all events are recorded with a valid chain. Run again and confirm the background event mix differs.

Recommended programmatic checks for Implementer/QA:
- `docker compose run --rm app pytest tests/T22_event_feed/`
- Test that the background-event sampler returns 8–12 events and that two samples from the full pool can differ without requiring deterministic production ordering.
- Test that every background template, when run through the real pipeline or a suitably isolated real pipeline fixture, resolves to `allow` or `allow_with_logging` and writes an audit record.
- Test that `/run/3/stream` emits an SSE sequence whose final payload is focal, has decision `block`, has control ID `FIN-PAY-001`, and includes trace stages from intercept through audit write.
- Test that a payment focal trace contains `semantic_skipped`/`evaluated=false`, while an email focal trace includes semantic evidence details derived from the real Evidence object.
- Test that existing `POST /run/{scenario_id}` and `POST /scenarios/{scenario_id}/run` behaviours still work after adding trace support.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T22_architect_brief.md` and `briefs/T22_test_brief.md`. Implement exactly T22. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start T23, T24, T25, T20, or T21. Report changed files and verification result.
