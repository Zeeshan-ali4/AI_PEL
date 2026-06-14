# Architect Brief — T02: Pydantic v2 schemas (all five)

## Task selected
- Task: T02 — Pydantic v2 schemas (all five)
- Current status: TODO (listed as "To do" in `TASK_LEDGER.md`)
- Dependencies checked: pass — T02 depends on T01, and T01 is marked Done in `TASK_LEDGER.md`. The ledger also states the current task is T02 and there are no known blockers.

## Source-of-truth references
- `MASTER_SPEC.md`:
  - §2 Principles: the model is not the judge; Evidence must contain no allow/block/decision field; fail-closed conditions are context failure, sensor error, or OPA unreachable.
  - §4 Technology decisions: schemas must use Pydantic v2.
  - §5 Canonical schemas: implement Action (§5.1), Context (§5.2), Evidence (§5.3), Decision (§5.4), and EvidenceRecord (§5.5) with exact field names.
  - §6 Control library: Decision values, failure modes, enforcement modes, framework mappings, and `threshold_used` must support later OPA policy output.
  - §10 File/directory layout: schema files live under `app/schemas/`.
  - §13 Scope fences: no decision field on Evidence; no policy decision in Python other than later OPA-unreachable `fail_closed` handling.
- `TASK_LEDGER.md`:
  - T02 goal, files, key notes, done criteria, verify command, and reviewer focus.
  - Golden rules: do not start tasks without DONE dependencies, touch only task files, preserve real components/stub labels, keep Evidence decision-free.
- `AGENTS.md`:
  - Work on exactly one task from the ledger at a time.
  - `MASTER_SPEC.md` wins on conflicts.
  - During coding, touch only files listed for the current task and do not create extra files unless the task allows them.
  - Do not mark the task DONE unless verification passes; human remains final gate.

## Allowed files
- `app/schemas/action.py`
- `app/schemas/context.py`
- `app/schemas/evidence.py`
- `app/schemas/decision.py`
- `app/schemas/audit.py`

Architect-stage output also creates this handoff file:
- `briefs/T02_architect_brief.md`

## Implementation objective
Implement the five canonical Pydantic v2 schema modules exactly as `MASTER_SPEC.md` §5 defines them. These are contracts for every downstream task, so prioritise field-name fidelity, clear closed-value enums, validation that matches the documented shapes, and plain-English docstrings that make each model a living data dictionary.

The implementer should create models that can be imported and instantiated independently for hand-built examples of Action, Context, Evidence, Decision, and EvidenceRecord. Use Pydantic v2 APIs and type annotations that preserve downstream JSON serialisation behaviour for nested objects, timestamps, dates, UUIDs, hashes, lists, dictionaries, nullable fields, and numeric confidence/threshold values.

## Non-negotiables
- Implement exactly T02 only. Do not implement normalisation, context fixtures, semantic sensors, OPA clients, audit storage, settings, pipeline logic, web routes, or tests beyond the test file requested by the PM/BA Test Brief.
- Touch only the allowed schema files above plus the test file specified in `briefs/T02_test_brief.md` once it exists. If a needed file such as `app/schemas/__init__.py` appears necessary, stop and ask; it is not listed in T02.
- Field names must match `MASTER_SPEC.md` §5 verbatim, including `record_type`, `references_hash`, and `threshold_used`.
- Use enums for closed value sets, including but not limited to:
  - Action `action_type`: `financial.payment.issue`, `communication.email.send`
  - Environment: `demo`, `sandbox`, `prod`
  - Enforcement mode: `shadow`, `soft`, `full`
  - Customer status: `normal`, `flagged`, `blocked`
  - Evidence `sensitivity_level`: `low`, `medium`, `high`
  - Evidence entity source: `presidio`
  - Vulnerability categories: `financial_vulnerability`, `health`, `coercion`
  - Vulnerability source: `nuance_stub`
  - Decision: `allow`, `block`, `escalate`, `modify`, `allow_with_logging`, `require_evidence`, `fail_closed`
  - Failure mode: `fail_closed`, `fail_open`
  - Logging requirements: `standard`, `enhanced`
  - EvidenceRecord `record_type`: `action_evaluation`, `approval_decision`
- Evidence must not contain any field that can express approval, enforcement, allow, block, decision, policy outcome, or human approval state. Evidence is sensor output only.
- Do not put policy logic into these schemas. Validation may enforce schema shape and obvious ranges, but OPA will later make binding decisions.
- Numeric confidence values should be constrained to the documented 0..1 range where applicable: `vulnerability_indicators.confidence`, `overall_confidence`, and `threshold_used`.
- The audit record model should represent nested `Action`, `Context`, `Evidence`, and `Decision` objects, not untyped decision/evidence blobs, while remaining serialisable for later JSONB/hash-chain storage.
- `record_hash` and `prev_hash` should be modelled as SHA-256 hex strings; `references_hash` is nullable but, when present, should follow the same shape.
- T02 should not create database tables, hashing functions, OPA input contracts, or runtime settings. Those belong to later tasks.
- Add concise docstrings or field descriptions explaining each model/field in plain English; avoid over-engineering or hidden behaviour.

## Verify step
Ledger verify command:

```bash
docker compose run --rm app python -c "from app.schemas.evidence import Evidence; print('ok')"
```

Repeat the import check for every schema module, for example:

```bash
docker compose run --rm app python -c "from app.schemas.action import Action; from app.schemas.context import Context; from app.schemas.evidence import Evidence; from app.schemas.decision import Decision; from app.schemas.audit import EvidenceRecord; print('ok')"
```

Task-specific checks for the implementer/QA:
- Instantiate one valid hand-built example of each model.
- Confirm enum validation rejects invalid closed-set values.
- Confirm confidence/threshold range validation rejects values outside 0..1.
- Confirm Evidence has no field named or semantically equivalent to `allow`, `block`, `decision`, `approved`, `approval`, `enforcement`, or `executed`.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T02_architect_brief.md` and `briefs/T02_test_brief.md`. Implement exactly T02. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.
