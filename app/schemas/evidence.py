"""Canonical Evidence schema for bounded sensor output only."""

from enum import StrEnum

from pydantic import BaseModel, Field


class SensitivityLevel(StrEnum):
    """Overall sensitivity level reported by sensors."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EntitySource(StrEnum):
    """Supported deterministic entity-detection source."""

    PRESIDIO = "presidio"


class VulnerabilityCategory(StrEnum):
    """Supported vulnerability-indicator categories from the labelled stub."""

    FINANCIAL_VULNERABILITY = "financial_vulnerability"
    HEALTH = "health"
    COERCION = "coercion"


class VulnerabilitySource(StrEnum):
    """Supported vulnerability-indicator source."""

    NUANCE_STUB = "nuance_stub"


class DetectedEntity(BaseModel):
    """Entity detected in content by a deterministic sensor."""

    type: str = Field(..., description="Entity type reported by the sensor.")
    score: float = Field(..., description="Sensor confidence score for the entity.")
    source: EntitySource = Field(..., description="Sensor that produced this entity.")


class EvidenceSpan(BaseModel):
    """Character span supporting a piece of sensor evidence."""

    start: int = Field(..., description="Inclusive start character offset.")
    end: int = Field(..., description="Exclusive end character offset.")
    label: str = Field(..., description="Plain-English label for the span.")


class VulnerabilityIndicators(BaseModel):
    """Bounded vulnerability signals from the visibly labelled nuance stub."""

    present: bool = Field(..., description="Whether vulnerability indicators were detected.")
    confidence: float = Field(..., ge=0, le=1, description="Stub confidence in the 0..1 range.")
    categories: list[VulnerabilityCategory] = Field(..., description="Detected vulnerability categories.")
    source: VulnerabilitySource = Field(..., description="Labelled source of the vulnerability signal.")


class Evidence(BaseModel):
    """Sensor evidence for policy evaluation; never a policy decision."""

    evaluated: bool = Field(..., description="False when semantic sensors were intentionally skipped.")
    contains_personal_data: bool = Field(..., description="Whether personal data was detected.")
    contains_special_category_data: bool = Field(..., description="Whether special-category data was detected.")
    sensitivity_level: SensitivityLevel = Field(..., description="Overall sensitivity level inferred from sensors.")
    detected_entities: list[DetectedEntity] = Field(..., description="Detected entities from deterministic sensors.")
    evidence_spans: list[EvidenceSpan] = Field(..., description="Character spans supporting the evidence.")
    vulnerability_indicators: VulnerabilityIndicators = Field(..., description="Bounded vulnerability signals from the stub.")
    overall_confidence: float = Field(..., ge=0, le=1, description="Overall sensor confidence in the 0..1 range.")
    sensor_versions: dict[str, str] = Field(..., description="Versions of sensors that produced this evidence.")
    sensor_error: bool = Field(..., description="True when a required sensor failed.")
