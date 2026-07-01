"""Evidence Sources section acceptance tests for the decision detail page."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _run(client: TestClient, scenario_id: int) -> str:
    response = client.post(f"/scenarios/{scenario_id}/run")
    assert response.status_code == 200
    return response.text


def test_decision_view_renders_evidence_sources_heading(wired_pipeline):
    html = _run(TestClient(app), 1)

    assert "Evidence Sources" in html
    assert "Source-by-source view of the demo evidence" in html


def test_payment_decision_shows_fixture_crm_and_policy_engine_sources(wired_pipeline):
    html = _run(TestClient(app), 1)

    assert "CRM / Customer profile" in html
    assert "fixture_crm" in html
    assert "DEMO FIXTURE stand-in for CRM customer profile context" in html
    assert "Policy engine" in html
    assert "policy_engine" in html
    assert "Deterministic policy decision" in html


def test_email_decision_shows_content_analysis_source(wired_pipeline):
    html = _run(TestClient(app), 4)

    assert "Content analysis" in html
    assert "content_analysis" in html
    assert "PII, special-category indicators, vulnerability signal, confidence" in html
    assert "Semantic evidence only; the policy engine makes the binding decision" in html


def test_evidence_sources_do_not_break_existing_decision_rendering(wired_pipeline):
    html = _run(TestClient(app), 4)

    assert 'data-decision="escalate"' in html
    assert "COMM-EMAIL-001" in html
    assert "Resolved context used" in html
    assert "Evidence" in html
    assert "Enforcement" in html
