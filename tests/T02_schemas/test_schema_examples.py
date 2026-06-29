from datetime import date, datetime, timezone
from uuid import UUID

from app.schemas.action import Action
from app.schemas.audit import EvidenceRecord
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence

ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
TWO_HASH = "2" * 64
ACTION_ID = UUID("11111111-1111-1111-1111-111111111111")
CORRELATION_ID = UUID("22222222-2222-2222-2222-222222222222")
NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def payment_action() -> Action:
    return Action(
        action_id=ACTION_ID,
        correlation_id=CORRELATION_ID,
        timestamp=NOW,
        action_type="financial.payment.issue",
        actor={"agent_id": "agent-1", "agent_owner": "ops", "role": "contact_centre_agent"},
        tool="issue_payment",
        target_system="payments",
        resource={"type": "customer", "id": "CUST-100"},
        parameters={"amount_gbp": 125.50},
        content=None,
        recipient=None,
        environment="demo",
        enforcement_mode="full",
    )


def email_action() -> Action:
    return Action(
        action_id=ACTION_ID,
        correlation_id=CORRELATION_ID,
        timestamp=NOW,
        action_type="communication.email.send",
        actor={"agent_id": "agent-1", "agent_owner": "ops", "role": "contact_centre_agent"},
        tool="send_email",
        target_system="email",
        resource={"type": "customer", "id": "CUST-100"},
        parameters={"subject": "Update"},
        content="Hello, here is your update.",
        recipient="external@example.com",
        environment="demo",
        enforcement_mode="shadow",
    )


def context() -> Context:
    return Context(
        customer={
            "id": "CUST-100",
            "status": "normal",
            "vulnerability_flag": False,
            "fraud_flag": False,
            "sanctions_match": False,
            "account_age_days": 400,
        },
        payment_history={"count_30d": 1, "total_30d_gbp": 125.5, "last_payment_date": date(2026, 1, 1)},
        approval_state={"has_approval": False, "approver": None, "approval_id": None},
        recipient={"is_external": True, "domain": None, "approved_disclosure_basis": False},
        affects_individual_financial_standing=True,
        business_hours=True,
        context_resolution_ok=True,
    )


def evidence(evaluated: bool = True) -> Evidence:
    return Evidence(
        evaluated=evaluated,
        contains_personal_data=evaluated,
        contains_special_category_data=evaluated,
        sensitivity_level="high" if evaluated else "low",
        detected_entities=[{"type": "EMAIL_ADDRESS", "score": 0.91, "source": "presidio"}] if evaluated else [],
        evidence_spans=[{"start": 0, "end": 5, "label": "email"}] if evaluated else [],
        vulnerability_indicators={
            "present": evaluated,
            "confidence": 0.88 if evaluated else 0,
            "categories": ["health"] if evaluated else [],
            "source": "nuance_stub",
        },
        overall_confidence=0.88 if evaluated else 0,
        sensor_versions={"presidio": "2.x", "nuance_stub": "stub-0.1"},
        sensor_error=False,
    )


def decision() -> Decision:
    return Decision(
        decision="escalate",
        control_id="FIN-PAY-002",
        triggered_controls=["FIN-PAY-002"],
        reason="Payment requires approval.",
        required_approval_role="finance_supervisor",
        framework_mappings=["Internal Delegated-Authority Policy"],
        failure_mode="fail_closed",
        logging_requirements="enhanced",
        policy_version="demo-0.1",
        threshold_used=0.75,
    )


def record(**overrides) -> EvidenceRecord:
    data = dict(
        id=1,
        correlation_id=CORRELATION_ID,
        action=payment_action(),
        context_used=context(),
        evidence=evidence(False),
        decision=decision(),
        enforcement_mode="full",
        executed=False,
        record_type="action_evaluation",
        references_hash=None,
        human_approver=None,
        approval_reason=None,
        created_at=NOW,
        record_hash=ONE_HASH,
        prev_hash=ZERO_HASH,
        evidence_schema_version="1.0.0",
    )
    data.update(overrides)
    return EvidenceRecord(**data)


def test_action_accepts_spec_compliant_payment_example():
    dumped = payment_action().model_dump()
    assert set(dumped) == {
        "action_id", "correlation_id", "timestamp", "action_type", "actor", "tool", "target_system",
        "resource", "parameters", "content", "recipient", "environment", "enforcement_mode"
    }


def test_action_accepts_spec_compliant_email_example():
    action = email_action()
    assert action.content == "Hello, here is your update."
    assert action.recipient == "external@example.com"


def test_context_accepts_spec_compliant_example():
    model = context()
    assert model.customer.status == "normal"
    assert model.approval_state.approver is None
    assert model.recipient.domain is None


def test_evidence_accepts_spec_compliant_email_sensor_example():
    model = evidence(True)
    assert model.detected_entities[0].source == "presidio"
    assert model.vulnerability_indicators.source == "nuance_stub"


def test_evidence_accepts_payment_path_not_evaluated_example():
    model = evidence(False)
    assert model.evaluated is False
    assert model.detected_entities == []


def test_decision_accepts_spec_compliant_escalation_example():
    model = decision()
    assert model.threshold_used == 0.75


def test_evidence_record_accepts_action_evaluation_example():
    model = record()
    dumped = model.model_dump()
    assert {"action", "context_used", "evidence", "decision"}.issubset(dumped)
    assert model.references_hash is None


def test_evidence_record_accepts_approval_decision_reference_example():
    model = record(record_type="approval_decision", references_hash=TWO_HASH, human_approver="Jane", approval_reason="Valid need")
    assert model.references_hash == TWO_HASH
    assert model.human_approver == "Jane"
