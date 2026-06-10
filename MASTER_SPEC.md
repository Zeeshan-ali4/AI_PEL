# Master Spec — Runtime Policy Enforcement Gate for AI Agent Actions (Demo Build)

**Status:** v1.1 — source of truth for the demo. Supersedes v1.0.
**Audience for the demo artifact:** the **Head of Risk and Assurance, Post Office Ltd**. The build is optimised to *demonstrate assurance* — visible human oversight, reliable evidence, and provable control operation — not engineering depth. Parts that are easy to fake (PII detection, the policy engine, the audit chain) are built for real, because faking them undermines the exact assurance claims the product makes.

Both Claude Code (architect/reviewer) and Codex (implementer) consume this document. Do not deviate from the schemas, file layout, or control logic here without updating this file first.

---

## 0. Changes in v1.1 (read first if you saw v1.0)

- Audience set to Post Office Head of Risk & Assurance; value framing rewritten around **assurance** (§1, §1A).
- **Decision precedence changed**: `block` is now reserved for a *clearly-prohibited / malicious* tier only. All other risk **escalates to a human**. (§6)
- Controls and scenarios recontextualised to a Post Office contact-centre agent; special-category email now **escalates**, not blocks. (§6, §7)
- New section on **UI/UX for assurance** (§8A) — the demo's centre of gravity.
- **Configurable confidence threshold** is now a first-class, UI-exposed setting. (§6, §8A)
- Framework mappings retuned for Post Office; **thematic** (not fabricated) alignment to the Horizon Inquiry. (§6)
- New **sensitivity & framing guidance** (§1B) — mandatory reading before the pitch.
- Deployment guidance updated for a government-owned, data-sensitive buyer (§14).

---

## 1. What the demo proves

1. An agent's proposed action is **intercepted before execution** (SDK wrapper PEP; MCP is the production path).
2. The action is **normalised** into one governance schema regardless of original tool.
3. Policy-relevant **context** is resolved from (clearly-labelled fixture) enterprise systems.
4. A **real deterministic sensor** (Presidio) and a **clearly-labelled model stub** produce **bounded evidence only** — never a decision.
5. A **real deterministic policy engine** (OPA/Rego) returns a **binding decision** with a control ID and framework mappings.
6. The decision is **enforced**; risky-but-legitimate actions route to a **named human**.
7. Every proposed action + decision is written to a **tamper-evident, hash-chained evidence store**, exportable for audit.
8. Risk can **see and tune** the controls (assurance dashboard + configurable threshold), and adopt safely via **shadow → soft → full**.

### Deliberately NOT in scope (state openly in the demo)
Real MCP interception; real connectors (context is fixtures); a real fine-tuned vulnerability model (one labelled stub); production auth/multi-tenancy/scale.

> **Honesty principle:** anything stubbed is labelled as stubbed in the UI. Presidio, OPA, and the hash chain are real. Do not stub them.

---

## 1A. Value pillars (the language for this buyer)

Lead with these, in roughly this order:

1. **Human oversight & contestability.** The system stops only what is clearly prohibited; every judgement call goes to a *named human* with the evidence in front of them. The machine is never the final arbiter.
2. **Evidential reliability & integrity.** Every consequential action has a complete, tamper-evident, exportable record. You can prove what the system did, what evidence it had, who decided, and that the record has not been altered.
3. **Demonstrable control operation.** Risk can see each control, its framework mapping, and live evidence it is operating — and can prove it operated *before* trusting it, via shadow mode.
4. **Governed, configurable policy.** Thresholds and controls are owned and tuned by risk in the open — not buried in code, prompts, or a vendor black box.
5. **Proportionate, deterministic enforcement.** The model is a sensor; the policy engine is the judge; uncertainty escalates; the system fails closed.

---

## 1B. Sensitivity & framing guidance (mandatory before the pitch)

