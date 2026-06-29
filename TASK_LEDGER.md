# Task Ledger — Runtime Policy Enforcement Gate (Demo Build)

**Companion to:** `MASTER_SPEC.md` v1.1 (the source of truth). This ledger is the *build order*. It does not restate the spec; it points into it.

## Current build state

- Current task: T22 / T23 / T25 (parallelisable); T20 and T21 pending revised dependencies
- Last completed task: T19
- Known blockers: none
- **New since last update:** Phase 5 — Evidence & Assurance Enhancements (T26–T29, backlog T30) added below. These exist to make the demo's core sales argument explicit for a Risk & Assurance buyer: that without a deterministic policy layer it is hard to know what evidence to log or whether it is sufficient for regulatory reporting, and that this build answers both questions structurally. T26–T29 are mostly template/content work over fields the pipeline already produces; only T29 touches the schema (see its note on Golden rule 6).

## How to use this ledger

- **Claude Code = architect / orchestrator / reviewer.** It holds this ledger, picks the next task whose dependencies are all `DONE`, hands that one task to Codex, then checks the result against the task's **Done when** and **Reviewer focus** before marking it `DONE`.
- **Codex = implementer.** It does exactly one task at a time, touching only the files listed for that task.
- **You = the human gate.** After each task, run the **Verify** step yourself. If it fails, the task is not done — do not move on.

### Golden rules (repeat to Codex every task)
1. Do not start a task whose dependencies are not `DONE`.
2. Touch only the files listed in the task. Do not create files outside `MASTER_SPEC.md` §10.
3. Real components stay real (Presidio, OPA, hash chain). Stubs stay labelled.
4. The Evidence schema has no decision field. The decision comes from OPA, not Python.
5. The audit table only ever receives INSERTs (see spec §5.5 — append-only approvals).
6. If a task forces a change to a schema or the file layout, **stop and update the spec first.**

### Spec clarification baked into this ledger
Approvals are **append-only**: an escalation writes an `action_evaluation` record; a human decision appends a linked `approval_decision` record. Nothing mutates an existing row. (Spec §5.5 / §8A item 4, updated.)

---

## Sequence overview (dependency order)

```
Phase 0  Foundations         T01
Phase 1  Contracts           T02
Phase 2  Components          T03 → T04 → T05 → T06 → T07 → T08 → T09 → T10 → T11 → T12 → T13
Phase 3  Assurance UI        T14 → T15 → T16 → T17 → T18 → T19
Phase 3B Production Feel     T22 (parallel: T23, T25) → T24
Phase 4  Verify & present    T20 → T21
Phase 5  Evidence & Assurance T26 → T27 → T28 → T29   (T30 backlog, not scheduled)
```

Integration milestone is **T13** (all six scenarios pass end-to-end via a JSON endpoint, before any UI). Demo-ready is **T19**. Production-feel milestone is **T24** (live event feed, rule editor, audit security). Phase 5 is the **evidence-sufficiency milestone**: it does not change what the gate decides, only how clearly the demo proves, to a regulator-literate audience, that the evidence it produces is structurally adequate.

---

# PHASE 0 — Foundations

## T01 — Repo scaffold + Docker Compose + skeleton app + connectivity check
- **Status:** Done
- **Goal:** `docker compose up` starts three services (`app`, `opa`, `postgres`); a FastAPI app serves a placeholder page and a `/health` endpoint that confirms it can reach OPA and Postgres.
- **Depends on:** none
- **Spec refs:** §3, §4, §10
- **Files:** `docker-compose.yml`, `Dockerfile`, `requirements.txt`, `.env.example`, `app/__init__.py`, `app/main.py`, `app/config.py`, `README.md` (stub)
- **Key notes (novice):** App on port **8080**, OPA on **8181**, Postgres on **5432**. Put `python -m spacy download en_core_web_sm` in the Dockerfile now (so Presidio works later without a surprise). `/health` should make a real HTTP call to OPA (`GET /health`) and a real connection to Postgres, and return JSON `{app:ok, opa:ok|fail, db:ok|fail}`.
- **Done when:** `docker compose up` runs with no crash; `http://localhost:8080/health` returns all-ok; `http://localhost:8080/` returns a placeholder page.
- **Verify:** `docker compose up --build`, then open `/health` and confirm `opa:ok, db:ok`.
- **Reviewer focus:** that OPA and Postgres are *actually* reached (not hard-coded ok); that ports and service names match the spec so later tasks don't drift.

---

# PHASE 1 — Contracts

## T02 — Pydantic v2 schemas (all five)
- **Status:** Done
- **Goal:** Implement Action, Context, Evidence, Decision, EvidenceRecord exactly as spec §5 (including `record_type`, `references_hash`, `threshold_used`).
- **Depends on:** T01
- **Spec refs:** §5 (all), §2 (no decision field on Evidence)
- **Files:** `app/schemas/action.py`, `context.py`, `evidence.py`, `decision.py`, `audit.py`, `tests/T02_schemas/`
- **Key notes:** Field names must match the spec verbatim — every later task imports these. Use enums for the closed value sets (decision types, status, sensitivity, record_type, enforcement_mode). Add docstrings explaining each field in plain English (this is your living data dictionary).
- **Done when:** all five models import cleanly and validate a hand-built example each; Evidence has **no** allow/block/decision field.
- **Verify:** `docker compose run --rm app python -c "from app.schemas.evidence import Evidence; print('ok')"` (repeat per module), or a tiny pytest that instantiates each.
- **Reviewer focus:** exact field-name fidelity to §5; confirm Evidence cannot express a decision.

---

# PHASE 2 — Components

## T03 — Scenarios + agent simulator + SDK wrapper (PEP)
- **Status:** Done
- **Goal:** Encode the six scenarios (spec §7) as data; an agent simulator that emits a raw tool call per scenario; an SDK wrapper that **intercepts** the call and hands it to the pipeline entry point (pipeline itself comes in T13 — for now the wrapper calls a placeholder that echoes the raw call).
- **Depends on:** T02
- **Spec refs:** §7, §3 (PEP), §1 (interception is the headline)
- **Files:** `scenarios/scenarios.py`, `app/pep/agent_simulator.py`, `app/pep/sdk_wrapper.py`, `tests/T03_scenarios/`
- **Key notes:** The SDK wrapper is the conceptual product — make the interception point obvious and well-commented (this is what you point at in the demo). Scenario data must include the planted email bodies for #4/#5/#6 and the fixture customer IDs for #1/#2/#3.
- **Done when:** each scenario can be emitted and intercepted; the wrapper logs "intercepted before execution" and passes a raw tool-call dict onward.
- **Verify:** run a script that loops the six scenarios and prints each intercepted raw call.
- **Reviewer focus:** that execution genuinely cannot proceed without passing through the wrapper; planted content matches the §7 confidence expectations (0.88 / 0.62).

## T04 — Action normaliser
- **Status:** Done
- **Goal:** Convert each raw tool call into the canonical Action (spec §5.1), mapping tool names to `action_type` (`financial.payment.issue`, `communication.email.send`).
- **Depends on:** T03
- **Spec refs:** §5.1
- **Files:** `app/normaliser/normaliser.py`, `tests/T04_normaliser/`
- **Key notes:** Generate `action_id` and `correlation_id` (uuid4) here; set `timestamp`, `environment="demo"`, carry `enforcement_mode` through. Unknown tool → raise a clear error (not a silent default).
- **Done when:** all six scenarios normalise to valid Action objects with correct `action_type`.
- **Verify:** pytest `test_normaliser.py` (built fully in T20, but a quick assertion now is fine).
- **Reviewer focus:** correct action_type mapping; correlation_id present (everything downstream links on it).

