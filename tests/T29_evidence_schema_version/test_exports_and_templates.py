"""T29 export and template tests.

Verifies that evidence_schema_version appears in:
- the per-record JSON export
- the printable HTML export
- the record view page
- the audit log page framing
- DEMO_SCRIPT.md Beat 9 narration
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.pipeline as pipeline_module
from app.audit.store import AuditStore, EVIDENCE_SCHEMA_VERSION
from app.main import app
from app.schemas.action import Action
from app.schemas.audit import RecordType
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence
from app.settings_store import SettingsStore

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _action(correlation_id: uuid.UUID | None = None) -> Action:
    return Action(
        action_id=uuid.uuid4(),
        correlation_id=correlation_id or uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        action_type="financial.payment.issue",
        actor={"agent_id": "agent-1", "agent_owner": "ops", "role": "clerk"},
        tool="payment_tool",
        target_system="payment_system",
        resource={"type": "customer", "id": "CUST-100"},
        parameters={"amount_gbp": 80},
        content=None,
        recipient=None,
        environment="demo",
        enforcement_mode="full",
    )


def _context() -> Context:
    return Context(
        customer={
            "id": "CUST-100",
            "status": "normal",
            "vulnerability_flag": False,
            "fraud_flag": False,
            "sanctions_match": False,
            "account_age_days": 365,
        },
        payment_history={"count_30d": 0, "total_30d_gbp": 0, "last_payment_date": None},
        approval_state={"has_approval": False, "approver": None, "approval_id": None},
        recipient={"is_external": False, "domain": None, "approved_disclosure_basis": False},
        affects_individual_financial_standing=True,
        business_hours=True,
        context_resolution_ok=True,
    )


def _evidence() -> Evidence:
    return Evidence(
        evaluated=False,
        contains_personal_data=False,
        contains_special_category_data=False,
        sensitivity_level="low",
        detected_entities=[],
        evidence_spans=[],
        vulnerability_indicators={"present": False, "confidence": 0.0, "categories": [], "source": "nuance_stub"},
        overall_confidence=0.0,
        sensor_versions={"presidio": "2.2.355", "nuance_stub": "stub-0.1"},
        sensor_error=False,
    )


def _decision() -> Decision:
    return Decision(
        decision="allow",
        control_id=None,
        triggered_controls=[],
        reason="test reason",
        required_approval_role=None,
        framework_mappings=[],
        failure_mode="fail_closed",
        logging_requirements="standard",
        policy_version="v1",
        threshold_used=0.75,
    )


@pytest.fixture
def store_with_record(tmp_path):
    """An AuditStore pre-populated with one action_evaluation record."""
    store = AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")
    action = _action()
    record = store.write_record(
        action=action,
        context_used=_context(),
        evidence=_evidence(),
        decision=_decision(),
        enforcement_mode="full",
        executed=True,
        record_type="action_evaluation",
    )
    return store, record


@pytest.fixture
def patched_pipeline(tmp_path, monkeypatch, store_with_record):
    """Patch the global pipeline to use our pre-populated SQLite store."""
    store, record = store_with_record
    settings_store = SettingsStore(f"sqlite:///{tmp_path / 'settings.db'}")
    pipe = pipeline_module.PolicyPipeline(
        settings_store=settings_store,
        audit_store=store,
        opa_url="http://localhost:18181",  # not contacted by record view tests
    )
    monkeypatch.setattr(pipeline_module, "_default_pipeline", pipe)
    return pipe, record


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_record_json_export_includes_schema_version(patched_pipeline):
    """Per-record JSON export must contain evidence_schema_version at the top level."""
    _, record = patched_pipeline
    client = TestClient(app)

    response = client.get(f"/records/{record.record_hash}/export.json")
    assert response.status_code == 200

    payload = response.json()
    assert "evidence_schema_version" in payload, "JSON export must include evidence_schema_version"
    assert payload["evidence_schema_version"] == EVIDENCE_SCHEMA_VERSION

    # Existing fields must remain
    for field in ("record_hash", "prev_hash", "action", "evidence", "decision"):
        assert field in payload, f"Expected field {field!r} still present in JSON export"


def test_printable_record_html_export_displays_schema_version(patched_pipeline):
    """Printable HTML export must show a human-readable evidence schema version label."""
    _, record = patched_pipeline
    client = TestClient(app)

    response = client.get(f"/records/{record.record_hash}/export.html")
    assert response.status_code == 200
    assert "html" in response.headers["content-type"]

    body = response.text
    assert "Evidence schema version" in body, "Printable HTML export must contain 'Evidence schema version' label"
    assert EVIDENCE_SCHEMA_VERSION in body, "Printable HTML export must show the version value"

    # Chain fields must still be present
    assert record.record_hash in body
    assert record.prev_hash in body


def test_record_page_displays_schema_version(patched_pipeline):
    """Interactive record view page must display the evidence schema version."""
    _, record = patched_pipeline
    client = TestClient(app)

    response = client.get(f"/records/{record.record_hash}")
    assert response.status_code == 200

    body = response.text
    assert "Evidence schema version" in body, "Record page must show 'Evidence schema version' label"
    assert EVIDENCE_SCHEMA_VERSION in body

    # Export links must remain
    assert f"/records/{record.record_hash}/export.json" in body
    assert f"/records/{record.record_hash}/export.html" in body


def test_audit_log_page_mentions_schema_versioning(patched_pipeline):
    """Audit log page must surface schema-versioning framing for reviewers."""
    client = TestClient(app)

    response = client.get("/audit")
    assert response.status_code == 200

    body = response.text
    assert any(
        phrase in body
        for phrase in ("evidence schema version", "schema version", "evidence_schema_version")
    ), "Audit log page must mention evidence schema versioning to buyers"


def test_demo_script_beat_9_mentions_schema_versioning_without_reordering_beats():
    """DEMO_SCRIPT.md Beat 9 must include schema-versioning narration; beat order intact."""
    text = (REPO_ROOT / "DEMO_SCRIPT.md").read_text(encoding="utf-8")

    # Locate Beat 9 section
    beat9_start = text.find("## Beat 9")
    assert beat9_start >= 0, "DEMO_SCRIPT.md must contain a Beat 9 section"

    beat10_start = text.find("## Beat 10")
    beat9_text = text[beat9_start:beat10_start] if beat10_start > 0 else text[beat9_start:]

    assert any(
        phrase in beat9_text
        for phrase in ("evidence schema version", "schema version", "versioned", "version")
    ), "Beat 9 must mention evidence schema versioning"

    # Beat ordering must remain intact
    assert text.find("## Beat 0") < text.find("## Beat 1") < text.find("## Beat 9") < text.find("## Beat 10")