- **Do not lead with Horizon. Do not use it as a hook.** This person lives it; the statutory inquiry is ongoing; people died. Leading with the tragedy reads as opportunistic and loses the room.
- Build so the assurance properties are *self-evidently* the antidote and let the buyer make the connection. They will, immediately.
- If it surfaces, reference it once, soberly, as "the assurance failures the sector is rightly focused on" — not by reciting the scandal.
- **Accuracy guard:** the Inquiry's Volume 1 (Jul 2025) and its 19 recommendations concern **compensation and redress**, not IT controls. Volume 2 (systemic failures, leadership, culture) addresses governance. Do **not** map controls to specific recommendation numbers. Alignment to the Inquiry is **thematic**: faulty automated outputs treated as authoritative, absence of effective human oversight/contestability, and reliance on system records of questionable integrity. The product addresses those failure-modes.

---

## 2. Principles the code must preserve

- **The model is not the judge. The policy engine is the judge. The model only provides evidence.** The Evidence schema contains **no allow/block field**. If you add one, stop.
- **Deterministic tools before general LLMs.** Presidio runs first; the stub adds only nuance the deterministic layer cannot.
- **Default to a human.** `block` is reserved for the clearly-prohibited tier; everything else escalates.
- **Uncertainty escalates, never silently allows.** Confidence below the configurable threshold → escalate.
- **Fail closed.** Sensor error / context failure / OPA unreachable → `fail_closed`.
- **Permissions decide who can reach the lever; this layer decides whether this specific pull is permitted.** The agent already *has* the tool permission; the gate still evaluates the instance.

---

## 3. Logical architecture (demo scope)

```
[Agent simulator]
   │ emits structured tool call
   ▼
[SDK wrapper = Policy Enforcement Point (PEP)]   ← interception happens HERE
   ▼
[Action normaliser]            → canonical Action schema
   ▼
[Context resolver]             → reads fixture "systems" → Context schema
   ▼
[Semantic evidence layer]      → Presidio (real) + nuance stub → Evidence schema (bounded, no decision)
   ▼
[Policy Decision Point = OPA]  → Action + Context + Evidence + config → Decision schema
   ▼
[Enforcement handler]          → applies decision; routes escalations to a named-role approval queue
   ▼
[Audit / evidence store]       → append-only, hash-chained record for EVERY proposed action
   ▼
[Assurance UI]                 → control dashboard, scenario runner, evidence records, approvals, settings, chain verify
```

Semantic layer runs **only** for action types whose policy needs meaning from unstructured content (email). The payment path skips it — intentional, demonstrates "semantics only where needed."

---

## 4. Technology decisions (final — do not substitute)

| Concern | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | single language; novice-friendly |
| Web | FastAPI | serves JSON + HTML |
| Templates | Jinja2 (server-rendered) | no JS build step |
| Styling | Tailwind via CDN | no toolchain |
| Schemas | Pydantic v2 | every schema below = a model |
| Policy engine | **OPA** (`openpolicyagent/opa`) container | app calls `POST /v1/data/...` |
| Policy language | Rego | |
| Deterministic sensor | **Presidio** (`presidio-analyzer`) | in-process; spaCy `en_core_web_sm` |
| Nuance sensor | **Stub** (`nuance_stub.py`) | deterministic-by-input; labelled |
| Audit store | **Postgres 15** container | append-only + SHA-256 hash chain |
| Orchestration | Docker Compose | services: `app`, `opa`, `postgres` |
| Config/settings | pydantic-settings + a DB-backed settings row | threshold is editable at runtime via UI |

> **Novice gotcha:** download the spaCy model at build time in the Dockerfile (`python -m spacy download en_core_web_sm`), not at runtime.

---

## 5. Canonical schemas (contracts — field names exact, Pydantic v2)

### 5.1 Action (normaliser output)
```json
{
  "action_id": "uuid", "correlation_id": "uuid", "timestamp": "ISO-8601",
  "action_type": "financial.payment.issue | communication.email.send",
  "actor": { "agent_id": "string", "agent_owner": "string", "role": "string" },
  "tool": "string", "target_system": "string",
  "resource": { "type": "string", "id": "string" },
  "parameters": { "...action-specific..." },
  "content": "string | null", "recipient": "string | null",
  "environment": "demo | sandbox | prod",
  "enforcement_mode": "shadow | soft | full"
}
```