## T05 — Context resolver + fixtures
- **Status:** Done
- **Goal:** Fake "enterprise systems" as fixtures; resolver returns a Context (spec §5.2) for a given Action. Includes CUST-100 (clean), CUST-300 (fraud_flag), recipients (external gmail, known partner), approval states.
- **Depends on:** T04
- **Spec refs:** §5.2, §7
- **Files:** `app/context/fixtures.py`, `app/context/resolver.py`, `tests/T05_context/`
- **Key notes:** Label fixtures clearly as stand-ins for IAM/CRM/fraud/etc. Set `affects_individual_financial_standing` per action (payments → true). Provide a way to force `context_resolution_ok=false` (for the fail-closed demo later).
- **Done when:** each scenario resolves to the Context that will produce its §7 decision (e.g. CUST-300 has `fraud_flag=true`).
- **Verify:** script prints resolved Context per scenario; spot-check fraud_flag and recipient.is_external.
- **Reviewer focus:** fixtures actually drive the intended decisions; nothing real is being called.

## T06 — Presidio sensor (REAL)
- **Status:** Done
- **Goal:** A real `presidio-analyzer` sensor that detects PII/PHI in email bodies and returns entities + spans + scores. Add a custom recognizer for UK NHS number.
- **Depends on:** T02 (+ T01 for the spaCy model in the image)
- **Spec refs:** §5.3 (detected_entities, evidence_spans), §2 (deterministic first)
- **Files:** `app/semantic/presidio_sensor.py`, `tests/T06_presidio/`
- **Key notes:** This is **real**, not stubbed. Map health-related entities (and the NHS-number recognizer) toward `contains_special_category_data` in the next task. Keep it returning raw evidence only — no judgement.
- **Done when:** scenario #4 body yields real entities including the NHS number and health terms, with spans; scenario #6 yields a name/email only.
- **Verify:** script runs the sensor on the three email bodies and prints detected entities + spans.
- **Reviewer focus:** entities are genuinely from Presidio (not hardcoded); spans line up with the text.

## T07 — Nuance stub + evidence builder
- **Status:** Done
- **Goal:** A clearly-labelled stub nuance classifier (deterministic-by-input: planted phrases → fixed confidences 0.88 / 0.62 / low) and an evidence builder that assembles the full Evidence object (spec §5.3) from Presidio + stub.
- **Depends on:** T06
- **Spec refs:** §5.3, §7, §1B (labelling)
- **Files:** `app/semantic/nuance_stub.py`, `app/semantic/evidence_builder.py`, `tests/T07_evidence/`
- **Key notes:** Stub must carry `source:"nuance_stub"` and version `stub-0.1`. Evidence builder sets `contains_special_category_data`, `sensitivity_level`, `overall_confidence`, and `evaluated=true` for email; `evaluated=false` for payments. On any sensor exception set `sensor_error=true`. **No decision field.**
- **Done when:** #4 → special_category=true, conf 0.88; #5 → vulnerability present, conf 0.62; #6 → personal data only, no special category; payments → `evaluated=false`.
- **Verify:** script prints the assembled Evidence for all six scenarios.
- **Reviewer focus:** confidences match §7 exactly; stub is unmistakably labelled; payment path skips semantics.

## T08 — Settings store (runtime-editable)
- **Status:** Done
- **Goal:** A DB-backed settings row holding `high_confidence_threshold` (default 0.75) and per-control mode (shadow/soft/full); read/update helpers.
- **Depends on:** T01
- **Spec refs:** §4 (settings), §6 (threshold), §8 (modes)
- **Files:** `app/settings_store.py`, `tests/T08_settings/`
- **Key notes:** Seed defaults on first run. These values feed OPA input (T10) and the pipeline (T13), and are edited by the Settings UI (T19). Keep it simple — one row.
- **Done when:** can read defaults and update the threshold; value persists across app restart.
- **Verify:** update threshold to 0.60, restart app, confirm it reads 0.60.
- **Reviewer focus:** persistence works; threshold is a single source consumed everywhere (no hard-coded 0.75 elsewhere).

## T09 — OPA round-trip (prove the HTTP path before real policy)
- **Status:** Done
- **Goal:** `controls.json` (control metadata + framework mappings, spec §6); `opa_client.py` that POSTs `{action, context, evidence, config}` to OPA and parses a Decision; a **trivial** Rego policy that returns `allow` for everything, just to prove the round-trip.
- **Depends on:** T02, T08
- **Spec refs:** §6, §5.4, §3
- **Files:** `opa/data/controls.json`, `app/policy/opa_client.py`, `opa/policies/common.rego` (trivial version), `tests/T09_opa_client/`
- **Key notes:** Decide the OPA input contract now and write it down in `opa_client.py` docstring; T10 fills the real logic. On OPA unreachable → return `Decision(decision="fail_closed", failure_mode="fail_closed")`.
- **Done when:** client sends a real request to OPA and gets back a parsed `allow` Decision; killing OPA yields `fail_closed`.
- **Verify:** run client against a live scenario → `allow`; `docker compose stop opa` → `fail_closed`.
- **Reviewer focus:** the input contract is explicit and stable; fail-closed is real (not a try/except that swallows and allows).

## T10 — OPA real policies + precedence (the heart)
- **Status:** Done
- **Goal:** Implement all controls (spec §6) in Rego across `payment.rego`, `email.rego`, `common.rego`, with the precedence resolver (`fail_closed > block > escalate > require_evidence > modify > allow_with_logging > allow`) and the configurable threshold from `config.high_confidence_threshold`. Output the full Decision (§5.4) including `triggered_controls`, `control_id`, `reason`, `required_approval_role`, `framework_mappings`, `threshold_used`.
- **Depends on:** T09
- **Spec refs:** §6 (every control), §5.4, §2 (default-to-human)
- **Files:** `opa/policies/payment.rego`, `opa/policies/email.rego`, `opa/policies/common.rego`, `tests/T10_policy/`
- **Key notes (novice + Rego):** This is the hardest task — expect Claude Code to explain Rego as it goes. Build one control at a time and test each. Remember `block` is **only** the prohibited tier (FIN-PAY-001); everything else escalates. Pull framework_mappings from `controls.json` so policy and metadata stay in sync. FIN-PAY-004 is PROPOSED — implement behind a flag in `controls.json` so it can be toggled off without code changes (see §1B).
- **Done when:** feeding each scenario's Action+Context+Evidence yields exactly the §7 decision and control_id, and the threshold genuinely governs #5.
- **Verify:** run all six through `opa_client` → compare to §7 table; set threshold 0.60 → #5 becomes `allow_with_logging`.
- **Reviewer focus:** precedence is correct (a flagged-fraud + over-£500 case still resolves to `block`); no decision logic leaked into Python; threshold is read from input, not hardcoded.

