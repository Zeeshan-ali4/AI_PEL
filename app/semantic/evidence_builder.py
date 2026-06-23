"""Build canonical Evidence from Presidio output and the labelled nuance stub."""

from __future__ import annotations

from typing import Any

from app.schemas.action import Action, ActionType
from app.schemas.evidence import Evidence
from app.semantic import nuance_stub, presidio_sensor
from app.semantic.presidio_sensor import HEALTH_KEYWORD_ENTITY, NHS_NUMBER_ENTITY

PRESIDIO_VERSION_KEY = "presidio"
UNKNOWN_SENSOR_VERSION = "unknown"


def build_evidence(action: Action) -> Evidence:
    """Assemble bounded Evidence for a normalised action.

    Email actions run Presidio first and then the labelled nuance stub. Payment
    actions intentionally skip both semantic sensors and return
    ``evaluated=false`` evidence. Sensor exceptions are converted into
    ``sensor_error=true`` so the later policy engine can fail closed.
    """
    if action.action_type != ActionType.COMMUNICATION_EMAIL_SEND:
        return _payment_skip_evidence()

    text = _action_text(action)
    try:
        presidio_result = presidio_sensor.analyze_text(text)
        stub_result = nuance_stub.classify_vulnerability(text)
    except Exception:
        return _sensor_error_evidence(evaluated=True)

    detected_entities = list(presidio_result.get("detected_entities", []))
    evidence_spans = list(presidio_result.get("evidence_spans", []))
    entities = list(presidio_result.get("entities", []))
    vulnerability = stub_result.as_dict()

    contains_personal_data = bool(detected_entities or evidence_spans)
    contains_special_category_data = _contains_special_category(entities, evidence_spans)
    sensitivity_level = _sensitivity_level(
        contains_personal_data=contains_personal_data,
        contains_special_category_data=contains_special_category_data,
        vulnerability_present=bool(vulnerability["present"]),
    )

    sensor_versions = _sensor_versions(presidio_result)
    overall_confidence = float(vulnerability["confidence"]) if vulnerability["present"] else _max_presidio_score(detected_entities)

    return Evidence(
        evaluated=True,
        contains_personal_data=contains_personal_data,
        contains_special_category_data=contains_special_category_data,
        sensitivity_level=sensitivity_level,
        detected_entities=detected_entities,
        evidence_spans=evidence_spans,
        vulnerability_indicators=vulnerability,
        overall_confidence=overall_confidence,
        sensor_versions=sensor_versions,
        sensor_error=False,
    )


def _payment_skip_evidence() -> Evidence:
    return Evidence(
        evaluated=False,
        contains_personal_data=False,
        contains_special_category_data=False,
        sensitivity_level="low",
        detected_entities=[],
        evidence_spans=[],
        vulnerability_indicators=_empty_vulnerability(),
        overall_confidence=0.0,
        sensor_versions=_sensor_versions({}),
        sensor_error=False,
    )


def _sensor_error_evidence(*, evaluated: bool) -> Evidence:
    return Evidence(
        evaluated=evaluated,
        contains_personal_data=False,
        contains_special_category_data=False,
        sensitivity_level="low",
        detected_entities=[],
        evidence_spans=[],
        vulnerability_indicators=_empty_vulnerability(),
        overall_confidence=0.0,
        sensor_versions=_sensor_versions({}),
        sensor_error=True,
    )


def _action_text(action: Action) -> str:
    if action.content is not None:
        return action.content
    body = action.parameters.get("body")
    return body if isinstance(body, str) else ""


def _empty_vulnerability() -> dict[str, Any]:
    return {
        "present": False,
        "confidence": 0.0,
        "categories": [],
        "source": nuance_stub.STUB_SOURCE,
    }


def _sensor_versions(presidio_result: dict[str, Any]) -> dict[str, str]:
    versions = dict(presidio_result.get("sensor_versions", {}))
    versions.setdefault(PRESIDIO_VERSION_KEY, UNKNOWN_SENSOR_VERSION)
    versions.update(nuance_stub.sensor_versions())
    return versions


def _contains_special_category(entities: list[dict[str, Any]], spans: list[dict[str, Any]]) -> bool:
    special_labels = {NHS_NUMBER_ENTITY, HEALTH_KEYWORD_ENTITY}
    entity_types = {str(entity.get("type")) for entity in entities}
    span_labels = {str(span.get("label")) for span in spans}
    return bool(special_labels & (entity_types | span_labels))


def _sensitivity_level(
    *,
    contains_personal_data: bool,
    contains_special_category_data: bool,
    vulnerability_present: bool,
) -> str:
    if contains_special_category_data:
        return "high"
    if contains_personal_data or vulnerability_present:
        return "medium"
    return "low"


def _max_presidio_score(detected_entities: list[dict[str, Any]]) -> float:
    scores = [float(entity.get("score", 0.0)) for entity in detected_entities]
    return max(scores, default=0.0)
