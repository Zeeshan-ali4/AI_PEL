"""Routes for the T14 control dashboard plus the T13 JSON scenario endpoint."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.pipeline import UnknownScenarioError, get_pipeline
from app.schemas.audit import RecordType
from app.settings_store import VALID_ENFORCEMENT_MODES

router = APIRouter()

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

STATIC_DIR = Path(__file__).resolve().parent / "static"

CONTROLS_PATH = Path(__file__).resolve().parents[2] / "opa" / "data" / "controls.json"

# Plain-English board labels for the internal decision tiers (spec §6 / §8A item 1).
TIER_LABELS = {
    "prohibited": "Prohibited — hard block",
    "escalate": "Escalate — human decision",
    "allow_with_logging": "Log — allow, with logging",
}

# Maps a binding PDP decision value onto the dashboard's live-count buckets.
DECISION_TO_COUNT_BUCKET = {
    "allow": "allowed",
    "allow_with_logging": "logged",
    "escalate": "escalated",
    "block": "blocked",
}

# Illustrative simulated per-run step count for the §9 auditable-surface counter.
# Not derived from real agent telemetry; the dashboard labels it as such.
AGENT_STEPS_PER_RUN = 14


def _load_enabled_controls() -> dict[str, dict]:
    payload = json.loads(CONTROLS_PATH.read_text())
    return {
        control_id: control
        for control_id, control in payload["controls"].items()
        if control.get("enabled", False)
    }


def _empty_counts() -> dict[str, int]:
    return {"allowed": 0, "escalated": 0, "blocked": 0, "logged": 0}


def _build_control_rows(
    controls: dict[str, dict],
    control_modes: dict[str, str],
    records: list,
) -> tuple[list[dict], int]:
    counts_by_control = {control_id: _empty_counts() for control_id in controls}
    gated_total = 0

    for record in records:
        if record.record_type != RecordType.ACTION_EVALUATION:
            continue
        gated_total += 1
        control_id = record.decision.control_id
        bucket = DECISION_TO_COUNT_BUCKET.get(record.decision.decision)
        if bucket is not None and control_id in counts_by_control:
            counts_by_control[control_id][bucket] += 1

    rows = [
        {
            "id": control_id,
            "description": control["description"],
            "tier": control["tier"],
            "tier_label": TIER_LABELS.get(control["tier"], control["tier"]),
            "framework_mappings": control["framework_mappings"],
            "mode": control_modes.get(control_id, "shadow"),
            "counts": counts_by_control[control_id],
        }
        for control_id, control in sorted(controls.items())
    ]
    return rows, gated_total


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    """Render the board-ready landing control dashboard (spec §8A item 1, §9)."""

    pipeline = get_pipeline()
    settings = pipeline.settings_store.read_settings()
    controls = _load_enabled_controls()
    records = pipeline.audit_store.read_records()
    rows, gated_total = _build_control_rows(controls, settings.control_modes, records)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "rows": rows,
            "gated_total": gated_total,
            "agent_steps_total": gated_total * AGENT_STEPS_PER_RUN,
            "valid_modes": sorted(VALID_ENFORCEMENT_MODES),
        },
    )


@router.post("/mode")
def set_enforcement_mode(mode: str = Form(...)) -> RedirectResponse:
    """Persist the dashboard's enforcement-mode toggle through `SettingsStore`."""

    if mode not in VALID_ENFORCEMENT_MODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid enforcement mode: {mode!r}; must be one of {sorted(VALID_ENFORCEMENT_MODES)}",
        )

    pipeline = get_pipeline()
    current = pipeline.settings_store.read_settings()
    updated_modes = {control_id: mode for control_id in current.control_modes}
    pipeline.settings_store.update_control_modes(updated_modes)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


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
