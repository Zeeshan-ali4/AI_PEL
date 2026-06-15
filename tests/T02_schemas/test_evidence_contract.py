from app.schemas.action import Action
from app.schemas.audit import EvidenceRecord
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence


def test_evidence_model_has_no_decision_or_enforcement_fields():
    expected = {
        "evaluated",
        "contains_personal_data",
        "contains_special_category_data",
        "sensitivity_level",
        "detected_entities",
        "evidence_spans",
        "vulnerability_indicators",
        "overall_confidence",
        "sensor_versions",
        "sensor_error",
    }
    forbidden = {
        "allow", "block", "decision", "approval", "approved", "enforcement", "executed",
        "control_id", "triggered_controls", "required_approval_role", "failure_mode", "policy_version",
    }
    fields = set(Evidence.model_fields)
    assert fields == expected
    assert not any(forbidden_name in field for field in fields for forbidden_name in forbidden)


def test_model_imports_are_clean():
    assert Action and Context and Evidence and Decision and EvidenceRecord
