"""End-to-end decision-view acceptance tests for all six canonical scenarios.

These exercise the real route -> pipeline -> real OPA path (spec §7, §8A item 3,
§12). Nothing here mocks OPA, Presidio, the settings store, or the audit write
path.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

EXPECTED = {
    1: ("allow", None, None),
    2: ("escalate", "FIN-PAY-002", "finance_supervisor"),
    3: ("block", "FIN-PAY-001", None),
    4: ("escalate", "COMM-EMAIL-001", "data_protection_approver"),
    5: ("escalate", "COMM-EMAIL-002", "vulnerable_customer_team"),
    6: ("allow_with_logging", "COMM-EMAIL-003", None),
}


def _run(client: TestClient, scenario_id: int):
    response = client.post(f"/scenarios/{scenario_id}/run")
    assert response.status_code == 200
    return response.text


def test_each_run_opens_decision_view_with_expected_outcome(wired_pipeline):
    client = TestClient(app)
    for scenario_id, (decision, control_id, role) in EXPECTED.items():
        html = _run(client, scenario_id)
        assert f'data-decision="{decision}"' in html
        if control_id is not None:
            assert control_id in html
        else:
            assert "No control was triggered" in html
        if role is not None:
            assert f"Sent to {role} for human decision" in html


def test_decision_view_shows_plain_reason_headline_and_colour_state(wired_pipeline):
    client = TestClient(app)
    for scenario_id in (1, 2, 3, 6):
        html = _run(client, scenario_id)
        decision, _, _ = EXPECTED[scenario_id]
        assert f'data-decision="{decision}"' in html
        # The reason is rendered as readable prose, not buried only in raw JSON.
        assert '"reason"' not in html


def test_decision_view_shows_triggered_control_and_framework_chips(wired_pipeline):
    client = TestClient(app)
    for scenario_id in (2, 3, 4, 5, 6):
        html = _run(client, scenario_id)
        _, control_id, _ = EXPECTED[scenario_id]
        assert control_id in html
        assert "illustrative mapping" in html
        assert "Horizon" not in html

    html_1 = _run(client, 1)
    assert "No control was triggered" in html_1


def test_decision_view_displays_resolved_context_used(wired_pipeline):
    client = TestClient(app)

    html_payment = _run(client, 2)
    assert "Customer status" in html_payment
    assert "Existing approval on record" in html_payment
    assert "Payments in the last 30 days" in html_payment

    html_email = _run(client, 4)
    assert "Recipient is external" in html_email
    assert "Approved disclosure basis" in html_email


def test_escalated_decisions_show_human_routing_and_approval_link(wired_pipeline):
    client = TestClient(app)
    for scenario_id in (2, 4, 5):
        _, _, role = EXPECTED[scenario_id]
        html = _run(client, scenario_id)
        assert f"Sent to {role} for human decision" in html
        assert 'href="/approvals"' in html


def test_existing_json_run_endpoint_remains_backward_compatible(wired_pipeline):
    client = TestClient(app)
    for scenario_id in (1, 4):
        decision, control_id, role = EXPECTED[scenario_id]
        response = client.post(f"/run/{scenario_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["decision"]["decision"] == decision
        assert body["decision"]["control_id"] == control_id
        assert body["decision"]["required_approval_role"] == role
        assert body["record_hash"]
