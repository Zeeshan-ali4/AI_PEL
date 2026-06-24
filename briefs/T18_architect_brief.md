# Architect Brief — T18: Audit log + verify chain + simulate tampering (headline moment)

## Task selected
- Task: T18 — Audit log + verify chain + simulate tampering (headline moment)
- Current status: To do
- Dependencies checked: pass — T18 depends on T12 and T14; both are marked Done in `TASK_LEDGER.md`.

## Source-of-truth references
- MASTER_SPEC.md: §1 points 7–8 (tamper-evident evidence store and risk-visible controls); §1A pillar 2 (evidential reliability and integrity); §5.5 Evidence Record and hash rule; §8A item 6 Audit log + integrity; §10 canonical file layout; §12 acceptance criteria that verify chain passes and simulated tampering fails with the broken record named.
- TASK_LEDGER.md: T18 task block (goal, dependencies, files, done when, verify, reviewer focus); T12 task block for existing `verify_chain()` and `simulate_tampering()` store behaviours; T14 task block for shared UI/dashboard conventions and route/template style.
- AGENTS.md: Work on exactly one task; touch only files allowed for T18 plus tests; do not broaden scope or alter schemas/policy/scenario outcomes; every task must produce committed pytest tests under the task test subfolder; do not mark T18 Done.

## Allowed files
- `app/web/templates/audit.html`
- `app/web/routes.py`
- `tests/T18_audit_ui/`

## Implementation objective
Build the assurance-facing Audit Log + Integrity page for T18. The page must list audit/evidence records chronologically and make the hash-chain integrity demo clear enough to be a headline moment for a Head of Risk and Assurance. Add routes that let a user verify the current chain, simulate deliberate tampering through the existing audit-store helper, and return to the audit page with an unmistakable integrity status.

The implementation should reuse the real T12 audit store behaviour. Normal application writes must remain append-only. The only in-place update path should be the existing deliberately named `simulate_tampering()` helper, surfaced in the UI as a demo-only tamper action.

## Non-negotiables
- Do not implement a fake chain verifier in the web layer. Call the real audit store `verify_chain()` behaviour from T12.
- Do not implement normal update/delete audit operations. The audit table remains append-only in normal operation.
- The simulated tampering route must be visibly demo-only and must call the deliberately separate tamper helper from T12.
- The integrity result must be visually unambiguous: green/intact with verified count, or red/broken naming the exact failing record/row returned by `verify_chain()`.
- The chronological audit list must expose enough fields for assurance review: record id, created time, record type, correlation id, decision, executed state, `record_hash`, `prev_hash`, and a link to the existing single-record view where available.
- Provide a “reset demo data” affordance if an existing reset/seed route/helper is available within the allowed route/store surface. If no reset helper exists, do not invent a new data-management subsystem outside T18 scope; instead show clear copy explaining how to reseed/reset via the existing demo workflow.
- Do not change canonical schemas, hash calculation rules, policy decisions, scenario outcomes, or approval append-only semantics.
- Keep UI tone aligned with §8A: calm, large readable type, assurance-first copy, no jargon in primary messages, and clear labels for demo-only tampering.
- Do not touch T19 settings or any other future task.

## Verify step
Ledger verify: `verify → intact; simulate tampering → fail names the row`.

Required implementation checks for this task:
1. Start with a clean/demo dataset containing at least one audit record.
2. Visit the audit log page and run Verify Chain.
3. Confirm the page shows an intact green result and includes the verified record count.
4. Trigger Simulate Tampering.
5. Confirm the page re-verifies and shows a clear red failure naming the exact failing row/record.
6. Run the T18 pytest tests in `tests/T18_audit_ui/`.

Suggested command-level verification for implementer/QA:
- `docker compose run --rm app pytest -q tests/T18_audit_ui/`
- If the app stack is available, exercise the UI routes with `curl` or browser clicks: audit page → verify action → simulate tampering action.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T18_architect_brief.md` and `briefs/T18_test_brief.md`. Implement exactly T18. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
