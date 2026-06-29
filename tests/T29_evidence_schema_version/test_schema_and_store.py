"""T29 schema and store tests.

Verifies that:
- EvidenceRecord model has evidence_schema_version
- write_record populates the field for action_evaluation records
- write_record populates the field for approval_decision records
- audit package includes the field for every record
- hash chain stays intact
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import pydantic

from app.audit.store import AuditStore, EVIDENCE_SCHEMA_VERSION
from app.schemas.action import Action
from app.schemas.audit import EvidenceRecord
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence


# ---------------------------------------------------------------------------
# Shared sample builders (mirrors tests/T12_audit/conftest.py)
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


def _decision(decision: str = "allow") -> Decision:
    return Decision(
        decision=decision,
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
def store(tmp_path):
    return AuditStore(f"sqlite:///{tmp_path / 'audit.db'}")


# ---------------------------------------------------------------------------
# Schema model tests
# ---------------------------------------------------------------------------

def test_evidence_record_model_has_schema_version_field():
    """EvidenceRecord must declare evidence_schema_version as a required str field."""
    assert "evidence_schema_version" in EvidenceRecord.model_fields
    field_info = EvidenceRecord.model_fields["evidence_schema_version"]
    assert field_info.annotation is str or str in getattr(field_info.annotation, "__args__", ())


def test_evidence_record_serializes_schema_version():
    """A valid EvidenceRecord must include evidence_schema_version in model_dump output."""
    action = _action()
    record = EvidenceRecord(
        id=1,
        correlation_id=action.correlation_id,
        action=action,
        context_used=_context(),
        evidence=_evidence(),
        decision=_decision(),
        enforcement_mode="full",
        executed=True,
        record_type="action_evaluation",
        references_hash=None,
        human_approver=None,
        approval_reason=None,
        created_at=datetime.now(timezone.utc),
        record_hash="a" * 64,
        prev_hash="0" * 64,
        evidence_schema_version=EVIDENCE_SCHEMA_VERSION,
    )
    dumped = record.model_dump(mode="json")
    assert "evidence_schema_version" in dumped
    assert dumped["evidence_schema_version"] == EVIDENCE_SCHEMA_VERSION


def test_omitting_schema_version_raises_validation_error():
    """Constructing EvidenceRecord without evidence_schema_version must raise ValidationError."""
    action = _action()
    with pytest.raises(pydantic.ValidationError):
        EvidenceRecord(
            id=1,
            correlation_id=action.correlation_id,
            action=action,
            context_used=_context(),
            evidence=_evidence(),
            decision=_decision(),
            enforcement_mode="full",
            executed=True,
            record_type="action_evaluation",
            references_hash=None,
            human_approver=None,
            approval_reason=None,
            created_at=datetime.now(timezone.utc),
            record_hash="a" * 64,
            prev_hash="0" * 64,
            # evidence_schema_version deliberately omitted
        )


# ---------------------------------------------------------------------------
# Store write tests
# ---------------------------------------------------------------------------

def test_write_record_populates_schema_version_for_action_evaluation(store):
    """write_record must populate evidence_schema_version on action_evaluation records."""
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

    assert record.evidence_schema_version == EVIDENCE_SCHEMA_VERSION
    assert record.evidence_schema_version != ""

    persisted = store.read_records()
    assert len(persisted) == 1
    assert persisted[0].evidence_schema_version == EVIDENCE_SCHEMA_VERSION

    chain = store.verify_chain()
    assert chain.intact is True


def test_write_record_populates_schema_version_for_approval_decision(store):
    """write_record must populate evidence_schema_version on approval_decision records too."""
    action = _action()
    original = store.write_record(
        action=action,
        context_used=_context(),
        evidence=_evidence(),
        decision=_decision("escalate"),
        enforcement_mode="full",
        executed=False,
        record_type="action_evaluation",
    )

    approval = store.write_record(
        action=action,
        context_used=_context(),
        evidence=_evidence(),
        decision=_decision("escalate"),
        enforcement_mode="full",
        executed=True,
        record_type="approval_decision",
        correlation_id=action.correlation_id,
        references_hash=original.record_hash,
        human_approver="finance_supervisor",
        approval_reason="Approved — legitimate high-value refund",
    )

    assert approval.evidence_schema_version == EVIDENCE_SCHEMA_VERSION
    assert approval.record_type == "approval_decision"
    assert approval.references_hash == original.record_hash
    assert approval.human_approver == "finance_supervisor"

    records = store.read_records()
    assert all(r.evidence_schema_version == EVIDENCE_SCHEMA_VERSION for r in records)

    chain = store.verify_chain()
    assert chain.intact is True


def test_audit_package_json_includes_schema_version_for_every_record(store):
    """export_audit_package must include evidence_schema_version in every record."""
    action = _action()
    original = store.write_record(
        action=action,
        context_used=_context(),
        evidence=_evidence(),
        decision=_decision("escalate"),
        enforcement_mode="full",
        executed=False,
        record_type="action_evaluation",
    )
    store.write_record(
        action=action,
        context_used=_context(),
        evidence=_evidence(),
        decision=_decision("escalate"),
        enforcement_mode="full",
        executed=True,
        record_type="approval_decision",
        correlation_id=action.correlation_id,
        references_hash=original.record_hash,
        human_approver="finance_supervisor",
        approval_reason="Approved",
    )

    package = store.export_audit_package(correlation_id=action.correlation_id)

    # T25 structural fields must be intact
    assert "header" in package
    assert "selection" in package
    assert "chain_links" in package
    assert "records" in package
    assert "package_integrity_hash" in package

    # Every record in the package must carry the schema version
    for rec in package["records"]:
        assert "evidence_schema_version" in rec, f"Missing evidence_schema_version in record: {rec.get('id')}"
        assert rec["evidence_schema_version"] == EVIDENCE_SCHEMA_VERSION

    # Chain links must show at least one intact link
    assert any(link["link_intact"] for link in package["chain_links"])
