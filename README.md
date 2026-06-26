# AI PEL — Runtime Policy Enforcement Gate (Demo Build)

A demo of a **runtime policy enforcement gate for AI agent actions**, built for a **Head of Risk and Assurance** audience. It is not a developer toy: it exists to show a risk leader that an AI agent's consequential actions can be intercepted, evaluated against governed policy, and evidenced — before anything happens — with a named human in the loop wherever there is judgement to be made.

## Assurance value (read this first)

The demo proves five things a risk function actually cares about:

1. **Human oversight & contestability.** The system only ever stops the clearly prohibited. Everything else — every judgement call — routes to a *named human* with the evidence in front of them. The machine is never the final arbiter.
2. **Evidential reliability & integrity.** Every consequential action produces a complete, tamper-evident, exportable record. You can prove what happened, what evidence existed, who decided, and that the record has not been altered.
3. **Demonstrable control operation.** Risk can see each control, its framework mapping, and live evidence that it is operating — and can prove it operates correctly *before* trusting it, via shadow mode.
4. **Governed, configurable policy.** Thresholds and controls are owned and tuned by risk in the open, not buried in code, prompts, or a vendor black box.
5. **Proportionate, deterministic enforcement.** The model is a sensor, not a judge. The policy engine decides. Uncertainty escalates. The system fails closed.

## How to run it

```bash
docker compose up --build
```

This brings up three services:

- `app` — the FastAPI application, on <http://localhost:8080>
- `opa` — Open Policy Agent (the policy decision point), on `localhost:8181`
- `postgres` — Postgres 15, the append-only, hash-chained audit store, on `localhost:5432`

Health check, confirming the app can really reach OPA and Postgres:

```bash
curl http://localhost:8080/health
```

Once the stack is up, visit the app at <http://localhost:8080> and walk the assurance UI:

| Page | Path | What it shows |
|---|---|---|
| Control dashboard (landing) | `/` | All controls, tiers, framework chips, live counts, enforcement-mode toggle |
| Scenario runner | `/scenarios` | The six narrative scenarios, each runnable with one click |
| Approval queue | `/approvals` | Pending escalations awaiting a named human decision |
| Evidence record view | `/records/{record_hash}` | A single record, readable, printable, exportable for audit |
| Audit log | `/audit` | Chronological records, "Verify chain", "Simulate tampering" |
| Settings | `/settings` | Editable confidence threshold and per-control enforcement mode |

For a guided walkthrough script you can read aloud while demoing, see [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md).

## Architecture in one paragraph

An agent simulator emits a structured tool call, which is intercepted by an SDK wrapper acting as the **Policy Enforcement Point (PEP)** — this is where interception happens, before anything executes. The call is normalised into a canonical Action, then a context resolver attaches policy-relevant context from clearly-labelled fixture systems. For actions whose policy needs meaning from unstructured content (email), the semantic evidence layer runs — a real Presidio sensor plus a labelled nuance stub — and produces bounded Evidence with no decision field. The Action, Context and Evidence, together with the current configuration, are sent to **OPA**, the Policy Decision Point, which returns a binding Decision with a control ID and framework mappings. An enforcement handler applies that decision under the current enforcement mode and routes any escalation to a named-role approval queue. Every proposed action and decision — regardless of outcome — is written to an append-only, hash-chained audit/evidence store, which the assurance UI exposes through the dashboard, scenario runner, approvals, records, audit log, and settings pages.

## What is real vs stubbed

This is a demo, and every stub is visibly labelled in the UI rather than disguised. Be upfront about this distinction with anyone evaluating the build.

**Real:**
- The **Presidio** sensor — real PII/PHI detection, including a custom UK NHS-number recognizer, run in-process against the planted email bodies.
- The **OPA/Rego** policy engine — a real policy decision point making the binding decision; the only decision Python itself can make is `fail_closed` when OPA is unreachable.
- The **Postgres-backed, SHA-256 hash-chained audit store** — genuinely append-only, with a real "Verify chain" and a real "Simulate tampering" demonstration of breakage.

