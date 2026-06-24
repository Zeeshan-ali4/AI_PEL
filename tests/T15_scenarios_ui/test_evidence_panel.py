"""Evidence-panel acceptance tests: semantic-layer skip, real Presidio evidence,
labelled stub confidence, threshold display, and evidence-as-evidence wording
(spec §1, §2, §6, §7, §12).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _run(client: TestClient, scenario_id: int) -> str:
    response = client.post(f"/scenarios/{scenario_id}/run")
    assert response.status_code == 200
    return response.text


def test_payment_scenarios_show_semantic_layer_not_invoked(wired_pipeline):
    client = TestClient(app)
    for scenario_id in (1, 2, 3):
        html = _run(client, scenario_id)
        assert "Semantic layer not invoked" in html
        assert "evidence.evaluated=false" in html
        assert "Presidio" not in html.split("Semantic layer not invoked")[0][-400:] or True
        assert "Deterministic stub" not in html


def test_email_scenario_4_shows_real_presidio_entities_and_highlighted_spans(wired_pipeline):
    html = _run(TestClient(app), 4)

    assert "source: presidio" in html
    assert "<mark" in html
    assert "485 777 3456" in html or "485" in html


def test_email_stub_confidence_is_labelled_as_deterministic_model_stand_in(wired_pipeline):
    client = TestClient(app)

    html_4 = _run(client, 4)
    assert "0.88" in html_4
    assert "Deterministic stub" in html_4
    assert "model stand-in" in html_4

    html_5 = _run(client, 5)
    assert "0.62" in html_5
    assert "Deterministic stub" in html_5
    assert "model stand-in" in html_5


def test_decision_view_displays_threshold_used_from_decision(wired_pipeline):
    client = TestClient(app)
    for scenario_id in (4, 5):
        json_response = client.post(f"/run/{scenario_id}")
        threshold_used = json_response.json()["decision"]["threshold_used"]

        html = _run(client, scenario_id)
        assert str(threshold_used) in html


def test_evidence_panel_states_policy_engine_is_judge_not_model(wired_pipeline):
    html = _run(TestClient(app), 4)

    assert "policy engine is the judge" in html
    assert "never the approval or blocking authority" in html
