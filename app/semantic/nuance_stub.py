"""Visibly labelled deterministic nuance stub for vulnerability evidence.

This is intentionally a stub, not a model. It maps planted demo phrases to
fixed, bounded vulnerability signals and never makes policy decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

STUB_SOURCE = "nuance_stub"
STUB_VERSION = "stub-0.1"
SCENARIO_4_CONFIDENCE = 0.88
SCENARIO_5_CONFIDENCE = 0.62
NO_VULNERABILITY_CONFIDENCE = 0.0

_DECISION_LIKE_KEYS = frozenset(
    {
        "decision",
        "allow",
        "block",
        "escalate",
        "approval",
        "approved",
        "enforcement",
        "executed",
        "required_approval_role",
        "control_id",
    }
)


@dataclass(frozen=True)
class NuanceStubResult:
    """Bounded vulnerability signal from the labelled nuance stub."""

    present: bool
    confidence: float
    categories: list[str]
    source: str = STUB_SOURCE

    def as_dict(self) -> dict[str, Any]:
        """Return schema-compatible vulnerability indicators."""
        return {
            "present": self.present,
            "confidence": self.confidence,
            "categories": list(self.categories),
            "source": self.source,
        }


def classify_vulnerability(text: str | None) -> NuanceStubResult:
    """Classify planted demo phrases with deterministic fixed confidences.

    The stub is deliberately phrase-based and labelled. It returns evidence
    only: no decision-like fields are ever emitted.
    """
    body = (text or "").casefold()

    if _contains_scenario_4_signal(body):
        return NuanceStubResult(
            present=True,
            confidence=SCENARIO_4_CONFIDENCE,
            categories=["financial_vulnerability", "health"],
        )

    if "struggling a bit since losing my job" in body:
        return NuanceStubResult(
            present=True,
            confidence=SCENARIO_5_CONFIDENCE,
            categories=["financial_vulnerability"],
        )

    return NuanceStubResult(present=False, confidence=NO_VULNERABILITY_CONFIDENCE, categories=[])


def sensor_versions() -> dict[str, str]:
    """Return the visible stub version label for Evidence.sensor_versions."""
    return {STUB_SOURCE: STUB_VERSION}


def assert_no_decision_fields(result: dict[str, Any]) -> None:
    """Developer guard used by tests to ensure this stub remains evidence-only."""
    forbidden = _DECISION_LIKE_KEYS.intersection(result)
    if forbidden:
        raise AssertionError(f"Nuance stub emitted decision-like fields: {sorted(forbidden)}")


def _contains_scenario_4_signal(body: str) -> bool:
    return (
        "can't afford repayments" in body
        and ("cancer diagnosis" in body or "nhs number" in body or "health" in body)
    )
