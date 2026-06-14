import pytest
from pydantic import ValidationError

from app.schemas.action import Action
from app.schemas.audit import EvidenceRecord
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence
from tests.T02_schemas.test_schema_examples import context, decision, evidence, payment_action, record


def assert_invalid(factory):
    with pytest.raises(ValidationError):
        factory()


@pytest.mark.parametrize(
    ("factory", "field", "bad"),
    [
        (payment_action, "action_type", "unknown.tool"),
        (payment_action, "environment", "qa"),
        (payment_action, "enforcement_mode", "monitor"),
    ],
)
def test_action_closed_value_enums_reject_invalid_values(factory, field, bad):
    data = factory().model_dump()
    data[field] = bad
    assert_invalid(lambda: Action(**data))


def test_context_closed_value_enums_reject_invalid_values():
    data = context().model_dump()
    data["customer"]["status"] = "vip"
    assert_invalid(lambda: Context(**data))


@pytest.mark.parametrize(
    ("path", "bad"),
    [
        (("sensitivity_level",), "critical"),
        (("detected_entities", 0, "source"), "manual"),
        (("vulnerability_indicators", "categories"), ["unknown"]),
        (("vulnerability_indicators", "source"), "llm"),
    ],
)
def test_evidence_closed_value_enums_reject_invalid_values(path, bad):
    data = evidence(True).model_dump()
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = bad
    assert_invalid(lambda: Evidence(**data))


@pytest.mark.parametrize("field,bad", [("decision", "approve"), ("failure_mode", "ignore"), ("logging_requirements", "verbose")])
def test_decision_closed_value_enums_reject_invalid_values(field, bad):
    data = decision().model_dump()
    data[field] = bad
    assert_invalid(lambda: Decision(**data))


def test_record_type_enum_rejects_invalid_values():
    data = record().model_dump()
    data["record_type"] = "mutation"
    assert_invalid(lambda: EvidenceRecord(**data))


@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_confidence_and_threshold_ranges_are_enforced(value):
    ev = evidence(True).model_dump()
    ev["vulnerability_indicators"]["confidence"] = value
    assert_invalid(lambda: Evidence(**ev))

    ev = evidence(True).model_dump()
    ev["overall_confidence"] = value
    assert_invalid(lambda: Evidence(**ev))

    dec = decision().model_dump()
    dec["threshold_used"] = value
    assert_invalid(lambda: Decision(**dec))


def test_hash_fields_validate_sha256_hex_shape():
    record(record_hash="a" * 64, prev_hash="b" * 64, references_hash="c" * 64)
    for field, bad in [("record_hash", "a" * 63), ("prev_hash", "b" * 65), ("references_hash", "g" * 64)]:
        data = record().model_dump()
        data[field] = bad
        assert_invalid(lambda: EvidenceRecord(**data))


@pytest.mark.parametrize(
    ("factory", "field"),
    [
        (payment_action, "action_id"),
        (context, "customer"),
        (evidence, "evaluated"),
        (decision, "decision"),
        (record, "record_hash"),
    ],
)
def test_required_spec_fields_are_not_optional(factory, field):
    data = factory().model_dump()
    data.pop(field)
    model_class = {
        "action_id": Action,
        "customer": Context,
        "evaluated": Evidence,
        "decision": Decision,
        "record_hash": EvidenceRecord,
    }[field]
    assert_invalid(lambda: model_class(**data))
