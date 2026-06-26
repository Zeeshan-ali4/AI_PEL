from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = (ROOT / "README.md").read_text()
SCRIPT = (ROOT / "DEMO_SCRIPT.md").read_text()

SCENARIOS = {
    "1": ["allow", "no triggered control"],
    "2": ["escalate", "FIN-PAY-002", "finance_supervisor"],
    "3": ["block", "FIN-PAY-001"],
    "4": ["escalate", "COMM-EMAIL-001", "data_protection_approver", "0.88"],
    "5": ["escalate", "COMM-EMAIL-002", "vulnerable_customer_team", "0.62", "0.75", "0.60", "allow_with_logging"],
    "6": ["allow_with_logging", "COMM-EMAIL-003"],
}


def test_readme_audience_value_and_run_instructions():
    lower = README.lower()
    assert "runtime policy enforcement gate" in lower
    assert "head of risk and assurance" in lower
    assert lower.index("assurance value") < lower.index("how to run") < lower.index("architecture")
    assert "docker compose up --build" in README
    assert "http://localhost:8080" in README
    assert "localhost:8181" in README
    assert "localhost:5432" in README
    for page in ["/scenarios", "/approvals", "/audit", "/settings", "/records/{record_hash}"]:
        assert page in README


def test_readme_pipeline_real_stubbed_and_model_not_judge():
    lower = README.lower()
    arch = lower[lower.index("architecture in one paragraph"):]
    positions = [arch.index(term) for term in [
        "agent simulator", "policy enforcement point", "normalised", "context resolver",
        "semantic evidence layer", "opa", "enforcement handler", "hash-chained", "assurance ui",
    ]]
    assert positions == sorted(positions)
    for term in ["presidio", "opa/rego", "postgres-backed", "sha-256 hash-chained", "settings"]:
        assert term in lower
    for term in ["mcp interception", "enterprise connectors", "context", "nuance stub", "auth, multi-tenancy", "framework mappings", "one-shot"]:
        assert term in lower
    assert "payment actions skip the semantic layer" in lower
    assert "opa" in lower and "never from the model" in lower


def test_scenario_outcomes_match_in_readme_and_script():
    for number, tokens in SCENARIOS.items():
        for document in (README, SCRIPT):
            doc_lower = document.lower()
            marker = f"| {number} |" if document is README else f"scenario {number}"
            idx = doc_lower.index(marker)
            window = document[idx: idx + 900]
            for token in tokens:
                assert token in window


def test_threshold_shadow_audit_fail_closed_and_no_prohibited_framing():
    combined = README + "\n" + SCRIPT
    lower = combined.lower()
    assert "horizon" not in lower
    assert "illustrative" in README.lower() and ("not certified" in README.lower() or "not asserted" in README.lower())
    assert "illustrative" in SCRIPT.lower() and "not certified" in SCRIPT.lower()
    for token in ["0.75", "0.60", "shadow", "would have blocked", "verify chain", "simulate tampering", "download", "fail_closed", "auto-reset"]:
        assert token in lower


def test_demo_script_ten_beats_in_required_order_and_spoken():
    lower = SCRIPT.lower()
    beat_section = lower[lower.index("## beat 1"):]
    beats = [
        "## beat 1 — dashboard calm", "## beat 2 — live feed — routine",
        "## beat 3 — live feed — enforcement", "## beat 4 — human oversight",
        "## beat 5 — semantic evidence", "## beat 6 — shadow mode",
        "## beat 7 — policy control", "## beat 8 — confidence threshold",
        "## beat 9 — audit integrity", "## beat 10 — fail closed",
    ]
    positions = [beat_section.index(beat) for beat in beats]
    assert positions == sorted(positions)
    for pillar in ["human oversight", "evidential reliability", "demonstrable control", "governed configurable policy", "deterministic enforcement"]:
        assert pillar in lower
    assert SCRIPT.count(".") >= 35
    assert "```" not in SCRIPT
