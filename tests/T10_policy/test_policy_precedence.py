import pytest

from tests.T10_policy.test_policy_scenarios import OPA, base_action, base_context, evaluate, evidence, payload

pytestmark = pytest.mark.skipif(OPA is None, reason="OPA CLI is not installed")

def test_precedence_fraud_flag_over_large_payment_blocks_not_escalates():
    context = base_context()
    context["customer"]["fraud_flag"] = True
    result = evaluate(payload(base_action("financial.payment.issue", amount=850), context, evidence(evaluated=False)))
    assert "FIN-PAY-001" in result.triggered_controls
    assert "FIN-PAY-002" in result.triggered_controls
    assert result.decision == "block"
    assert result.control_id == "FIN-PAY-001"
    assert result.required_approval_role is None


def test_fail_closed_when_context_resolution_failed():
    context = base_context()
    context["context_resolution_ok"] = False
    result = evaluate(payload(base_action("financial.payment.issue", amount=80), context, evidence(evaluated=False)))
    assert result.decision == "fail_closed"
    assert result.control_id is None
    assert "GLOBAL-FAIL-CLOSED" in result.triggered_controls
    assert result.framework_mappings
    assert result.logging_requirements == "enhanced"
    assert result.failure_mode == "fail_closed"
    assert result.threshold_used == 0.75


def test_fail_closed_when_sensor_error_true():
    result = evaluate(
        payload(
            base_action("communication.email.send"),
            base_context(external=True, disclosure_basis=True),
            evidence(evaluated=True, personal=True, vulnerability=True, confidence=0.62, sensor_error=True),
        )
    )
    assert result.decision == "fail_closed"
    assert result.framework_mappings
    assert result.logging_requirements == "enhanced"
    assert result.failure_mode == "fail_closed"


def test_decision_metadata_is_complete_for_selected_controls():
    cases = [
        payload(base_action("financial.payment.issue", amount=80), base_context(), evidence(evaluated=False)),
        payload(base_action("financial.payment.issue", amount=850), base_context(), evidence(evaluated=False)),
        payload(
            base_action("communication.email.send"),
            base_context(external=True, disclosure_basis=True),
            evidence(evaluated=True, personal=True, confidence=0.85),
        ),
        payload(
            base_action("communication.email.send"),
            base_context(external=True, disclosure_basis=True),
            evidence(evaluated=True, personal=True, confidence=0.85, sensor_error=True),
        ),
    ]
    fraud_context = base_context()
    fraud_context["customer"]["fraud_flag"] = True
    cases.append(payload(base_action("financial.payment.issue", amount=200), fraud_context, evidence(evaluated=False)))

    for case in cases:
        result = evaluate(case)
        assert result.reason
        assert result.policy_version
        assert result.threshold_used == case["config"]["high_confidence_threshold"]
        if result.control_id is not None or result.decision == "fail_closed":
            assert result.framework_mappings
        if result.decision == "escalate":
            assert result.required_approval_role is not None
        else:
            assert result.required_approval_role is None


def test_fin_pay_004_proposed_control_respects_metadata_flag_if_present():
    context = base_context()
    context["affects_individual_financial_standing"] = True
    result = evaluate(payload(base_action("financial.payment.issue", amount=80), context, evidence(evaluated=False)))
    assert "FIN-PAY-004" not in result.triggered_controls
    assert result.decision == "allow"
