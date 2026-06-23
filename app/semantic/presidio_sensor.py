"""Real Presidio-backed deterministic sensor for raw email evidence.

This module intentionally returns raw analyzer findings only. It does not make
policy decisions, infer enforcement outcomes, or populate the final Evidence
schema; T07 assembles those higher-level evidence fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from typing import Any

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider

NHS_NUMBER_ENTITY = "UK_NHS_NUMBER"
HEALTH_KEYWORD_ENTITY = "HEALTH_INFORMATION"
DEFAULT_LANGUAGE = "en"


@dataclass(frozen=True)
class PresidioFinding:
    """Raw finding adapter around a Presidio RecognizerResult."""

    type: str
    score: float
    start: int
    end: int
    source: str = "presidio"

    @property
    def label(self) -> str:
        return self.type

    def as_entity(self) -> dict[str, Any]:
        return {"type": self.type, "score": self.score, "source": self.source}

    def as_span(self) -> dict[str, Any]:
        return {"start": self.start, "end": self.end, "label": self.type}

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "label": self.type,
            "score": self.score,
            "source": self.source,
            "start": self.start,
            "end": self.end,
        }


class PresidioSensor:
    """Thin wrapper around Presidio AnalyzerEngine for email-body scanning."""

    def __init__(self, analyzer: AnalyzerEngine | None = None) -> None:
        self.analyzer = analyzer or _build_analyzer()

    def analyze(self, text: str | None) -> dict[str, Any]:
        """Return raw Presidio findings and spans for original text offsets."""
        body = text or ""
        if not body.strip():
            return _empty_result()

        results = self.analyzer.analyze(text=body, language=DEFAULT_LANGUAGE)
        findings = [_finding_from_result(result) for result in _sort_results(results)]
        return {
            "entities": [finding.as_dict() for finding in findings],
            "detected_entities": [finding.as_entity() for finding in findings],
            "evidence_spans": [finding.as_span() for finding in findings],
            "sensor_versions": {"presidio": _presidio_version()},
        }


def analyze_text(text: str | None) -> dict[str, Any]:
    """Convenience function for callers that do not need to manage a sensor."""
    return PresidioSensor().analyze(text)


def _build_analyzer() -> AnalyzerEngine:
    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": DEFAULT_LANGUAGE, "model_name": "en_core_web_sm"}],
        }
    )
    analyzer = AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=[DEFAULT_LANGUAGE])
    analyzer.registry.add_recognizer(_nhs_number_recognizer())
    analyzer.registry.add_recognizer(_health_keyword_recognizer())
    return analyzer


def _nhs_number_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity=NHS_NUMBER_ENTITY,
        name="uk_nhs_number_recognizer",
        patterns=[
            Pattern(
                name="uk_nhs_number_with_spaces",
                regex=r"(?<!\d)\d{3}\s\d{3}\s\d{4}(?!\d)",
                score=0.85,
            ),
            Pattern(
                name="uk_nhs_number_compact",
                regex=r"(?<!\d)\d{10}(?!\d)",
                score=0.65,
            ),
        ],
        context=["nhs", "number", "health", "patient"],
        supported_language=DEFAULT_LANGUAGE,
    )


def _health_keyword_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity=HEALTH_KEYWORD_ENTITY,
        name="health_keyword_recognizer",
        patterns=[
            Pattern(
                name="health_special_category_terms",
                regex=r"(?i)\b(cancer diagnosis|diagnosis|health condition|medical condition|patient)\b",
                score=0.7,
            )
        ],
        context=["health", "medical", "diagnosis", "condition"],
        supported_language=DEFAULT_LANGUAGE,
    )


def _finding_from_result(result: RecognizerResult) -> PresidioFinding:
    return PresidioFinding(
        type=result.entity_type,
        score=max(0.0, min(1.0, float(result.score))),
        start=int(result.start),
        end=int(result.end),
    )


def _sort_results(results: list[RecognizerResult]) -> list[RecognizerResult]:
    return sorted(results, key=lambda result: (result.start, result.end, result.entity_type))


def _empty_result() -> dict[str, Any]:
    return {
        "entities": [],
        "detected_entities": [],
        "evidence_spans": [],
        "sensor_versions": {"presidio": _presidio_version()},
    }


def _presidio_version() -> str:
    try:
        return metadata.version("presidio-analyzer")
    except metadata.PackageNotFoundError:
        return "unknown"
