# Review Report — T22: Live event feed with background traffic (headline demo moment)

## Verdict
REQUEST CHANGES

## Critical findings
- Full T22 verification was not completed in this environment: `docker compose run --rm app pytest tests/T22_event_feed/` could not run because Docker is unavailable, and local `pytest tests/T22_event_feed/` skipped the real OPA-backed acceptance tests because no `opa` binary or `OPA_URL` was available. The T22 ledger requires real-pipeline/OPA/audit verification before the task can be treated as done.

## Spec and ledger compliance
- Correct task only: yes
- Dependencies respected: yes
- Allowed files only: yes
- `Done when` satisfied: no
- `Verify` satisfied: no
- Reviewer focus satisfied: yes, subject to completing real-dependency verification

## Product invariant checks
- Model is not judge: pass
- OPA/PDP owns decisions: pass
- Evidence has no decision fields: pass
- Fail-closed preserved: pass
- Append-only audit preserved: pass
- Stubs labelled: pass
- Scenario outcomes preserved: pass, subject to completing real-dependency verification

## Required changes
1. Run the required T22 verification in an environment with Docker Compose or a real OPA endpoint available, and confirm the T22 acceptance tests exercise the real pipeline/OPA/audit path rather than being skipped.

## Non-blocking notes
- The implementation stays within the T22 file boundary, adds the required background-event pool, SSE endpoint, focal trace capture, event-feed template/static JS, and split tests under `tests/T22_event_feed/`.
- The local unit-only portion of `pytest tests/T22_event_feed/` passed, but this is not enough to satisfy T22 because the real-dependency acceptance tests were skipped.