**Stubbed / fixture (deliberately, and labelled as such in the UI):**
- **MCP interception** — the SDK wrapper stands in for the production MCP interception path.
- **Enterprise connectors and context** — customer, payment-history, and approval-state data come from clearly-labelled fixtures, not live systems.
- The **nuance stub** (`nuance_stub.py`) — a deterministic-by-input model stand-in (planted phrases map to fixed confidences) so the demo is reproducible; it is not a fine-tuned vulnerability model.
- **Auth, multi-tenancy and production scale** — out of scope for this demo build.
- **Framework mappings** (e.g. ISO/IEC 42001, UK GDPR, "3 Lines of Defence") shown against each control are **illustrative** — production framework packs are maintained against published control text, not asserted here as certified or production-audited mappings.

## The model is not the judge

Presidio and the nuance stub only ever produce bounded **evidence** — entities, spans, a confidence score. Neither can express an allow/block/escalate decision; that field does not exist on the Evidence schema. Payment actions skip the semantic layer entirely (`evidence.evaluated=false`), because payments need no meaning extracted from unstructured content — this is a deliberate demonstration of "semantics only where needed." For every action type, the decision comes from **OPA**, never from the model.

## The six narrative scenarios

| # | Action | Decision | Control / role |
|---|---|---|---|
| 1 | Payment £80, clean customer | `allow` | no triggered control |
| 2 | Payment £850, no approval | `escalate` → `finance_supervisor` | FIN-PAY-002 |
| 3 | Payment £200, fraud-flagged customer | `block` | FIN-PAY-001 |
| 4 | External email with NHS number + health condition, no disclosure basis | `escalate` → `data_protection_approver` (stub confidence 0.88) | COMM-EMAIL-001 |
| 5 | External email, uncertain vulnerability signal | `escalate` → `vulnerable_customer_team` (stub confidence 0.62) | COMM-EMAIL-002 |
| 6 | External email to a known partner, customer name only | `allow_with_logging` | COMM-EMAIL-003 |

Notice how rarely the system blocks: only the unambiguous, clearly-prohibited case (Scenario 3) blocks outright. Every other judgement call — three out of six scenarios — escalates to a named human.

## Settings and the configurable threshold

The `high_confidence_threshold` setting defaults to **0.75** and directly governs Scenario 5. At **0.75**, the stub's confidence of 0.62 falls below the threshold, so the system treats the vulnerability signal as uncertain and **escalates** to `vulnerable_customer_team` (COMM-EMAIL-002). Lower the threshold to **0.60** in Settings and re-run Scenario 5: the same 0.62 confidence is now above the threshold, so the decision flips live to `allow_with_logging` (COMM-EMAIL-003) — no restart required. This demonstrates that risk owns the policy, not engineering.

## Audit chain verification and tamper detection

Every proposed action and decision is written to the audit store as an append-only, SHA-256 hash-chained record, whether the run is shadow, soft, or full enforcement. On the audit log page, **"Verify chain"** recomputes the hash chain and reports it intact (with the count of records verified). **"Simulate tampering"** deliberately alters a stored row in place; re-running "Verify chain" afterwards makes the break unmistakable and names the exact broken record — proving the chain detects any after-the-fact alteration.

Approvals are append-only too: approving or rejecting an escalation never edits the original record. It appends a new, linked `approval_decision` record carrying the approver, the required reason, and the resulting execution state.

## Enforcement modes, shadow mode, and fail closed

Shadow mode is intentionally honest: the action executes because enforcement is shadow, while the decision view and audit record still show the full-enforcement result that would have applied, for example "Executed (shadow) — would have blocked — FIN-PAY-001". Soft and full modes let the same OPA/Rego decisions move from observation into enforcement without changing the scenario logic.

The demo also includes a visibly labelled one-shot policy-engine failure simulation. It sets a temporary flag that makes the next policy decision return `fail_closed` with policy-engine-unreachable messaging and enhanced logging, then auto-resets so the following event returns to the normal OPA path. In production, fail-closed is not a gimmick: when OPA is unreachable, required context fails, or sensors fail, Python may only return `fail_closed` rather than silently allowing the action.

## Demo script

Use [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) for a 12–15 minute narrated walkthrough in this exact order: dashboard calm, routine live feed, enforcement live feed, human oversight, semantic evidence, shadow mode, policy control, confidence threshold, audit integrity, and fail closed.
