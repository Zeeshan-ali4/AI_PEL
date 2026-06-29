# Demo script — AI PEL Runtime Policy Enforcement Gate

Audience: Head of Risk and Assurance. Tone: calm, transparent, and evidence-led. The purpose is not to show a clever chatbot; it is to show a control plane that intercepts AI-agent actions before execution, applies governed policy, routes judgement to named humans, and leaves a tamper-evident record.

Opening narration: "This demonstration is about human oversight and contestability, evidential reliability and integrity, demonstrable control operation, governed configurable policy, and proportionate deterministic enforcement. The model is not the judge. Presidio and the labelled nuance stub provide bounded evidence only; OPA/Rego is the binding policy decision-maker. Framework mappings and control packs in the UI are illustrative demo mappings, not certified or production-audited mappings."

Also say early: "Some components are real because assurance depends on them: Presidio detection is real, OPA/Rego policy decisioning is real, and the Postgres-backed SHA-256 hash chain is real. Other parts are deliberately demo-only and visibly labelled: MCP interception is represented by an SDK wrapper, enterprise connectors are context fixtures, the nuance/model layer is a deterministic stub, auth/multi-tenancy/production scale are out of scope, framework mappings/control packs are illustrative, and the one-shot policy engine failure control is a labelled simulation for the fail-safe moment."

## Beat 0 — Evidence gap framing

Open `http://localhost:8080/evidence-gap`. "Before we look at the system, it is worth being explicit about the evidence problem it solves." Walk the paired contrast: without a policy enforcement layer, assurance is reconstructed from logs after the fact; with AI PEL, the gate captures structured action, context, bounded evidence, binding decision fields, control mappings, and hash-chain custody at decision time.

Narration: "This page is not the demo evidence itself; it frames why the next screens matter. Now let's see what evidence looks like when it is structural rather than reconstructed." Move from the contrast page into the control dashboard.

## Beat 1 — Dashboard calm

Open `http://localhost:8080/`. "This is what your AI operations look like when the control plane is running." Show total evaluations, decision breakdown for allowed, escalated, blocked, and logged outcomes, and the action-type breakdown between payment and email. Point to the controls, modes, and framework chips.

Narration: "The important point is calm visibility. Risk can see the controls that exist, how they are operating, and the evidence that the gate is evaluating actions before execution. The dashboard is not a developer console; it is a board-readable assurance surface."

## Beat 2 — Live feed — routine

Open the live event feed and run Scenario 1, then optionally Scenario 6. Scenario 1 is a routine £80 payment for a clean customer: decision `allow`, no triggered control. Scenario 6 is an external partner email containing only ordinary personal data: decision `allow_with_logging`, control `COMM-EMAIL-003`.

Narration: "These are AI agents operating within policy. Every action is evaluated, every decision is recorded, and routine work stays routine. Notice the background events: they are green or neutral, but they are still recorded. Assurance is continuous, not only after something goes wrong."

## Beat 3 — Live feed — enforcement

Run Scenario 3 in the live event feed. It is a £200 payment for a fraud-flagged customer. The decision is `block` under `FIN-PAY-001`. Expand the red focal row and walk through interception, normalisation, context resolution, semantic skipped for payment, OPA/Rego policy decision, enforcement, and audit write.

Narration: "This agent tried to issue a refund to a flagged customer. The system caught it before execution. Payment scenarios deliberately skip the semantic evidence layer because no unstructured meaning is needed; the fraud and sanctions controls come from structured context and OPA/Rego policy. This is proportionate deterministic enforcement."

## Beat 4 — Human oversight

Run Scenario 2. It is an £850 payment with no approval. The decision is `escalate`, control `FIN-PAY-002`, required approval role `finance_supervisor`. Show the amber row, the approval queue badge increment, and the enriched approval item. Approve it with a short reason.

Narration: "This refund was legitimate but high-value. The system did not block it; it routed it to the right human. The approval is append-only: the original action evaluation remains unchanged, and the human decision appends a linked `approval_decision` record with the approver and reason. That is contestability and accountability in the evidence trail."

## Beat 5 — Semantic evidence

Run Scenario 4. It is an external email with an NHS number and health information but no approved disclosure basis. The decision is `escalate`, control `COMM-EMAIL-001`, required approval role `data_protection_approver`, and the labelled nuance stub confidence shown is `0.88`.

Narration: "Here the semantic layer matters. Presidio identifies personal and special-category indicators and the stub adds a bounded confidence signal, but neither sensor decides. The evidence panel is deliberately named evidence. OPA/Rego applies the policy and returns the binding escalation decision."

## Beat 6 — Shadow mode

Switch all controls to shadow mode on the dashboard or settings page. Re-run Scenario 3. The action executes because the mode is shadow, while the record says executed in shadow and `would have blocked` with `FIN-PAY-001`. Then switch back to full enforcement and re-run Scenario 3; it blocks.

Narration: "No enterprise deploys enforcement on day one. Shadow mode lets you observe before you enforce. It is honest: the action executes in shadow, but the evidence record still shows the full-enforcement decision that would have applied. That is how a risk team can prove control behaviour before turning it on."

## Beat 7 — Policy control

Open settings. Disable `FIN-PAY-002`, re-run Scenario 2, and show that it allows because the high-value approval control is disabled. Re-enable `FIN-PAY-002`. Change the FIN-PAY-002 amount threshold from `500` to `1000`, re-run Scenario 2, and show it allows. Restore the threshold from `1000` to `500`, re-run Scenario 2, and show it escalates again to `finance_supervisor`.

Narration: "Your risk team owns these policies. No code change. No deployment. The policy engine is still the judge; the UI changes governed configuration that is fed into the OPA input. This makes policy ownership visible and auditable."

## Beat 8 — Confidence threshold

Keep settings open. Change the semantic confidence threshold from `0.75` to `0.60`. Run Scenario 5. At the default threshold `0.75`, Scenario 5 is `escalate`, control `COMM-EMAIL-002`, required approval role `vulnerable_customer_team`, because the stub confidence is `0.62` and uncertainty escalates. At threshold `0.60`, the same `0.62` confidence flips to `allow_with_logging`.

Narration: "You decide the confidence level at which the system defers to a human. This is not a prompt hidden inside a model call; it is a risk-owned threshold, visible in the decision record as `threshold_used`. Restore the default threshold to `0.75` before continuing."

## Beat 9 — Audit integrity

Open the audit log. Click Verify chain and show the green intact result and verified count. Then click Simulate tampering, re-verify, and show the red broken link, mismatched hashes, and exact failing record. Download the audit package.

Narration: "Every decision is hash-chained. If anyone alters a historical record, the chain breaks and tells you where. Evidence can be extracted for external review. This is not only logging; it is evidential integrity. And notice that every record in the package carries an evidence schema version — so you can show a regulator not only what was captured, but that the definition of 'captured' was itself controlled and has not silently drifted between the start and end of the reporting period."

## Beat 10 — Fail closed

Use the labelled demo control to simulate one policy-engine failure. Trigger one-shot policy engine failure, then run the next live event. The policy decision stage says policy engine unreachable and the decision is `fail_closed` with enhanced logging. Run the following event normally and show that it no longer fails; the flag has auto-reset.

Narration: "This is a deliberately labelled one-shot simulation so we do not stop OPA for the whole room. The assurance claim is the behaviour: if the policy engine is unreachable, the default is stop, never allow. Then the next event runs normally because the simulation is consumed."
