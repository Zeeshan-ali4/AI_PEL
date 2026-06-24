"""Live-count and auditable-surface counter tests for the T14 dashboard."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from tests.T14_dashboard.conftest import write_action_evaluation


def test_dashboard_live_counts_initially_show_zero_when_audit_store_empty(wired_pipeline):
    html = TestClient(app).get("/").text

    assert wired_pipeline.audit_store.read_records() == []
    assert "0 consequential action" in html
    # Zero counts render visibly for every outcome column, not just hidden JSON.
    assert html.count(">0<") >= 4


def test_dashboard_live_counts_update_after_running_scenarios(wired_pipeline, opa_url):
    wired_pipeline.opa_url = opa_url
    client = TestClient(app)

    assert client.post("/run/3").status_code == 200  # block / FIN-PAY-001
    assert client.post("/run/6").status_code == 200  # allow_with_logging / COMM-EMAIL-003

    html = client.get("/").text

    records = wired_pipeline.audit_store.read_records()
    assert len(records) == 2
    assert "2 consequential action" in html

    rows_by_control = {
        record.decision.control_id: record.decision.decision for record in records
    }
    assert rows_by_control["FIN-PAY-001"] == "block"
    assert rows_by_control["COMM-EMAIL-003"] == "allow_with_logging"


def test_dashboard_auditable_surface_counter_explains_gate_not_agent_logging(wired_pipeline):
    write_action_evaluation(wired_pipeline.audit_store, decision="allow", control_id=None)

    html = TestClient(app).get("/").text

    assert "auditable surface" in html.lower()
    assert "gate" in html.lower()
    assert "proposed consequential actions" in html.lower() or "consequential action" in html.lower()
    assert "complete, unauditable agent transcript" in html
