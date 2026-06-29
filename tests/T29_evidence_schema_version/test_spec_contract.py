"""T29 spec-contract tests.

Verifies that MASTER_SPEC.md has been updated (spec-first discipline) and
that the Evidence schema boundary is intact.
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def _master_spec_text() -> str:
    return (REPO_ROOT / "MASTER_SPEC.md").read_text(encoding="utf-8")


def test_spec_documents_evidence_schema_version_and_bumps_status():
    """MASTER_SPEC.md must be bumped past v1.1 and document evidence_schema_version in §5.5."""
    text = _master_spec_text()

    # Status line must be bumped beyond v1.1
    assert "v1.2" in text, "MASTER_SPEC.md status must be bumped to at least v1.2"

    # Change log area must mention schema versioning
    assert any(
        phrase in text
        for phrase in ("evidence_schema_version", "schema version", "schema versioning")
    ), "MASTER_SPEC.md must mention evidence schema versioning in the change log"

    # §5.5 Evidence Record JSON block must contain the field
    assert "evidence_schema_version" in text, (
        "MASTER_SPEC.md §5.5 EvidenceRecord must include the evidence_schema_version field"
    )


def test_evidence_schema_still_has_no_decision_or_enforcement_fields():
    """Evidence Pydantic model must not have any decision/enforcement/approval fields."""
    from app.schemas.evidence import Evidence

    forbidden_fields = {
        "allow", "block", "decision", "approval", "approved",
        "enforcement", "executed", "evidence_schema_version",
    }
    model_field_names = set(Evidence.model_fields.keys())
    violations = forbidden_fields & model_field_names
    assert not violations, (
        f"Evidence schema must not contain decision/enforcement fields; found: {violations}"
    )
