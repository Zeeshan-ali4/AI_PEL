# QA Report — T21: README + demo script (narration)

## Verdict
PASS

## What was verified
- Read `MASTER_SPEC.md` (§1, §1A, §1B, §6, §7, §8A), `TASK_LEDGER.md` (T21 block), `briefs/T21_architect_brief.md`, `briefs/T21_test_brief.md`, `briefs/T21_reviewer_brief.md`.
- Confirmed scope: only `README.md`, `DEMO_SCRIPT.md`, `tests/T21_readme_demo/*`, plus the three ledger-authorised minor additions (`app/pipeline.py`, `app/settings_store.py`, `app/web/routes.py`, `app/web/templates/{dashboard,decision,settings}.html`). No schema, Rego, control-ID, or scenario-outcome changes — matches AGENTS.md non-negotiables.
- Read `README.md` (101 lines) and `DEMO_SCRIPT.md` (67 lines) in full:
  - README leads with the five assurance value pillars before architecture/run instructions.
  - Run instructions (`docker compose up --build`, ports 8080/8181/5432, page map) are present and match `docker-compose.yml`/`.env.example`.
  - "What is real vs stubbed" section present with the required Real/Stubbed lists.
  - Six-scenario outcome table matches §7 exactly (decision, control ID, approval role, stub confidences 0.88/0.62, threshold 0.75→0.60 flip).
  - Payment-skips-semantics and model-is-not-judge statements present.
  - No mention of "Horizon"; framework mappings labelled illustrative.
  - DEMO_SCRIPT contains the ten beats in the required order (dashboard calm → routine feed → enforcement feed → human oversight → semantic evidence → shadow mode → policy control → confidence threshold → audit integrity → fail closed), walks all six scenarios with correct outcomes, and reads as spoken narration (no code fences, full sentences).

## Test execution
- `tests/T21_readme_demo/` (3 files: `__init__.py`, `test_readme_demo_content.py`, `test_demo_support_behaviour.py`): **6/6 passed** (ran with `python3 -m pytest -q tests/T21_readme_demo`, after installing `psycopg[binary]`, `python-multipart`, `presidio-analyzer`, etc. locally — no Docker daemon available in this QA environment).
- Ran the full repo test suite (`tests/`) for regression coverage of the touched runtime files:
  - 165 passed, 91 skipped, 2 failed, 4 errors.
  - All failures/errors trace to one root cause: `psycopg.OperationalError: ... Name or service not known` — the tests need the real `postgres`/`opa` containers (hostnames `postgres`/`opa` only resolve inside `docker compose`), which are unavailable in this sandbox (no Docker daemon: `dial unix /var/run/docker.sock: ... no such file or directory`).
  - Confirmed these are infra-only failures, not caused by T21: the failing tests (`tests/test_policy_decisions.py`, `tests/T15_scenarios_ui/test_scenario_runner.py`) fail at `app/audit/store.py::_postgres_connection`, unrelated to the diff's content (doc files + one-shot OPA-failure flag + dashboard stats + shadow-mode callout).
  - This matches the Reviewer's own note that the Docker-based Verify step could not be run in their environment either.

## Test Brief coverage check
All test brief cases are covered by the 6 implemented tests (consolidated per the brief's "suggested" file split, as already flagged non-blocking by the Reviewer):
- README audience/value-pillars-first, run instructions, architecture pipeline order, real-vs-stubbed completeness, six-scenario exact mapping, payment/model-is-not-judge statements, threshold/audit/shadow/fail-closed mentions — covered in `test_readme_demo_content.py`.
- Demo script value pillars, ten-beat order, six-scenario walkthrough, shadow/policy-control/threshold/audit/fail-closed moments, spoken-narration heuristic, no-Horizon, illustrative-mapping labelling, README/script cross-consistency — covered in `test_readme_demo_content.py`.
- Dashboard aggregate stats, shadow-mode callout, one-shot OPA failure auto-reset (the three ledger-authorised runtime additions) — covered in `test_demo_support_behaviour.py`.

## Manual Verify step (TASK_LEDGER.md)
Not executable in this QA environment: no Docker daemon present (`docker ps` fails to connect to the daemon socket), so the full `docker compose up --build` walkthrough and the 10-beat manual demo could not be performed here. This is consistent with the Architect/Reviewer briefs' own caveats. **This remains outstanding and must be done by the human gate** before marking T21 `DONE`, per AGENTS.md ("You = the human gate... run the Verify step yourself").

## Findings
- No code or content defects found in scope.
- No schema, control-ID, policy, or scenario-outcome drift.
- No unlabelled stubs; no prohibited Horizon framing; framework mappings labelled illustrative.

## Recommendation
QA passes T21 on all checks executable without Docker (content correctness, test-brief coverage, regression safety of the touched runtime files, all reachable via real component instantiation). The human gate should still complete the manual `docker compose up --build` walkthrough and the 10-beat demo run before flipping T21 to `DONE` in `TASK_LEDGER.md`, since that step requires live Postgres/OPA containers not available here.
