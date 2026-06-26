# Architect Brief — T25: Audit security demonstration (extends T17/T18)

## Task selected
- Task: T25 — Audit security demonstration (extends T17/T18)
- Current status: To do
- Dependencies checked: pass — T25 depends on T17 and T18; `TASK_LEDGER.md` marks both T17 and T18 as Done.

## Source-of-truth references
- MASTER_SPEC.md: §1 proof point 7 (every proposed action + decision is written to a tamper-evident, hash-chained evidence store, exportable for audit); §1 honesty principle (Presidio, OPA, and hash chain are real; stubs labelled); §5.5 Evidence Record and hash rule; §8A items 5–6 for evidence record export and audit log integrity UI; §10 canonical file layout for `app/audit/store.py`, `app/web/routes.py`, and the Jinja templates.
- TASK_LEDGER.md: T25 task definition, dependencies, file list, key notes, done criteria, verify step, reviewer focus, and estimate; T17/T18 dependency tasks are Done.
- AGENTS.md: work on exactly one task; touch only files listed for the current task plus the PM/BA-specified test file under `tests/`; do not broaden schemas, policy decisions, scenario outcomes, or audit append-only rules; every task must produce committed pytest tests.

## Allowed files
- `briefs/T25_architect_brief.md` — Architect handoff for this task.
- `app/web/templates/audit.html` — extend the audit log with visual hash-chain links and broken-link state.
- `app/web/templates/record.html` — extend single-record export affordance/copy to include chain hashes and package export linkage where appropriate.
- `app/audit/store.py` — add `export_audit_package()` for JSON bundle generation and package-level SHA-256 integrity hash.
- `app/web/routes.py` — extend export route(s) to serve the audit package for a `correlation_id` and/or date range.
- `tests/T25_audit_security/` — PM/BA must specify concrete target test file(s); Implementer must create `__init__.py` and real pytest coverage here.

## Implementation objective
Make the existing T17/T18 audit integrity story obvious to a non-technical assurance reviewer. The implementer should add a visual hash-chain presentation to the audit log and a JSON audit package export that bundles selected records with their chain hashes plus a package-level integrity hash. This is a demo-grade SHA-256 integrity package, not a digital signature or production attestation system.

## Non-negotiables
- Do not alter the Evidence Record schema or the canonical hash rule from `MASTER_SPEC.md` §5.5.
- Do not mutate historical audit rows as part of normal operation; approvals and other decisions remain append-only.
- Do not move decision-making into Python or templates. This task is audit/export/UI only; OPA remains the binding policy judge.
- Do not add PKI, signing keys, external verification services, WORM storage, background workers, or new infrastructure.
- Label the audit package honestly as a demo integrity check and state that production would use signed attestation.
- The visual chain must be understandable without cryptography jargon: show truncated current/previous hashes, a connector/arrow, green intact links, and a red broken link with mismatched hashes after tampering.
- Preserve T18's existing Verify Chain and Simulate Tampering behaviour while enhancing its visual output.
- `export_audit_package()` should be deterministic for the selected records: include a human-readable explanation/header, full selected records, relevant chain fields (`record_hash`, `prev_hash`, and enough adjacent/link information to verify continuity), selection metadata, and `package_integrity_hash` computed over a canonical representation of the package content excluding the hash itself.
- Tests must cover package content and hash stability/change. At minimum, PM/BA should require tests proving the package includes selected records and explanation text, exposes chain hashes, computes a reproducible package hash, and changes the package hash when exported record content/chain state changes.
- Scope is exactly T25. Do not implement T20/T21, do not change demo narration, and do not mark any ledger task Done.

## Verify step
Manual ledger verify: Run several scenarios. Open audit log. Confirm visual chain links are visible and green. Click "Download audit package" — open the file and confirm records and integrity hash are present. Simulate tampering — confirm the broken chain link turns red with mismatched hashes displayed. Download package again — confirm the integrity hash has changed.

Task-specific automated checks: run the PM/BA-specified pytest file(s) under `tests/T25_audit_security/` and any directly impacted existing tests for T17/T18 audit export/chain behaviour. If a Docker-based verify command is specified downstream, prefer the repository's established `docker compose run --rm app pytest ...` pattern.

## Handoff to Implementer
You are the Implementer Agent. Read briefs/T25_architect_brief.md and briefs/T25_test_brief.md. Implement exactly T25. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