### 5.2 Context (resolver output)
```json
{
  "customer": { "id": "string", "status": "normal | flagged | blocked",
                "vulnerability_flag": "boolean", "fraud_flag": "boolean",
                "sanctions_match": "boolean", "account_age_days": "int" },
  "payment_history": { "count_30d": "int", "total_30d_gbp": "number", "last_payment_date": "date | null" },
  "approval_state": { "has_approval": "boolean", "approver": "string | null", "approval_id": "string | null" },
  "recipient": { "is_external": "boolean", "domain": "string | null", "approved_disclosure_basis": "boolean" },
  "affects_individual_financial_standing": "boolean",
  "business_hours": "boolean",
  "context_resolution_ok": "boolean   ← false triggers fail_closed"
}
```

### 5.3 Evidence (semantic layer output — NO decision field)
```json
{
  "evaluated": "boolean (false for payment path)",
  "contains_personal_data": "boolean", "contains_special_category_data": "boolean",
  "sensitivity_level": "low | medium | high",
  "detected_entities": [ { "type": "string", "score": "number", "source": "presidio" } ],
  "evidence_spans": [ { "start": "int", "end": "int", "label": "string" } ],
  "vulnerability_indicators": { "present": "boolean", "confidence": "number 0..1",
                                "categories": ["financial_vulnerability","health","coercion"], "source": "nuance_stub" },
  "overall_confidence": "number 0..1",
  "sensor_versions": { "presidio": "string", "nuance_stub": "stub-0.1" },
  "sensor_error": "boolean   ← true triggers fail_closed"
}
```

### 5.4 Decision (OPA / PDP output — binding)
```json
{
  "decision": "allow | block | escalate | modify | allow_with_logging | require_evidence | fail_closed",
  "control_id": "string | null", "triggered_controls": ["string"],
  "reason": "string", "required_approval_role": "string | null",
  "framework_mappings": ["string"], "failure_mode": "fail_closed | fail_open",
  "logging_requirements": "standard | enhanced", "policy_version": "string",
  "threshold_used": "number   ← echoes the configurable threshold for the record"
}
```

### 5.5 Evidence Record (audit row — hash-chained)
```json
{
  "id": "bigint", "correlation_id": "uuid",
  "action": "Action (jsonb)", "context_used": "Context (jsonb)",
  "evidence": "Evidence (jsonb)", "decision": "Decision (jsonb)",
  "enforcement_mode": "shadow | soft | full", "executed": "boolean",
  "record_type": "action_evaluation | approval_decision",
  "references_hash": "sha256 hex | null   ← approval_decision rows reference the original action_evaluation",
  "human_approver": "string | null", "approval_reason": "string | null",
  "created_at": "timestamp", "record_hash": "sha256 hex", "prev_hash": "sha256 hex (genesis = 64 zeros)"
}
```

**Hash rule:** `record_hash = sha256( canonical_json(row minus id/record_hash) + prev_hash )`; canonical JSON = sorted keys, no whitespace. Altering any historical row breaks the chain; the UI exposes "verify chain" and "simulate tampering".