## T11 — Enforcement handler + approval queue (append-only)
- **Status:** Done
- **Goal:** Apply a Decision under a mode (shadow/soft/full): determine `executed`; route `escalate` to an in-app approval queue with the `required_approval_role`. Approve/Reject **appends** a linked `approval_decision` record (no mutation).
- **Depends on:** T10 (decisions to act on)
- **Spec refs:** §8, §8A item 4, §5.5 (append-only)
- **Files:** `app/enforcement/handler.py`, `app/enforcement/approval_queue.py`, `tests/T11_enforcement/`
- **Key notes:** Shadow = always `executed=true` but record what *would* have happened. The actual record-writing is T12; here, define the interfaces and the executed/queued logic. Approval write-back is an INSERT of a new record (wire to store in T13).
- **Done when:** given each Decision + mode, handler returns correct `executed` and queue state; shadow forces execution with a "would have X" flag.
- **Verify:** unit-style check: block in full → not executed + nothing queued (it's prohibited, not escalated); escalate in full → not executed + queued; block in shadow → executed + "would have blocked".
- **Reviewer focus:** prohibited block does **not** go to the human queue (it's a hard stop); escalations do; shadow logic correct.

## T12 — Audit store + hash chain (tamper-evident)
- **Status:** Done
- **Goal:** SQLAlchemy model + store that writes append-only EvidenceRecords with SHA-256 hash chaining (spec §5.5), plus `verify_chain()` and a `simulate_tampering()` helper that alters a stored row in place (to demo breakage).
- **Depends on:** T02, T01
- **Spec refs:** §5.5, §8A items 5–6
- **Files:** `app/audit/models.py`, `app/audit/store.py`, `tests/T12_audit/`
- **Key notes:** Canonical JSON = sorted keys, no whitespace. Genesis `prev_hash` = 64 zeros. `write_record` computes hash from prior record's hash. `verify_chain` recomputes and returns the first broken index (or "intact"). The store exposes only INSERT for normal writes; `simulate_tampering` is a deliberately separate, clearly-named method used only by the demo.
- **Done when:** writing N records builds a valid chain; `verify_chain` = intact; tampering one row makes `verify_chain` report that exact row.
- **Verify:** pytest `test_audit_chain.py` (built in T20) — but a quick manual run now: write 3, verify intact, tamper row 2, verify reports row 2.
- **Reviewer focus:** hashing is deterministic/canonical; normal write path cannot update rows; tamper helper is isolated and labelled.

## T13 — pipeline.py (INTEGRATION MILESTONE)
- **Status:** Done
- **Goal:** Wire the full loop per spec §11: intercept → normalise → resolve → (semantic if email) → load settings → OPA decide → enforce → write record. Expose a JSON endpoint `POST /run/{scenario_id}` returning the Decision + record hash.
- **Depends on:** T03–T12
- **Spec refs:** §11, §12
- **Files:** `app/pipeline.py`, `app/web/routes.py` (JSON endpoint only for now), `tests/T13_pipeline/`
- **Key notes:** This is where integration risk shows up — budget time. Set `sensor_error`/`context_resolution_ok` failures to drive `fail_closed`. Every run writes a record regardless of decision.
- **Done when:** `POST /run/1..6` returns exactly the §7 decisions and a written, chain-valid record each.
- **Verify:** `curl` each of the six; confirm decisions match §7; hit `verify_chain` → intact. **This is the first time the whole thing runs — celebrate, then continue.**
- **Reviewer focus:** order matches §11; a record is always written; fail-closed paths reachable.

---

# PHASE 3 — Assurance UI (server-rendered; the demo surface)

> All UI tasks use FastAPI + Jinja2 + Tailwind CDN. Read `MASTER_SPEC.md` §8A before each. Tone: calm assurance dashboard, large readable type, every stub/illustrative element labelled. Consult `frontend-design` skill conventions.

## T14 — base.html + control dashboard (landing)
- **Status:** Done
- **Goal:** Shared layout; landing page listing all controls (ID, plain-English purpose, tier, current mode, framework chips, live counts), the enforcement-mode toggle, and the auditable-surface counter (spec §9).
- **Depends on:** T13
- **Spec refs:** §8A item 1, §9, §6
- **Files:** `app/web/templates/base.html`, `dashboard.html`, `app/web/static/` (minimal), routes for `/`, `tests/T14_dashboard/`
- **Done when:** dashboard renders all controls from `controls.json` with live counts pulled from the audit store; mode toggle persists via settings store.
- **Verify:** open `/`; run a scenario; counts and counter update on refresh.
- **Reviewer focus:** this reads like something shown to a board; framework chips match §6; counts are real.

## T15 — Scenario runner + decision view
- **Status:** Done
- **Goal:** Six scenario cards with "Run"; result page showing the decision (colour + plain reason), triggering control + framework chips, resolved context, the **evidence panel** (real Presidio entities with highlighted spans; labelled stub confidence; `threshold_used`), and — if escalated — a prominent "Sent to {role}" state linking to approvals.
- **Depends on:** T14
- **Spec refs:** §8A items 2–3, §7
- **Files:** `app/web/templates/scenarios.html`, `decision.html`, routes, `tests/T15_scenarios_ui/`
- **Done when:** all six produce correct, readable decision views; #4 shows real highlighted spans; payment scenarios show "semantic layer not invoked".
- **Verify:** click through all six; confirm spans render and stub is labelled.
- **Reviewer focus:** evidence panel makes the "model is a sensor, not judge" point visually; nothing stubbed is unlabelled.

## T16 — Approval queue view
- **Status:** Done
- **Goal:** Pending escalations with role, summary, evidence; Approve/Reject with a **required reason**; submitting **appends** an `approval_decision` record and updates `executed`.
- **Depends on:** T15
- **Spec refs:** §8A item 4, §5.5
- **Files:** `app/web/templates/approvals.html`, routes, `tests/T16_approvals_ui/`
- **Done when:** escalating #2 puts an item in the queue for `finance_supervisor`; approving with a reason appends a linked record (original unchanged) and shows it as actioned.
- **Verify:** run #2 → see queue item → approve with reason → check audit log shows two linked records, original intact.
- **Reviewer focus:** original record is **not** mutated; reason is mandatory; correlation/reference linkage correct.

## T17 — Evidence record view + export
- **Status:** Done
- **Goal:** Full single-record view (readable + printable) with `record_hash`, `prev_hash`, approver, reason, execution status; **"Export for audit"** producing JSON + a human-readable file.
- **Depends on:** T14
- **Spec refs:** §8A item 5
- **Files:** `app/web/templates/record.html`, routes (can run parallel to T15/T16), `tests/T17_record_view/`
- **Done when:** any record opens cleanly; export produces a file a non-technical reviewer can read.
- **Verify:** open a record; export; open the exported file.
- **Reviewer focus:** the export is genuinely readable by a risk reviewer, not a raw dump.

## T18 — Audit log + verify chain + simulate tampering (headline moment)
- **Status:** Done
- **Goal:** Chronological record list; **"Verify chain"** (intact + count, or names the broken record); **"Simulate tampering"** alters a row and re-verifies to show breakage and the exact failing record.
- **Depends on:** T12, T14
- **Spec refs:** §8A item 6, §5.5
- **Files:** `app/web/templates/audit.html`, routes, `tests/T18_audit_ui/`
- **Done when:** verify shows intact green; simulate tampering flips it to a clear red failure naming the record; (offer a "reset demo data" affordance).
- **Verify:** verify → intact; simulate tampering → fail names the row.
- **Reviewer focus:** give this room visually — it is the most resonant moment for this buyer; make breakage unmistakable.

## T19 — Settings page (DEMO-READY milestone)
- **Status:** Done
- **Goal:** Editable confidence threshold with a **live impact panel** ("At 0.75, Scenario 5 (0.62) escalates; lower to 0.60 and it would allow-with-logging"); editable per-control mode; changes persist and take effect immediately.
- **Depends on:** T08, T15
- **Spec refs:** §8A item 7, §6
- **Files:** `app/web/templates/settings.html`, routes, `tests/T19_settings_ui/`
- **Done when:** moving the threshold to 0.60 and re-running #5 yields `allow_with_logging` with no restart.
- **Verify:** change threshold live; re-run #5; observe the flip. **Demo is now runnable end-to-end.**
- **Reviewer focus:** demonstrates "risk owns the policy"; impact panel is accurate to the current scenarios.

---

# PHASE 3B — Production Feel (the "this is a real system" layer)

> These tasks transform the demo from "click and see a result" to "watch a control plane operating in real time." They do not add new enforcement logic — they add observability, configurability, and auditability UX that makes the demo feel like a production system. **Scope discipline is critical**: each task has a hard boundary. Do not build a policy studio, a notification system, or a real-time streaming platform. Build exactly what is specified.

## T22 — Live event feed with background traffic (headline demo moment)
- **Status:** Done
- **Goal:** Clicking "Run Scenario N" fires a burst of 8–12 randomised background events through the **real pipeline** (normalise, resolve, evidence, OPA, audit), streamed to the UI via Server-Sent Events, followed by the focal scenario event. The UI shows a live vertical feed of events resolving in real time. Background events appear as compact rows (timestamp, action type, target, decision badge). The focal event appears last with visual emphasis and expands to show the full pipeline trace (stage-by-stage outputs + timing), the evidence panel, triggering control, and framework mappings. The buyer watches routine actions sail through as "allow," then sees the focal event get blocked or escalated — making the enforcement point visceral.
- **Depends on:** T13, T05 (fixture data for background events)
- **Spec refs:** §11, §7, §8A (new section)
- **Files:**
  - `app/scenarios/background_events.py` — pool of 20–25 routine action templates
  - `app/pipeline.py` — modify to return a structured `PipelineTrace` alongside the Decision
  - `app/web/routes.py` — new SSE streaming endpoint `GET /run/{scenario_id}/stream`
  - `app/web/templates/event_feed.html` — live feed UI with EventSource JS
  - `app/web/static/event_feed.js` — JS for sequential event rendering + focal event expansion
  - `tests/T22_event_feed/`
- **Key notes:**
  - **Background event pool** (`background_events.py`): 20–25 routine action templates using existing action types and clean fixture data. Examples: £30 refund to CUST-100, internal email to colleague@postoffice.example, case note update, £120 refund to CUST-200. Each run randomly samples 8–12 from the pool so repeated clicks look different. **Design them to be boring** — they should all resolve to `allow` or `allow_with_logging`. If a background event accidentally triggers an escalation, the demo moment is diluted. They are wallpaper; the focal event is the painting.
  - **Pipeline trace** (`PipelineTrace`): a list of stage results captured during pipeline execution. Each stage entry includes `stage_name`, `timestamp`, `duration_ms`, `inputs_summary` (compact), and `outputs_summary` (compact). Stages: `intercept`, `normalise`, `resolve_context`, `semantic_evidence` (or `semantic_skipped` for payments), `policy_decision`, `enforce`, `audit_write`. Do **not** restructure the pipeline — add trace capture as a lightweight wrapper/collector that records what each stage produced.
  - **SSE endpoint**: FastAPI `StreamingResponse` with `text/event-stream` content type. Each event is a small JSON payload: `{event_index, total_events, is_focal, action_summary, decision, control_id, trace (only on focal)}`. Yield one event per pipeline execution with a small delay (200–400ms) between background events for visual pacing. The focal event yields last with the full trace.
  - **Frontend**: EventSource JS. Each arriving event appends a row to a vertical feed. Background events: compact single-line rows with a green/neutral decision badge. Focal event: arrives last, highlighted with a distinct colour (amber/red per decision), auto-expands to show the pipeline trace as a vertical timeline of stage cards. Each stage card shows what it consumed, what it produced, and elapsed time. For email scenarios, the `semantic_evidence` stage card shows Presidio entities and confidence appearing. For payment scenarios, the card says "Semantic layer not invoked — structured action."
  - **Background events write real audit records.** This populates the audit log with realistic volume, making the hash chain and audit views more impressive. Add a "Reset demo data" button to clear and re-run cleanly (if T18 doesn't already have one).
  - **Do not over-engineer.** No WebSockets. No persistent event bus. No background workers. The SSE endpoint runs the pipeline in a loop synchronously and yields each result. This is a demo, not a production streaming platform.
- **Done when:**
  1. Clicking any scenario shows 8–12 background events streaming in as compact rows with "allow" decisions
  2. The focal event appears last with visual emphasis and the correct §7 decision
  3. Expanding the focal event shows the full pipeline trace with stage-by-stage outputs
  4. Running the same scenario twice shows a different mix of background events
  5. All events (background + focal) write real audit records and the hash chain remains intact
  6. Payment focal events show "semantic layer not invoked" in the trace; email focal events show Presidio entities
- **Verify:** Run scenario #3 (fraud block). Watch 8+ green "allow" rows stream in. See the final row turn red with "BLOCK — FIN-PAY-001". Expand it. Confirm the trace shows all pipeline stages. Switch to audit log — confirm all events are recorded with valid chain. Run again — confirm different background event mix.
- **Reviewer focus:** The focal event must *land* — after a stream of green, the red/amber row must be visually unmistakable. Background events must be genuinely boring (no accidental escalations). SSE must work without page reload. Trace must show real stage outputs, not hardcoded text. Every event writes a real audit record.
- **Estimate:** 2–3 days. SSE plumbing is ~30 lines. Background event pool is the main work — each template needs valid fixture data that passes through the real pipeline.

## T23 — Policy rule editor (extends T19)
- **Status:** Done
- **Goal:** Extend the settings page with a control-level configuration panel. Each control from `controls.json` can be toggled enabled/disabled. Key parameters — specifically the refund escalation threshold (currently £500, FIN-PAY-002) — are editable via the UI. Changes persist and take effect on the next pipeline run with no restart. The buyer sees "risk owns the policy, not engineering" — they can disable a control or change a threshold and immediately observe the decision change.
- **Depends on:** T19, T10
- **Spec refs:** §6, §8A item 7 (extended)
- **Files:**
  - `app/settings_store.py` — extend to store per-control enabled flag + parameterised thresholds
  - `opa/data/controls.json` — add `enabled` field and `parameters` object per control
  - `opa/policies/payment.rego` — add guard clause checking `enabled`; read threshold from `parameters`
  - `opa/policies/email.rego` — add guard clause checking `enabled`
  - `app/web/templates/settings.html` — extend with control toggle + parameter editor section
  - `app/web/routes.py` — extend settings routes
  - `tests/T23_rule_editor/`
- **Key notes:**
  - **Hard scope boundary:** This is a toggle + one or two editable parameters per control. It is NOT a policy authoring tool, NOT a Rego editor, NOT a rule builder. Two controls get editable parameters: FIN-PAY-002 (refund threshold amount) and the confidence threshold (already in T19). All controls get an enabled/disabled toggle.
  - **OPA integration:** The enabled flag and parameters are pushed into the OPA input alongside existing settings (via `config` in the OPA input contract). Rego policies add a guard: `control_enabled("FIN-PAY-002")` early in the rule, so disabled controls never fire. The refund threshold reads from `input.config.parameters["FIN-PAY-002"].amount_threshold` instead of a hardcoded 500.
  - **Settings store:** Extend the existing DB-backed settings to include a JSON column (or separate rows) for per-control config. Seed defaults matching the current hardcoded values on first run.
  - **UI:** Below the existing confidence threshold section, add a "Controls" section. Each control shows: ID, plain-English name, enabled toggle, current mode (from T19), and — where applicable — editable parameters. Use inline editing, not a modal. Show a "change takes effect on next evaluation" confirmation.
  - **Demo moment:** Disable FIN-PAY-002 (refund escalation). Re-run Scenario #2 (£850 refund, clean customer). It now resolves to `allow` instead of `escalate`. Re-enable it — back to `escalate`. Change the threshold from £500 to £1000. Re-run Scenario #2 — it resolves to `allow` (£850 is now under threshold). This is a 30-second demo beat that shows policy is configuration, not code.
- **Done when:**
  1. Each control has an enabled/disabled toggle on the settings page
  2. Disabling FIN-PAY-002 and re-running Scenario #2 yields `allow` instead of `escalate`
  3. Re-enabling FIN-PAY-002 restores the `escalate` decision
  4. Changing the FIN-PAY-002 amount threshold from 500 to 1000 and re-running Scenario #2 yields `allow`
  5. Restoring the threshold to 500 restores `escalate`
  6. All changes persist across page refresh (DB-backed)
  7. No restart required
- **Verify:** Toggle FIN-PAY-002 off → run #2 → allow. Toggle on → run #2 → escalate. Set threshold to 1000 → run #2 → allow. Set to 500 → run #2 → escalate. Restart app → confirm settings persisted.
- **Reviewer focus:** Rego must read the threshold from input, not hardcode it. Disabled controls must be genuinely skipped in OPA (not filtered in Python after the fact — that would undermine the "policy engine decides" principle). Parameter changes must not require any file edit or restart.
- **Estimate:** 1–1.5 days. The Rego changes are small. The settings store extension is moderate. The UI is a section addition to an existing page.

## T24 — Escalation dashboard polish (extends T16)
- **Status:** Done
- **Goal:** Enhance the approval queue to feel like an operational dashboard rather than a basic list. Add a pending-count badge in the nav bar (visible from any page), timestamps and triggering scenario context on each queue item, a role filter ("show only items for `finance_supervisor`"), and a link from each queue item to the pipeline trace that caused the escalation (linking to T22's trace view for the focal event).
- **Depends on:** T16, T22 (for trace linkage)
- **Spec refs:** §8A item 4 (extended)
- **Files:**
  - `app/web/templates/base.html` — add pending-count badge to nav
  - `app/web/templates/approvals.html` — extend with timestamps, context summary, role filter, trace link
  - `app/web/routes.py` — extend approval routes (pending count endpoint for nav, role filter param)
  - `tests/T24_escalation_polish/`
- **Key notes:**
  - **Pending badge:** A count of pending (un-actioned) escalations, shown next to the "Approvals" nav link on every page. Fetched from the audit store (count of `escalate` records with no linked `approval_decision`). Can be a simple server-rendered count on page load — no need for live updates.
  - **Queue item enrichment:** Each item shows: timestamp of the escalation, the action type and target (e.g. "£850 refund to CUST-100"), the triggering control ID and reason, the required approval role, and a "View trace" link that opens the pipeline trace from T22 (link by `correlation_id`).
  - **Role filter:** A simple dropdown or tab bar: "All", "finance_supervisor", "data_protection_officer". Filters the queue server-side.
  - **This is polish, not new architecture.** Do not add notifications, email alerts, SLA timers, or assignment logic. The existing approve/reject with mandatory reason workflow is unchanged.
- **Done when:**
  1. Nav bar shows a pending escalation count badge on all pages
  2. Queue items show timestamp, action summary, triggering control, and required role
  3. Role filter works (selecting "finance_supervisor" hides DPO escalations)
  4. "View trace" link on each item opens the relevant pipeline trace from T22
  5. Approve/reject workflow is unchanged and still works correctly
- **Verify:** Run scenario #2 (escalate). See badge appear in nav. Open approvals. Confirm enriched item. Filter by role. Click "View trace" — confirm it shows the pipeline trace for that evaluation. Approve with reason — badge count decrements.
- **Reviewer focus:** Badge count is accurate and updates on page navigation. Trace linkage uses `correlation_id` correctly. The existing append-only approval workflow is not broken by the additions.
- **Estimate:** 0.5–1 day. This is template and route work on existing infrastructure.

## T25 — Audit security demonstration (extends T17/T18)
- **Status:** Done
- **Goal:** Make the audit security story visually explicit for a non-technical reviewer. Two additions: (1) a visual hash chain view in the audit log showing each record's hash and its link to the previous record's hash, making the chain structure obvious; (2) an enhanced "Export audit package" function that bundles all records for a given `correlation_id` (or a date range) into a single JSON file with a package-level integrity hash, so the buyer can see that evidence can be extracted for external review in a tamper-evident format.
- **Depends on:** T17, T18
- **Spec refs:** §5.5, §8A items 5–6 (extended)
- **Files:**
  - `app/web/templates/audit.html` — extend with visual chain view (hash links between records)
  - `app/web/templates/record.html` — extend export to include chain hashes
  - `app/audit/store.py` — add `export_audit_package()` method (JSON bundle + integrity hash)
  - `app/web/routes.py` — extend export route
  - `tests/T25_audit_security/`
- **Key notes:**
  - **Visual chain:** In the audit log list, each record shows a truncated `record_hash` and `prev_hash`, with a visual connector (line or arrow) linking each record's `prev_hash` to the previous record's `record_hash`. This makes hash chaining tangible to someone who has never seen it. When the chain is intact, connectors are green. After "Simulate tampering," the broken link turns red with the mismatched hashes shown side by side.
  - **Audit package export:** A "Download audit package" button (on the audit page or filtered by correlation_id) produces a JSON file containing: all records in the selection, the full hash chain for those records, and a `package_integrity_hash` computed over the entire bundle. The file includes a human-readable header explaining what the hashes mean and how to verify. This is not a digital signature (no PKI in the demo) — it is a self-contained integrity check.
  - **Do not build:** PKI/signing infrastructure, external verification service, WORM storage integration, or any real cryptographic attestation beyond SHA-256 hashing. Label the package as "demo integrity check — production would use signed attestation."
- **Done when:**
  1. Audit log shows visual hash chain links between records
  2. Chain links are green when intact, red at the break point after simulated tampering
  3. "Download audit package" produces a JSON file with records + package integrity hash
  4. The package file includes a human-readable explanation of the integrity model
  5. The package is labelled as a demo (not production-grade signing)
- **Verify:** Run several scenarios. Open audit log. Confirm visual chain links are visible and green. Click "Download audit package" — open the file, confirm records and integrity hash are present. Simulate tampering — confirm the broken chain link turns red with mismatched hashes displayed. Download package again — confirm the integrity hash has changed.
- **Reviewer focus:** The visual chain must be immediately comprehensible to a non-technical reviewer — no cryptography jargon on the page. The broken-link visualisation after tampering should be the "aha" moment. The export package must be honest about being a demo-grade integrity check.
- **Estimate:** 0.5–1 day. Mostly template work plus a small export function.

---

# PHASE 5 — Evidence & Assurance Enhancements

This phase exists for one reason: a Head of Risk and Assurance does not just want to see that the gate makes decisions — they want to see that, without it, they would not know what evidence to capture or whether it would satisfy a regulator, and that this build answers both. T26–T29 are presentational/content work over fields the pipeline already produces in T02/T07/T10/T12. Only T29 adds a schema field; everything else maps existing data, it does not compute anything new.

## T26 — "If a regulator asked..." evidence mapping
- **Status:** Done
- **Goal:** On the decision page (post-scenario-run) and the record view, add a panel that lists the specific questions a regulator or internal auditor would ask about an AI-agent action, and shows, field by field, which part of the existing record answers each one. This is the single most direct way to make the "we already know what to log and it's sufficient" argument land — without it, the buyer has to infer sufficiency themselves from scattered fields.
- **Depends on:** T17, T19
- **Spec refs:** §5 (Action/Context/Evidence/Decision/EvidenceRecord field set), §7 (scenario table), §9 (assurance narrative)
- **Files:**
  - `app/web/templates/_regulator_questions.html` — new shared partial, included from both `decision.html` and `record.html`
  - `app/web/templates/decision.html` — include partial
  - `app/web/templates/record.html` — include partial
  - `app/web/routes.py` — build the question→field mapping context for both routes
  - `app/web/regulator_questions.py` — new small module: a pure function that takes an `Action`/`Decision`/`EvidenceRecord` (or the existing record) and returns an ordered list of `{question, answer_field_label, answer_value}` rows
  - `tests/T26_regulator_questions/`
- **Key notes:**
  - **No new computation.** Every "answer" is a value already present on the record: `executed`, `enforcement_mode`, `control_id`, `decision.reason`, `framework_mappings`, `context_used.*`, `evidence.*`, `required_approval_role`, `record_hash`/`prev_hash`, and for `approval_decision` records, `human_approver`/`approval_reason`. This task only decides which question each field answers and renders it as a pair.
  - **Question set should cover at minimum:** (1) Was the action intercepted before execution? (2) What policy/control was applied, and what does it map to? (3) What evidence and context informed the decision? (4) Who or what made the decision — model or policy engine? (5) Was a human involved where judgement was required, and is that decision itself evidenced? (6) Can this record be shown to have not been altered after the fact?
  - **Vary by record shape.** A `fail_closed` record should show "the policy engine was unreachable; the system defaulted to stop" against question 4, not a blank. A payment record should show "semantic layer not invoked — not needed for this action type" against question 3, consistent with the existing `evidence.evaluated=false` framing already in `record.html`/`decision.html`.
  - **Do not duplicate the existing "Evidence" and "Binding decision" sections** — this panel sits alongside them as an explicit index into them, framed as regulator questions, not as a third copy of the same data.
- **Done when:**
  1. Decision page and record page both show a "If a regulator asked..." panel with at least 6 questions
  2. Each question's answer cites an existing record field — no hardcoded or invented answers
  3. The panel correctly reflects `fail_closed`, `escalate`, `block`, `allow`, and `allow_with_logging` outcomes, and both `action_evaluation` and `approval_decision` record types
  4. Panel content differs sensibly between payment and email scenarios (semantic question answered differently)
- **Verify:** Run each of the six scenarios plus one approval and one fail-closed simulation. Open the decision page and the record view for each. Confirm the regulator-questions panel renders sensible, field-backed answers for every case, including the two edge cases (fail_closed, approval_decision).
- **Reviewer focus:** that the mapping module is the only place questions are defined (single source of truth, not duplicated string literals in templates); that no answer is fabricated or summarised away from what the record actually contains.
- **Estimate:** 0.5–1 day. Mostly a mapping module plus a template partial reused twice.

## T27 — "Evidence gap" contrast page + demo Beat 0
- **Status:** To do
- **Goal:** Add a short static page that states, plainly, what the evidence picture looks like for an AI-agent deployment **without** a deterministic policy/enforcement layer (unstructured logs, no pre-execution capture, no standardised decision field, no context-at-decision-time capture, no tamper-evident chain of custody, no framework traceability) — set directly against what this build produces for the same action, with a link into a live scenario run. This is the contrast that makes the rest of the demo land; right now the demo shows the "with this" side well but never states the "without this" side out loud.
- **Depends on:** T19
- **Spec refs:** §1, §1A, §9
- **Files:**
  - `app/web/templates/evidence_gap.html` — new page
  - `app/web/routes.py` — new `GET /evidence-gap` route
  - `app/web/templates/base.html` — add nav link
  - `DEMO_SCRIPT.md` — new **Beat 0** before the existing Beat 1, renumber narration references if needed
  - `tests/T27_evidence_gap/`
- **Key notes:**
  - **Two-column or before/after layout.** Left: "Without a policy enforcement layer" — five or six short, concrete pain points (e.g. "you only know what happened after it happened," "what counts as a 'decision' is implicit, not a field," "reconstructing context after the fact means querying five systems and hoping nothing's changed"). Right: "With AI PEL" — the corresponding capability, each one linking to a concrete field name or page already in the app (e.g. links to `/scenarios`, an example `/records/{hash}`).
  - **Tone:** matter-of-fact, not salesy. This is a risk audience; overclaiming undermines credibility built up by the existing "what's real vs stubbed" honesty section. Keep claims scoped to what the demo actually shows.
  - **Demo script:** Beat 0 narration, roughly: "Before we look at the system, it's worth being explicit about the problem it solves. [Walk the contrast page.] Now let's see what evidence actually looks like when it's structural rather than reconstructed." Keep this beat to under a minute — it's framing, not the main event.
- **Done when:**
  1. `/evidence-gap` renders the without/with contrast with at least 5 paired points
  2. Nav link present from any page
  3. At least one "with AI PEL" point links to a live, working page in the app
  4. `DEMO_SCRIPT.md` has a new Beat 0 ahead of the existing dashboard-calm beat, and subsequent beat numbers/cross-references are still consistent
- **Verify:** Open `/evidence-gap` cold. Click through to the linked live page and confirm it's a real, populated view (not a dead link). Read the updated demo script start-to-finish and confirm beat numbering is consistent throughout.
- **Reviewer focus:** the page must not assert anything the rest of the demo can't immediately back up; it should read as a one-minute framing device, not a sales slide. No invented statistics.
- **Estimate:** 0.5 day. Static content plus one route.

## T28 — Evidence sufficiency checklist (record view)
- **Status:** To do
- **Goal:** On the record view, add a checklist that evaluates the record's own fields against a small, clearly-labelled set of illustrative sufficiency criteria (e.g. "pre-execution interception evidenced," "decision rationale recorded," "framework mapping present," "tamper-evident chain position recorded," "human oversight evidenced where required") and renders each as met/not-applicable/missing. This turns "is this enough evidence?" from a question the buyer has to answer themselves into something the record visibly answers.
- **Depends on:** T17, T26
- **Spec refs:** §5, §9 (illustrative-mapping disclaimer pattern already established for `framework_mappings`)
- **Files:**
  - `app/audit/sufficiency.py` — new pure function: `EvidenceRecord -> list[SufficiencyItem]`, no persistence, no new schema fields
  - `app/web/templates/record.html` — extend with checklist section
  - `app/web/routes.py` — wire the checklist into the record route's context
  - `tests/T28_evidence_sufficiency/`
- **Key notes:**
  - **Hard scope boundary:** this is a demo-illustrative checklist against criteria you define, not a certification engine and not a claim of regulatory compliance. Label it exactly as clearly as the existing `framework_mappings` disclaimer ("(illustrative mapping)") — e.g. "Illustrative sufficiency check, not a compliance certification."
  - **Criteria must be derivable from fields that already exist** on `EvidenceRecord` (no new schema needed for this task — that's reserved for T29's single new field). Example mapping: interception evidenced → `executed` + `enforcement_mode` both present; decision rationale recorded → `decision.reason` non-empty; framework mapping present → `framework_mappings` non-empty; chain position recorded → `record_hash` + `prev_hash` present; human oversight evidenced where required → for `escalate` decisions, a linked `approval_decision` record exists (or is clearly flagged as pending).
  - **Handle record types correctly:** an `allow` record with no triggered control should show "human oversight" as not-applicable, not missing — don't penalise records for not needing something the scenario didn't require.
- **Done when:**
  1. Record view shows a sufficiency checklist of at least 5 items for every record type produced by the six scenarios, approvals, and fail-closed runs
  2. Each item is correctly met / not-applicable / missing based on real field values, never hardcoded per scenario
  3. The checklist carries an explicit "illustrative, not a certification" label
  4. An `escalate` record with no linked approval yet correctly shows the human-oversight item as pending/missing; once approved, re-viewing shows it as met
- **Verify:** Run all six scenarios, view each record, confirm checklist renders sensibly. Run Scenario 2, view its record before approving (oversight item should show pending), approve it, view the record again (should now show met).
- **Reviewer focus:** the checklist function must read only from the record's own fields — no scenario-number special-casing inside `sufficiency.py`. The illustrative/non-certification framing must be unmissable.
- **Estimate:** 0.5–1 day.

## T29 — Evidence schema versioning + regulatory export framing
- **Status:** To do
- **Goal:** Add a single `evidence_schema_version` field to `EvidenceRecord`, populated on every write, surfaced on the record view and in audit exports — so the buyer sees that the *definition* of sufficient evidence is itself versioned and governed, not informal. Pair this with narration-only updates to the existing audit package export (T25) and `DEMO_SCRIPT.md` Beat 9, reframing the already-built "Download audit package" feature explicitly as a regulatory-reporting artefact, with no functional change to the export itself.
- **Depends on:** T02, T25
- **Spec refs:** §5 (schema) — **note Golden rule 6: this is a schema change, so `MASTER_SPEC.md` §5 must be updated first**, with a version bump noted at the top of the spec, before implementation.
- **Files:**
  - `MASTER_SPEC.md` — update §5 `EvidenceRecord` definition first; bump spec version
  - `app/schemas/audit.py` — add `evidence_schema_version: str` field
  - `app/audit/store.py` — set the version constant when writing every record
  - `app/web/templates/record.html` — display the field
  - `app/web/templates/audit.html` — include it in the audit log table or package export description
  - `DEMO_SCRIPT.md` — update Beat 9 narration only (no behaviour change to the export itself)
  - `tests/T29_evidence_schema_version/`
- **Key notes:**
  - **Spec-first, per the golden rules.** Do not touch `app/schemas/audit.py` until `MASTER_SPEC.md` §5 reflects the new field.
  - **Keep it simple.** A single module-level constant (e.g. `EVIDENCE_SCHEMA_VERSION = "1.0.0"`) is sufficient for the demo; no migration tooling is needed since the demo's Postgres data is ephemeral and reset between runs. State this plainly in code comments rather than building anything more elaborate.
  - **Beat 9 reframing example:** "This package isn't just a log export — every record in it carries an evidence schema version, so you can show a regulator not only what was captured, but that the definition of 'captured' was itself controlled and hasn't silently drifted between the start and end of the reporting period."
- **Done when:**
  1. Every newly written record (both `action_evaluation` and `approval_decision`) carries `evidence_schema_version`
  2. The field is visible on the record view and included in both JSON and printable HTML exports
  3. `MASTER_SPEC.md` §5 documents the field and the spec version is bumped
  4. `DEMO_SCRIPT.md` Beat 9 narration mentions schema versioning; the underlying export mechanism is otherwise unchanged from T25
- **Verify:** Run a scenario, view the record, confirm the version field is present. Export JSON and printable HTML, confirm it's included in both. Diff `MASTER_SPEC.md` to confirm the schema update predates the code change in commit order.
- **Reviewer focus:** schema-first discipline (golden rule 6) was actually followed; no other field semantics were disturbed by this change; the export's existing tamper-evidence behaviour from T25 is untouched.
- **Estimate:** 0.5 day.

## T30 — Reporting dashboard summary view (backlog, not scheduled)
- **Status:** Backlog
- **Goal:** A separate aggregate view, distinct from the per-record evidence shown in T26–T29, that rolls records up into the kind of period summary a Head of Risk would actually present upward or to a regulator: total actions evaluated, breakdown by decision and control, count of escalations with linked human decisions vs pending, and a chain-integrity verification timestamp for the period. This moves the demo from "look at one record" to "look at your reporting posture" — but it's a materially bigger piece of work than T26–T29 and isn't needed for the current demo script.
- **Depends on:** T28, T29 (consumes their output)
- **Spec refs:** none yet — would need a short spec addendum before scheduling
- **Files:** not yet scoped
- **Key notes:** Deliberately left unscoped. Do not start without first writing a short spec addendum (per golden rule 6) and confirming it's worth the build time relative to T26–T29's lower-effort, higher-leverage additions.
- **Estimate:** not estimated — scope first.

---

# PHASE 4 — Verify & present

## T20 — Test suite
- **Status:** To do
- **Goal:** The four core test files (spec §10): normaliser mapping; Presidio detection on the planted bodies; **policy decisions per scenario** (each of the six → expected §7 decision); audit chain integrity + tamper detection. Plus two additional test files covering Phase 3B: background event safety (all background events resolve to `allow` or `allow_with_logging`, never escalate/block); control toggle and parameter override (disabling a control or changing a parameter changes the OPA decision).
- **Depends on:** T13, T22, T23
- **Spec refs:** §10, §12, §7
- **Files:** `tests/test_normaliser.py`, `test_presidio_sensor.py`, `test_policy_decisions.py`, `test_audit_chain.py`, `test_background_events.py`, `test_rule_editor.py`
- **Done when:** `pytest` is green; `test_policy_decisions` is the regression guard that the demo can never silently drift from §7; `test_background_events` confirms no accidental escalations in the background pool; `test_rule_editor` confirms control toggle and parameter override affect OPA decisions.
- **Verify:** `docker compose run --rm app pytest -q`.
- **Reviewer focus:** the policy-decision test asserts the full §7 table; chain test asserts tamper detection; background event test guarantees no surprise escalations; rule editor test confirms Rego reads parameters from input.

## T21 — README + demo script (narration)
- **Status:** To do
- **Goal:** README: what it is, how to run (`docker compose up`), the architecture in a paragraph, and the explicit list of what's real vs stubbed (spec §1). Plus a **demo script** — the spoken narration written for the Head-of-Assurance audience, honouring §1B (no Horizon as a hook).
- **Depends on:** T19, T22, T23, T24, T25
- **Spec refs:** §1, §1A, §1B, §7, §9
- **Files:** `README.md` (final), `DEMO_SCRIPT.md`
- **Key notes:**
  - **Demo script must include the following beats in this order:**
    1. **Dashboard calm.** Open landing page. Show aggregate stats (total evaluations, % allowed/escalated/blocked, breakdown by action type). Show controls listed, modes, framework chips. "This is what your AI operations look like when the control plane is running." *(Requires: summary stats cards on the dashboard — a few SQL count queries rendered at the top of `dashboard.html`. This is minor template work; implement as part of T21 if not already present.)*
    2. **Live feed — routine.** Run a low-risk scenario (#1 or #6) via the event feed. Watch 8–12 background events stream through, all green. "These are AI agents operating within policy. Every action evaluated, every decision recorded."
    3. **Live feed — enforcement.** Run #3 (fraud block). Stream of green, then the red row lands. Expand the pipeline trace. Walk through each stage. "This agent tried to issue a refund to a flagged customer. The system caught it in 200 milliseconds."
    4. **Human oversight.** Run #2 (escalation). Show the amber row. Show it appear in the approval queue (badge increments). Walk through the enriched queue item. Approve with reason. "This refund was legitimate but high-value. The system didn't block it — it routed it to the right human."
    5. **Semantic evidence.** Run #4 (email with health data). Show the evidence panel — Presidio entities, highlighted spans, confidence score. "The semantic layer detected NHS numbers and health information. It didn't make the decision — it provided evidence. The policy engine decided."
    6. **Shadow mode.** Switch all controls to shadow mode on the settings page. Re-run #3 (fraud). It executes — but the record says "would have blocked, FIN-PAY-001." Switch back to full enforcement. Re-run. It blocks. "No enterprise deploys enforcement on day one. Shadow mode lets you observe before you enforce." *(Requires: the decision view must clearly render shadow-mode state — "Executed (shadow) — would have blocked." Confirm T15's decision view handles this; add a shadow-mode callout if not.)*
    7. **Policy control.** On settings, disable FIN-PAY-002. Re-run #2. It allows. Re-enable. Change threshold from £500 to £1000. Re-run #2. It allows. Restore. "Your risk team owns these policies. No code change. No deployment."
    8. **Confidence threshold.** Change the semantic threshold from 0.75 to 0.60. Re-run #5. It flips from escalate to allow-with-logging. "You decide the confidence level at which the system defers to a human."
    9. **Audit integrity.** Open audit log. Show the visual hash chain — green links. "Every decision is hash-chained. If anyone alters a record, the chain breaks." Simulate tampering. Red link, mismatched hashes. "It tells you exactly where." Download audit package. "Evidence can be extracted for external review."
    10. **Fail closed.** Simulate component failure (force one OPA call to fail). The event feed shows an action arrive, policy decision stage shows "policy engine unreachable," decision is `fail_closed`. Next event runs normally. "If anything in the system fails, the default is stop. Never allow." *(Requires: a "Simulate policy engine failure" button on the event feed or settings page that sets a one-shot flag causing the next `opa_client` call to raise a connection error instead of calling OPA. This is ~10 lines of code: a flag in the settings store, a check in `opa_client.py`, a button in the UI, and the flag auto-resets after one use.)*
  - **Demo script pacing:** The full sequence should take 12–15 minutes. Each beat answers a different buyer question. The order is: calm → routine → enforcement → human oversight → semantic evidence → shadow mode → policy control → threshold → audit → fail-safe.
  - **Three minor code additions may be needed to support the script** (noted with *(Requires:...)*  above). These are each under 30 minutes of work and should be implemented during T21, not as separate tasks:
    1. Aggregate stats cards on the dashboard (SQL counts + template section)
    2. Shadow-mode callout in the decision view (if not already rendering clearly)
    3. One-shot OPA failure simulation (flag + button + auto-reset)
- **Done when:** a stranger can `docker compose up` and run the demo from the script alone; the narration covers all ten beats in the specified order; all three minor code additions work; the "what's real vs stubbed" honesty list is present in the README; tone is right for the room.
- **Verify:** follow your own README on a clean checkout; run the demo from the script, hitting every beat. Confirm shadow mode renders clearly. Confirm fail-closed simulation works and auto-resets. Confirm aggregate stats update after running scenarios.
- **Reviewer focus:** the demo script must not read like a feature walkthrough — it must read like a story about operational assurance. Each beat should answer an implicit buyer question ("does it work?", "does it catch things?", "what if I need a human?", "can I observe first?", "who controls the policy?", "can I trust the evidence?", "what if something fails?"). The three minor code additions must not break existing behaviour. The "what's real vs stubbed" honesty list is present and accurate.

---

## Parallelisation notes
- T17 can run alongside T15/T16.
- **T22, T23, and T25 can run in parallel** (no dependencies on each other).
- **T24 depends on T22** (for pipeline trace linkage).
- T20 depends on T22 and T23 (test suite must cover new behaviour).
- T21 depends on all Phase 3B tasks (demo script must narrate new features).
- **T26 depends on T17/T19** and can run independently of T20/T21.
- **T27 depends only on T19** and can run in parallel with T26.
- **T28 depends on T17 and T26** (reuses the question-mapping module's framing conventions).
- **T29 depends on T02 and T25**, and should run after T26–T28 land so its narration update to Beat 9 doesn't conflict with T27's Beat 0 insertion in `DEMO_SCRIPT.md`.
- T30 is backlog — not scheduled, needs its own spec addendum first.
- Everything else is linear by dependency.

---

## Effort estimates (Phase 3B + Phase 4 + Phase 5)

| Task | Effort | Notes |
|------|--------|-------|
| T22 — Live event feed | 2–3 days | SSE plumbing simple; background event pool is the work |
| T23 — Policy rule editor | 1–1.5 days | Rego changes small; settings store moderate |
| T24 — Escalation polish | 0.5–1 day | Template + route work on existing infra |
| T25 — Audit security | 0.5–1 day | Template work + small export function |
| T20 — Test suite | 1–1.5 days | Extended to cover T22/T23 |
| T21 — README + demo script | 1–1.5 days | Includes three minor code additions + full narration |
| T26 — Regulator's-question mapping | 0.5–1 day | One mapping module + one reused template partial |
| T27 — Evidence gap contrast page | 0.5 day | Static content + one route |
| T28 — Evidence sufficiency checklist | 0.5–1 day | Pure function over existing fields + template section |
| T29 — Schema version + export framing | 0.5 day | Spec update first, then a one-field schema change |
| T30 — Reporting dashboard (backlog) | not estimated | Needs its own spec addendum before scheduling |
| **Total (scheduled, excl. T30)** | **~9–12 days** | Discipline required — do not let T22, T23, or Phase 5 expand scope |
