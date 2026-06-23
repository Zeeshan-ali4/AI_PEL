from app.normaliser.normaliser import normalise
from app.schemas.evidence import Evidence
from app.semantic.evidence_builder import build_evidence
from scenarios.scenarios import get_raw_tool_call
from tests.T07_evidence.test_evidence_builder import _assert_no_decision_fields


def _email_action():
    return normalise(get_raw_tool_call(4))


def test_build_evidence_presidio_exception_returns_valid_sensor_error_evidence(monkeypatch):
    def raise_presidio(_text):
        raise RuntimeError("presidio unavailable")

    monkeypatch.setattr("app.semantic.presidio_sensor.analyze_text", raise_presidio)

    evidence = build_evidence(_email_action())

    assert isinstance(evidence, Evidence)
    assert evidence.evaluated is True
    assert evidence.sensor_error is True
    _assert_no_decision_fields(evidence.model_dump(mode="json"))


def test_build_evidence_nuance_exception_returns_valid_sensor_error_evidence(monkeypatch):
    def raise_nuance(_text):
        raise RuntimeError("stub unavailable")

    monkeypatch.setattr("app.semantic.nuance_stub.classify_vulnerability", raise_nuance)

    evidence = build_evidence(_email_action())

    assert isinstance(evidence, Evidence)
    assert evidence.evaluated is True
    assert evidence.sensor_error is True
    assert evidence.detected_entities == []
    assert evidence.evidence_spans == []
    assert evidence.vulnerability_indicators.present is False
    _assert_no_decision_fields(evidence.model_dump(mode="json"))
