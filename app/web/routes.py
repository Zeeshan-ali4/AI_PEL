"""JSON routes for the T13 integration milestone."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.pipeline import UnknownScenarioError, get_pipeline

router = APIRouter()


@router.post("/run/{scenario_id}")
def run_scenario(scenario_id: int) -> dict:
    """Run one canonical scenario through the full policy pipeline."""

    try:
        result = get_pipeline().run_scenario(scenario_id)
    except UnknownScenarioError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return result.response_payload()
