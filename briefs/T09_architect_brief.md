        "Thematic: human decision over automated output"
      ],
      "required_approval_role": "finance_supervisor",
      "enabled": true
    },
    "FIN-PAY-003": {
      "id": "FIN-PAY-003",
      "tier": "escalate",
      "decision": "escalate",
      "description": "Frequent payments (3+ in 30 days)",
      "framework_mappings": [
        "Counter-fraud monitoring control",
        "ISO/IEC 42001"
      ],
      "required_approval_role": "fraud_analyst",
      "enabled": true
    },
    "FIN-PAY-004": {
      "id": "FIN-PAY-004",
      "tier": "escalate",
      "decision": "escalate",
      "description": "Action affects individual financial standing",
      "framework_mappings": [
        "ISO/IEC 42001 (human oversight)",
        "Thematic: human accountability + evidential reliability"
      ],
      "required_approval_role": "named_decision_maker",
      "enabled": true,
      "proposed": true
    },
    "COMM-EMAIL-001": {
      "id": "COMM-EMAIL-001",
      "tier": "escalate",
      "decision": "escalate",
      "description": "External email with special-category data, no disclosure basis",
      "framework_mappings": [
        "UK GDPR Art.9 / DPA 2018",
        "Internal Data Disclosure Policy",
        "ISO/IEC 42001 (data governance)"
      ],
      "required_approval_role": "data_protection_approver",
      "enabled": true
    },
    "COMM-EMAIL-002": {
      "id": "COMM-EMAIL-002",
      "tier": "escalate",
      "decision": "escalate",
      "description": "External email with vulnerability indicators below confidence threshold",
      "framework_mappings": [
        "Internal Vulnerable-Customer Policy",
        "ISO/IEC 42001 (human oversight)"
      ],
      "required_approval_role": "vulnerable_customer_team",
      "enabled": true
    },
    "COMM-EMAIL-003": {
      "id": "COMM-EMAIL-003",
      "tier": "allow_with_logging",
      "decision": "allow_with_logging",
      "description": "External email with personal data (no special category)",
      "framework_mappings": [
        "UK GDPR Art.5(2) accountability",
        "Internal Data Disclosure Policy",
        "Record-keeping control RK-03"
      ],
      "required_approval_role": null,
      "enabled": true
    }
  }
}
```

Note: FIN-PAY-004 has `"proposed": true` — T10 will use this as a toggle flag per spec §6 / §1B.

### 2. `app/policy/opa_client.py` — OPA HTTP client

The client must:

- Accept `Action`, `Context`, `Evidence`, and `RuntimeSettings` (or its `.to_policy_config()` dict).
- Build the OPA input document and POST it to `{OPA_URL}/v1/data/policy/gate/decision`.
- The OPA input contract (document this in a docstring):
  ```json
  {
    "input": {
      "action": { ... Action model_dump(mode="json") ... },
      "context": { ... Context model_dump(mode="json") ... },
      "evidence": { ... Evidence model_dump(mode="json") ... },
      "config": {
        "high_confidence_threshold": 0.75,
        "control_modes": { ... }
      }
    }
  }
  ```
- Parse the OPA response `{"result": { ... Decision fields ... }}` into a `Decision` Pydantic model.
- On OPA unreachable (connection error, timeout, non-2xx response): return `Decision(decision="fail_closed", control_id=null, triggered_controls=[], reason="OPA unreachable", required_approval_role=null, framework_mappings=["Internal AI Governance Policy (safe-default)", "ISO/IEC 42001 (robustness)"], failure_mode="fail_closed", logging_requirements="enhanced", policy_version="unknown", threshold_used=<threshold from config>)`.
- Use `httpx` (already in requirements.txt via FastAPI) with a reasonable timeout (e.g. 5 seconds).
- Read `OPA_URL` from `app.config.get_settings().opa_url`.

### 3. `opa/policies/common.rego` — Trivial allow-all policy

A minimal Rego policy at package `policy.gate` that returns a hardcoded `allow` decision with all Decision schema fields populated. This proves the HTTP round-trip; T10 replaces it with real logic.

```rego
package policy.gate

default decision := {
    "decision": "allow",
    "control_id": null,
    "triggered_controls": [],
    "reason": "No controls triggered",
    "required_approval_role": null,
    "framework_mappings": [],
    "failure_mode": "fail_open",
    "logging_requirements": "standard",
    "policy_version": "0.1.0-trivial",
    "threshold_used": 0.75
}
```

Note: The trivial policy ignores `input.config.high_confidence_threshold` — that's fine for T09. T10 will read it.

### 4. `docker-compose.yml` — Mount OPA policies and data

The OPA service currently has no volume mounts. Add:

```yaml
opa:
  image: openpolicyagent/opa:latest
  container_name: ai_pel_opa
  command: ["run", "--server", "--addr=0.0.0.0:8181", "/policies", "/data"]
  ports:
    - "8181:8181"
  volumes:
    - ./opa/policies:/policies:ro
    - ./opa/data:/data:ro
```

This loads all `.rego` files from `/policies` and `controls.json` from `/data` on OPA startup.

## Non-negotiables
- The only Python-side decision is `fail_closed` when OPA is unreachable. All other decisions come from OPA.
- The Decision schema fields must match spec §5.4 exactly.
- The OPA input contract must be documented in `opa_client.py` docstring — T10 depends on it being stable.
- `controls.json` framework_mappings must match spec §6 verbatim.
- FIN-PAY-004 must have a `"proposed": true` flag (spec §6 / §1B).
- The fail-closed path must be a real try/except on the HTTP call, not a swallowed exception that defaults to allow.

## Verify step
1. `docker compose up --build` — all three services start.
2. Run `opa_client` against a live OPA with any valid Action/Context/Evidence → get back a parsed `Decision` with `decision="allow"`.
3. `docker compose stop opa` → run client again → get `Decision(decision="fail_closed")`.
4. `pytest tests/T09_opa_client/` passes.

## Handoff to Implementer
You are the Implementer Agent. Read `briefs/T09_architect_brief.md` and `briefs/T09_test_brief.md`. Implement exactly T09. Touch only the allowed files above plus the test file specified in the Test Brief. Do not start any other task. Report changed files and verification result.