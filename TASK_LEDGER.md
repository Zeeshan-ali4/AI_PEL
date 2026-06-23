# Task Ledger — Runtime Policy Enforcement Gate (Demo Build)

**Companion to:** `MASTER_SPEC.md` v1.1 (the source of truth). This ledger is the *build order*. It does not restate the spec; it points into it.

## Current build state

- Current task: T09
- Last completed task: T08
- Known blockers: none

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
Phase 4  Verify & present    T20 → T21
```

Integration milestone is **T13** (all six scenarios pass end-to-end via a JSON endpoint, before any UI). Demo-ready is **T19**. Tasks within a phase are mostly linear; where two can run in parallel it is noted.

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
- **Status:** IN_PROGRESS
- **Goal:** `controls.json` (control metadata + framework mappings, spec §6); `opa_client.py` that POSTs `{action, context, evidence, config}` to OPA and parses a Decision; a **trivial** Rego policy that returns `allow` for everything, just to prove the round-trip.
- **Depends on:** T02, T08
- **Spec refs:** §6, §5.4, §3
- **Files:** `opa/data/controls.json`, `app/policy/opa_client.py`, `opa/policies/common.rego` (trivial version), `tests/T09_opa_client/`
- **Key notes:** Decide the OPA input contract now and write it down in `opa_client.py` docstring; T10 fills the real logic. On OPA unreachable → return `Decision(decision="fail_closed", failure_mode="fail_closed")`.
- **Done when:** client sends a real request to OPA and gets back a parsed `allow` Decision; killing OPA yields `fail_closed`.
- **Verify:** run client against a live scenario → `allow`; `docker compose stop opa` → `fail_closed`.
- **Reviewer focus:** the input contract is explicit and stable; fail-closed is real (not a try/except that swallows and allows).

## T10 — OPA real policies + precedence (the heart)
- **Goal:** Implement all controls (spec §6) in Rego across `payment.rego`, `email.rego`, `common.rego`, with the precedence resolver (`fail_closed > block > escalate > require_evidence > modify > allow_with_logging > allow`) and the configurable threshold from `config.high_confidence_threshold`. Output the full Decision (§5.4) including `triggered_controls`, `control_id`, `reason`, `required_approval_role`, `framework_mappings`, `threshold_used`.
- **Depends on:** T09
- **Spec refs:** §6 (every control), §5.4, §2 (default-to-human)
- **Files:** `opa/policies/payment.rego`, `opa/policies/email.rego`, `opa/policies/common.rego`, `tests/T10_policy/`
- **Key notes (novice + Rego):** This is the hardest task — expect Claude Code to explain Rego as it goes. Build one control at a time and test each. Remember `block` is **only** the prohibited tier (FIN-PAY-001); everything else escalates. Pull framework_mappings from `controls.json` so policy and metadata stay in sync. FIN-PAY-004 is PROPOSED — implement behind a flag in `controls.json` so it can be toggled off without code changes (see §1B).
- **Done when:** feeding each scenario's Action+Context+Evidence yields exactly the §7 decision and control_id, and the threshold genuinely governs #5.
- **Verify:** run all six through `opa_client` → compare to §7 table; set threshold 0.60 → #5 becomes `allow_with_logging`.
- **Reviewer focus:** precedence is correct (a flagged-fraud + over-£500 case still resolves to `block`); no decision logic leaked into Python; threshold is read from input, not hardcoded.

## T11 — Enforcement handler + approval queue (append-only)
- **Goal:** Apply a Decision under a mode (shadow/soft/full): determine `executed`; route `escalate` to an in-app approval queue with the `required_approval_role`. Approve/Reject **appends** a linked `approval_decision` record (no mutation).
- **Depends on:** T10 (decisions to act on)
- **Spec refs:** §8, §8A item 4, §5.5 (append-only)
- **Files:** `app/enforcement/handler.py`, `app/enforcement/approval_queue.py`, `tests/T11_enforcement/`
- **Key notes:** Shadow = always `executed=true` but record what *would* have happened. The actual record-writing is T12; here, define the interfaces and the executed/queued logic. Approval write-back is an INSERT of a new record (wire to store in T13).
- **Done when:** given each Decision + mode, handler returns correct `executed` and queue state; shadow forces execution with a "would have X" flag.
- **Verify:** unit-style check: block in full → not executed + nothing queued (it's prohibited, not escalated); escalate in full → not executed + queued; block in shadow → executed + "would have blocked".
- **Reviewer focus:** prohibited block does **not** go to the human queue (it's a hard stop); escalations do; shadow logic correct.

## T12 — Audit store + hash chain (tamper-evident)
- **Goal:** SQLAlchemy model + store that writes append-only EvidenceRecords with SHA-256 hash chaining (spec §5.5), plus `verify_chain()` and a `simulate_tampering()` helper that alters a stored row in place (to demo breakage).
- **Depends on:** T02, T01
- **Spec refs:** §5.5, §8A items 5–6
- **Files:** `app/audit/models.py`, `app/audit/store.py`, `tests/T12_audit/`
- **Key notes:** Canonical JSON = sorted keys, no whitespace. Genesis `prev_hash` = 64 zeros. `write_record` computes hash from prior record's hash. `verify_chain` recomputes and returns the first broken index (or "intact"). The store exposes only INSERT for normal writes; `simulate_tampering` is a deliberately separate, clearly-named method used only by the demo.
- **Done when:** writing N records builds a valid chain; `verify_chain` = intact; tampering one row makes `verify_chain` report that exact row.
- **Verify:** pytest `test_audit_chain.py` (built in T20) — but a quick manual run now: write 3, verify intact, tamper row 2, verify reports row 2.
- **Reviewer focus:** hashing is deterministic/canonical; normal write path cannot update rows; tamper helper is isolated and labelled.

## T13 — pipeline.py (INTEGRATION MILESTONE)
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
- **Goal:** Shared layout; landing page listing all controls (ID, plain-English purpose, tier, current mode, framework chips, live counts), the enforcement-mode toggle, and the auditable-surface counter (spec §9).
- **Depends on:** T13
- **Spec refs:** §8A item 1, §9, §6
- **Files:** `app/web/templates/base.html`, `dashboard.html`, `app/web/static/` (minimal), routes for `/`, `tests/T14_dashboard/`
- **Done when:** dashboard renders all controls from `controls.json` with live counts pulled from the audit store; mode toggle persists via settings store.
- **Verify:** open `/`; run a scenario; counts and counter update on refresh.
- **Reviewer focus:** this reads like something shown to a board; framework chips match §6; counts are real.

## T15 — Scenario runner + decision view
- **Goal:** Six scenario cards with "Run"; result page showing the decision (colour + plain reason), triggering control + framework chips, resolved context, the **evidence panel** (real Presidio entities with highlighted spans; labelled stub confidence; `threshold_used`), and — if escalated — a prominent "Sent to {role}" state linking to approvals.
- **Depends on:** T14
- **Spec refs:** §8A items 2–3, §7
- **Files:** `app/web/templates/scenarios.html`, `decision.html`, routes, `tests/T15_scenarios_ui/`
- **Done when:** all six produce correct, readable decision views; #4 shows real highlighted spans; payment scenarios show "semantic layer not invoked".
- **Verify:** click through all six; confirm spans render and stub is labelled.
- **Reviewer focus:** evidence panel makes the "model is a sensor, not judge" point visually; nothing stubbed is unlabelled.

## T16 — Approval queue view
- **Goal:** Pending escalations with role, summary, evidence; Approve/Reject with a **required reason**; submitting **appends** an `approval_decision` record and updates `executed`.
- **Depends on:** T15
- **Spec refs:** §8A item 4, §5.5
- **Files:** `app/web/templates/approvals.html`, routes, `tests/T16_approvals_ui/`
- **Done when:** escalating #2 puts an item in the queue for `finance_supervisor`; approving with a reason appends a linked record (original unchanged) and shows it as actioned.
- **Verify:** run #2 → see queue item → approve with reason → check audit log shows two linked records, original intact.
- **Reviewer focus:** original record is **not** mutated; reason is mandatory; correlation/reference linkage correct.

## T17 — Evidence record view + export
- **Goal:** Full single-record view (readable + printable) with `record_hash`, `prev_hash`, approver, reason, execution status; **"Export for audit"** producing JSON + a human-readable file.
- **Depends on:** T14
- **Spec refs:** §8A item 5
- **Files:** `app/web/templates/record.html`, routes (can run parallel to T15/T16), `tests/T17_record_view/`
- **Done when:** any record opens cleanly; export produces a file a non-technical reviewer can read.
- **Verify:** open a record; export; open the exported file.
- **Reviewer focus:** the export is genuinely readable by a risk reviewer, not a raw dump.

## T18 — Audit log + verify chain + simulate tampering (headline moment)
- **Goal:** Chronological record list; **"Verify chain"** (intact + count, or names the broken record); **"Simulate tampering"** alters a row and re-verifies to show breakage and the exact failing record.
- **Depends on:** T12, T14
- **Spec refs:** §8A item 6, §5.5
- **Files:** `app/web/templates/audit.html`, routes, `tests/T18_audit_ui/`
- **Done when:** verify shows intact green; simulate tampering flips it to a clear red failure naming the record; (offer a "reset demo data" affordance).
- **Verify:** verify → intact; simulate tampering → fail names the row.
- **Reviewer focus:** give this room visually — it is the most resonant moment for this buyer; make breakage unmistakable.

## T19 — Settings page (DEMO-READY milestone)
- **Goal:** Editable confidence threshold with a **live impact panel** ("At 0.75, Scenario 5 (0.62) escalates; lower to 0.60 and it would allow-with-logging"); editable per-control mode; changes persist and take effect immediately.
- **Depends on:** T08, T15
- **Spec refs:** §8A item 7, §6
- **Files:** `app/web/templates/settings.html`, routes, `tests/T19_settings_ui/`
- **Done when:** moving the threshold to 0.60 and re-running #5 yields `allow_with_logging` with no restart.
- **Verify:** change threshold live; re-run #5; observe the flip. **Demo is now runnable end-to-end.**
- **Reviewer focus:** demonstrates "risk owns the policy"; impact panel is accurate to the current scenarios.

---

# PHASE 4 — Verify & present

## T20 — Test suite
- **Goal:** The four test files (spec §10): normaliser mapping; Presidio detection on the planted bodies; **policy decisions per scenario** (each of the six → expected §7 decision); audit chain integrity + tamper detection.
- **Depends on:** T13 (logic complete)
- **Spec refs:** §10, §12, §7
- **Files:** `tests/test_normaliser.py`, `test_presidio_sensor.py`, `test_policy_decisions.py`, `test_audit_chain.py`
- **Done when:** `pytest` is green; `test_policy_decisions` is the regression guard that the demo can never silently drift from §7.
- **Verify:** `docker compose run --rm app pytest -q`.
- **Reviewer focus:** the policy-decision test asserts the full §7 table; chain test asserts tamper detection.

## T21 — README + demo script (narration)
- **Goal:** README: what it is, how to run (`docker compose up`), the architecture in a paragraph, and the explicit list of what's real vs stubbed (spec §1). Plus a **demo script** — the spoken narration for the six scenarios + the tamper moment + the threshold change, written for the Head-of-Assurance audience, honouring §1B (no Horizon as a hook).
- **Depends on:** T19, T20
- **Spec refs:** §1, §1A, §1B, §7, §9
- **Files:** `README.md` (final), `DEMO_SCRIPT.md`
- **Done when:** a stranger can `docker compose up` and run the demo from the script alone; the narration leads with assurance value, not the scandal.
- **Verify:** follow your own README on a clean checkout; run the demo from the script.
- **Reviewer focus:** the "what's real vs stubbed" honesty list is present; demo script tone is right for the room.

---

## Parallelisation notes
- T17 can run alongside T15/T16.
- T20 test files can be written incrementally as each component lands (don't wait for the end).
- Everything else is linear by dependency.