**Append-only approvals (do not mutate records):** an escalation writes an `action_evaluation` record with `executed=false`. When a human approves/rejects, **append a new `approval_decision` record** (same `correlation_id`, `references_hash` = the original record's hash, carrying `human_approver` + `approval_reason` + the resulting `executed` state). Never update the original row. The audit table only ever receives INSERTs; this is the property the "verify chain" demo proves.

---

## 6. Control library + decision precedence (the moat — small, but make it look hard-won)

**Decision precedence (highest wins):**
`fail_closed` > `block` (PROHIBITED tier only) > `escalate` > `require_evidence` > `modify` > `allow_with_logging` > `allow`.

**Default-to-human rule:** `block` is reserved for the *clearly-prohibited / malicious* tier. All other triggered risk resolves to `escalate`. OPA collects every triggered control, then resolves to the highest-precedence decision.

Threshold constant `HIGH_CONFIDENCE` is **configurable at runtime** (default `0.75`), stored in the settings row, passed into OPA input as `config.high_confidence_threshold`, and echoed into the Decision as `threshold_used`.

### PROHIBITED tier (the only controls that BLOCK)
| ID | Trigger | Decision | Framework mappings |
|---|---|---|---|
| **FIN-PAY-001** | `customer.fraud_flag` OR `customer.sanctions_match` OR `customer.status = blocked` | `block` | Internal Fraud & Financial Crime Policy; ISO/IEC 42001 (safe operation); 3 Lines of Defence (1st-line preventive control) |

### ESCALATE tier (risky-but-legitimate → named human)
| ID | Trigger | Decision (role) | Framework mappings |
|---|---|---|---|
| **FIN-PAY-002** | payment > £500 AND `approval_state.has_approval = false` | `escalate` (`finance_supervisor`); if approval present → `allow_with_logging` | Internal Delegated-Authority Policy; ISO/IEC 42001 (human oversight); thematic: human decision over automated output |
| **FIN-PAY-003** | `payment_history.count_30d` ≥ 3 | `escalate` (`fraud_analyst`) | Counter-fraud monitoring control; ISO/IEC 42001 |
| **FIN-PAY-004** *(PROPOSED — confirm; see §1B)* | `affects_individual_financial_standing = true` | `escalate` (`named_decision_maker`); never autonomous | ISO/IEC 42001 (human oversight); thematic: human accountability + evidential reliability for actions affecting an individual's finances |
| **COMM-EMAIL-001** | `recipient.is_external` AND `contains_special_category_data` AND `recipient.approved_disclosure_basis = false` | `escalate` (`data_protection_approver`) | UK GDPR Art.9 / DPA 2018; Internal Data Disclosure Policy; ISO/IEC 42001 (data governance) |
| **COMM-EMAIL-002** | `recipient.is_external` AND `vulnerability_indicators.present` AND `overall_confidence < HIGH_CONFIDENCE` | `escalate` (`vulnerable_customer_team`) | Internal Vulnerable-Customer Policy; ISO/IEC 42001 (human oversight) |

### ALLOW_WITH_LOGGING
| ID | Trigger | Decision | Framework mappings |
|---|---|---|---|
| **COMM-EMAIL-003** | `recipient.is_external` AND `contains_personal_data` AND not caught above | `allow_with_logging` (`enhanced`) | UK GDPR Art.5(2) accountability; Internal Data Disclosure Policy; record-keeping control RK-03 |

### GLOBAL — FAIL-CLOSED
`context_resolution_ok = false` OR `sensor_error = true` OR OPA unreachable → `fail_closed`. Mappings: Internal AI Governance Policy (safe-default); ISO/IEC 42001 (robustness).

> Framework references are **illustrative**; label them in the UI as "illustrative mapping — production packs are maintained against published control text." Do not cite Horizon Inquiry recommendation numbers (see §1B).

---

## 7. The six narrative scenarios

| # | Action | Fixtures | Expected | Control |
|---|---|---|---|---|
| 1 | Payment £80 | CUST-100 (normal, clean) | `allow` | none |
| 2 | Payment £850 | CUST-100, no approval | `escalate` → `finance_supervisor` | FIN-PAY-002 |
| 3 | Payment £200 | CUST-300 (active **fraud_flag**) | `block` | FIN-PAY-001 |
| 4 | External email; body has NHS number + health condition + "can't afford repayments" | external gmail; no disclosure basis; stub conf **0.88** | `escalate` → `data_protection_approver` | COMM-EMAIL-001 |
| 5 | External email; body has "struggling a bit since losing my job" | external; stub conf **0.62** (uncertain) | `escalate` → `vulnerable_customer_team` | COMM-EMAIL-002 |
| 6 | External email to known partner; body has a customer name only | external partner; no special category / no vulnerability | `allow_with_logging` | COMM-EMAIL-003 |

Decisions span allow / escalate / block / allow_with_logging. **Three escalations is intentional** — it embodies the "default to a human" message. The single `block` is the clearly-prohibited case. Talking point: "Notice how rarely it blocks — it blocks only the unambiguous, and routes every judgement to a named human."

The nuance stub is **deterministic-by-input**: it pattern-matches planted phrases to fixed confidences (0.88, 0.62, …) so a live demo is reproducible. Labelled in the UI as a model stand-in. Presidio's PII/health detection on these bodies is **real**.

Optional 7th demonstration: "Verify chain" + "Simulate tampering" — build last.

---

## 8. Enforcement modes (shadow → soft → full = the safe-adoption / assurance story)

- **shadow** — evaluate fully, write the record, but **always execute**; UI shows "would have blocked / would have escalated" badges. The assurance argument: *prove the controls fire correctly before trusting them.*
- **soft** — enforce only controls in an allow-list; shadow the rest.
- **full** — enforce all.

Single `enforcement_mode` per run; toggle visible in the UI.

---

## 8A. UI / UX for assurance (the demo's centre of gravity)

Server-rendered (FastAPI + Jinja2 + Tailwind CDN). Clean, calm, "assurance dashboard," not a dev tool. Required views:

1. **Control dashboard (landing).** Table of all controls: ID, plain-English purpose, tier (Prohibited / Escalate / Log), current mode (shadow/soft/full), framework chips, and live counts (allowed / escalated / blocked / logged). This is the artefact a risk leader shows their board. Add the enforcement-mode toggle and the live counter (see §9).
2. **Scenario runner.** The six scenarios as cards; "Run" triggers the full pipeline; result opens the decision view.
3. **Decision view.** The headline decision with colour and a one-line plain-English reason; the triggering control + framework chips; the **resolved context** used; the **evidence panel** showing real Presidio entities with highlighted spans, and the labelled stub confidence with a clear "model stand-in" tag; the `threshold_used`. If escalated, a prominent "Sent to {role} for human decision" state with a link to the approval queue.
4. **Approval queue (human oversight, visible).** Pending escalations with role, action summary, and evidence; Approve / Reject with a **required reason**. The approval **appends a new `approval_decision` record** linked to the original by `correlation_id` + `references_hash` (it does not mutate the original — see §5.5); the new record carries the approver, reason, and resulting `executed` state.
5. **Evidence record view.** The full record, readable and printable, with **"Export for audit"** (JSON + a human-readable PDF/HTML). Shows `record_hash`, `prev_hash`, approver, reason, execution status.
6. **Audit log + integrity.** Chronological records; **"Verify chain"** (green = intact, with the count verified); **"Simulate tampering"** alters a stored row in place and re-verifies to show the chain breaking and the exact record that fails. This is a headline moment for this buyer — give it room.
7. **Settings.** Editable **confidence threshold** with a live impact panel: "At 0.75, Scenario 5 (0.62) escalates. Lower to 0.60 and it would allow-with-logging instead." Editable per-control mode (shadow/soft/full). Changes persist to the settings row and take effect immediately. This demonstrates that **risk owns the policy**.

Accessibility/tone: large readable type, no jargon in primary copy, every stubbed/illustrative element visibly labelled.

---

## 9. "Log the gate, not the agent" — reframed as auditable surface

Each run carries a fixed `agent_steps` count (simulated internal steps, e.g. 12–40) and increments `consequential_actions_gated` by 1. The dashboard shows a running tally and one line:

> "This session: **94 agent steps**, **6 consequential actions gated and fully evidenced.** Full-transcript logging stores ~Nx more with no added assurance of control."

Copy must state plainly that this evidences the *auditable surface* — consequential actions and the binding decisions on them — not a complete, unauditable agent transcript.

---

## 10. File / directory layout (canonical — do not invent files outside this)

```
agent-policy-gate/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── README.md
├── requirements.txt
├── opa/
│   ├── policies/{common.rego, payment.rego, email.rego}
│   └── data/controls.json
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── settings_store.py            # DB-backed runtime settings (threshold, per-control mode)
│   ├── schemas/{action.py, context.py, evidence.py, decision.py, audit.py}
│   ├── pep/{sdk_wrapper.py, agent_simulator.py}
│   ├── normaliser/normaliser.py
│   ├── context/{resolver.py, fixtures.py}
│   ├── semantic/{presidio_sensor.py, nuance_stub.py, evidence_builder.py}
│   ├── policy/opa_client.py
│   ├── enforcement/{handler.py, approval_queue.py}
│   ├── audit/{models.py, store.py}
│   ├── pipeline.py
│   └── web/
│       ├── routes.py
│       ├── templates/{base.html, dashboard.html, scenarios.html, decision.html,
│       │              approvals.html, record.html, audit.html, settings.html}
│       └── static/
├── scenarios/scenarios.py
└── tests/{test_normaliser.py, test_presidio_sensor.py, test_policy_decisions.py, test_audit_chain.py}
```

---

## 11. Pipeline order (`pipeline.py`)

1. Receive intercepted tool call from `sdk_wrapper`.
2. `normalise()` → Action.
3. `resolve()` → Context (set `context_resolution_ok=false` on failure).
4. If email: `presidio_sensor` then `nuance_stub` → `evidence_builder` → Evidence; else `Evidence(evaluated=false)`. On exception set `sensor_error=true`.
5. Load runtime settings (threshold, per-control modes). `opa_client.decide(action, context, evidence, config)` → Decision. OPA failure → `fail_closed`.
6. `handler.enforce(decision, mode)` → set `executed`; route escalations to `approval_queue`.
7. `store.write_record(...)` → append-only, hash-chained. **Always written.**
8. Return to UI.

---

## 12. Acceptance criteria

- `docker compose up` brings up app + opa + postgres; UI on a documented port.
- All six scenarios produce exactly the §7 decisions.
- Payment scenarios never invoke the semantic layer (`evidence.evaluated=false`), shown in the UI.
- Scenario 4 shows **real** Presidio entities (not hardcoded) + the labelled stub confidence.
- Moving the threshold to 0.60 in Settings flips Scenario 5 to `allow_with_logging`, live.
- Shadow mode makes Scenario 3 execute anyway with a "would have blocked" badge; the record shows `executed=true, decision=block`.
- Approving an escalation appends a new `approval_decision` record (linked by `correlation_id` + `references_hash`) carrying approver + reason, sets `executed` accordingly, and leaves the original record unchanged.
- "Verify chain" passes; "Simulate tampering" makes it fail and names the broken record.
- "Export for audit" produces a readable record file.
- Storage counter updates per run.
- Every stubbed/illustrative element is visibly labelled.

---

## 13. Non-goals / scope fences (repeat to Codex every task)

- No real connectors, no real auth, no MCP, no real LLM call, no multi-tenancy.
- No allow/block field on Evidence.
- The decision comes from OPA, not Python. The only Python-made decision is `fail_closed` when OPA is unreachable.
- Do not create files outside §10 without updating this spec.
- Do not name Horizon Inquiry recommendation numbers or imply IT-control recommendations (§1B).

---

## 14. Deployment guidance (for the conversation, not the demo build)

Buyer is government-owned and acutely data-sensitive, mid-rebuild onto cloud (AWS). Lead with **customer-hosted / in-VPC**: the runtime and all action/customer/postmaster data stay in their environment; nothing egresses; they can inspect everything running. Position the **hybrid control plane** (vendor ships control-pack updates, licensing, framework-mapped library; sensitive data never leaves) as the long-term model. Be explicit that containers are packaging, not DRM — the moat is the control library, evidence model, framework-mapped packs, semantic quality, and maintenance, not code secrecy. Expect their assurance team to want to assure *the gate itself*: have an answer for how the gate's own behaviour and records are verifiable.
