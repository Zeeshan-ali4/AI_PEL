"""Routes for the T14 control dashboard, the T15 scenario runner/decision view,
the T16 approval queue, and the T17 evidence record view/export."""

from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.pipeline import PipelineResult, UnknownScenarioError, get_pipeline
from app.schemas.action import Action, ActionType
from app.schemas.audit import EvidenceRecord, RecordType
from app.schemas.context import Context
from app.schemas.decision import Decision, DecisionValue
from app.schemas.evidence import Evidence
from app.settings_store import VALID_ENFORCEMENT_MODES
from scenarios.scenarios import get_scenarios

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

# Stable link target for the human approval queue. The page itself lands in T16;
# T15 only needs the escalation routing to point somewhere stable.
APPROVAL_QUEUE_PATH = "/approvals"

# Stable demo default used when an approver identity is not supplied on the
# approval form (spec §8A item 4 only requires the identity be populated).
DEFAULT_HUMAN_APPROVER = "demo.named.approver@internal.example"

# Plain-English, board-readable summaries for the scenario runner cards (spec §8A item 2).
# These do not alter scenario data or expected outcomes (scenarios/scenarios.py remains
# the single source of truth) — they only add calm narration for the UI.
SCENARIO_SUMMARIES = {
    1: "A routine £80 payment for a clean customer account.",
    2: "An £850 payment requested with no prior approval on record.",
    3: "A £200 payment requested for a customer with an active fraud flag.",
    4: "An external email containing an NHS number, a health condition, and an affordability concern.",
    5: "An external email carrying an uncertain signal of financial hardship.",
    6: "An external email to a known partner containing only a customer's name.",
}

_AMBER_BADGE_CSS = "border-amber-200 bg-amber-50 text-amber-900"

# Headline presentation for each binding decision value (spec §8A item 3).
DECISION_DISPLAY = {
    "allow": {"label": "Allow", "css": "border-emerald-200 bg-emerald-50 text-emerald-900"},
    "allow_with_logging": {
        "label": "Allow, with logging",
        "css": "border-sky-200 bg-sky-50 text-sky-900",
    },
    "escalate": {"label": "Escalate to a human", "css": _AMBER_BADGE_CSS},
    "block": {"label": "Block", "css": "border-rose-200 bg-rose-50 text-rose-900"},
    "require_evidence": {"label": "Require more evidence", "css": _AMBER_BADGE_CSS},
    "modify": {"label": "Modify before proceeding", "css": _AMBER_BADGE_CSS},
    "fail_closed": {"label": "Fail closed", "css": "border-rose-200 bg-rose-50 text-rose-900"},
}


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
    """Run one canonical scenario through the full policy pipeline (T13 JSON contract)."""

    try:
        result = get_pipeline().run_scenario(scenario_id)
    except UnknownScenarioError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return result.response_payload()


@router.get("/scenarios", response_class=HTMLResponse)
def scenarios_page(request: Request) -> HTMLResponse:
    """Render the six canonical scenario cards with a Run action each (spec §8A item 2)."""

    cards = [
        {
            "number": scenario["number"],
            "title": scenario["title"],
            "summary": SCENARIO_SUMMARIES.get(scenario["number"], scenario["title"]),
        }
        for scenario in get_scenarios()
    ]
    return templates.TemplateResponse(request, "scenarios.html", {"cards": cards})


@router.post("/scenarios/{scenario_id}/run", response_class=HTMLResponse)
def run_scenario_view(request: Request, scenario_id: int) -> HTMLResponse:
    """Run one canonical scenario and render its readable decision view (spec §8A item 3)."""

    try:
        result = get_pipeline().run_scenario(scenario_id)
    except UnknownScenarioError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    context = _build_decision_view_context(scenario_id, result)
    return templates.TemplateResponse(request, "decision.html", context)


def _scenario_title(scenario_id: int) -> str:
    for scenario in get_scenarios():
        if scenario["number"] == scenario_id:
            return scenario["title"]
    return f"Scenario {scenario_id}"


def _render_highlighted_text(text: str, spans: list) -> str:
    """Escape `text` and wrap each evidence span in a highlighted <mark>.

    Spans are character offsets into the same content Presidio analysed
    (`app/semantic/evidence_builder.py`), so this never invents markup beyond
    what the real sensor reported.
    """

    if not text:
        return ""
    ordered = sorted(spans, key=lambda span: span.start)
    pieces: list[str] = []
    cursor = 0
    for span in ordered:
        start = max(span.start, cursor)
        if start >= len(text):
            break
        end = min(span.end, len(text))
        if end <= start:
            continue
        pieces.append(html.escape(text[cursor:start]))
        pieces.append(
            f'<mark class="rounded bg-amber-200 px-0.5" title="{html.escape(span.label)}">'
            f"{html.escape(text[start:end])}</mark>"
        )
        cursor = end
    pieces.append(html.escape(text[cursor:]))
    return "".join(pieces)


def _build_context_rows(action: Action, context: Context) -> list[dict[str, Any]]:
    """Readable, labelled resolved-context fields (spec §8A item 3) — not a raw dump."""

    rows = [
        {"label": "Customer status", "value": context.customer.status.value},
        {"label": "Fraud flag", "value": context.customer.fraud_flag},
        {"label": "Sanctions match", "value": context.customer.sanctions_match},
        {"label": "Vulnerability flag", "value": context.customer.vulnerability_flag},
    ]
    if action.action_type == ActionType.FINANCIAL_PAYMENT_ISSUE:
        rows.append({"label": "Existing approval on record", "value": context.approval_state.has_approval})
        rows.append({"label": "Payments in the last 30 days", "value": context.payment_history.count_30d})
    else:
        rows.append({"label": "Recipient is external", "value": context.recipient.is_external})
        rows.append(
            {"label": "Approved disclosure basis", "value": context.recipient.approved_disclosure_basis}
        )
    return rows


def _action_text(action: Action) -> str:
    if action.content is not None:
        return action.content
    body = action.parameters.get("body")
    return body if isinstance(body, str) else ""


def _build_decision_view_context(scenario_id: int, result: PipelineResult) -> dict[str, Any]:
    """Assemble the full T15 decision-view template context from one pipeline run."""

    record = result.record
    action: Action = record.action
    context: Context = record.context_used
    evidence: Evidence = record.evidence
    decision: Decision = record.decision
    outcome = result.enforcement_outcome

    display = DECISION_DISPLAY.get(decision.decision.value, {"label": decision.decision.value, "css": ""})
    escalated = decision.decision == DecisionValue.ESCALATE

    semantic_evaluated = evidence.evaluated
    body_text = _action_text(action) if semantic_evaluated else ""
    vulnerability = evidence.vulnerability_indicators

    return {
        "scenario_number": scenario_id,
        "scenario_title": _scenario_title(scenario_id),
        "decision": {
            "value": decision.decision.value,
            "label": display["label"],
            "css": display["css"],
            "reason": decision.reason,
        },
        "escalated": escalated,
        "required_approval_role": decision.required_approval_role,
        "approval_link": APPROVAL_QUEUE_PATH,
        "control_id": decision.control_id,
        "triggered_controls": decision.triggered_controls,
        "framework_mappings": decision.framework_mappings,
        "threshold_used": decision.threshold_used,
        "context_rows": _build_context_rows(action, context),
        "semantic_evaluated": semantic_evaluated,
        "highlighted_body": _render_highlighted_text(body_text, evidence.evidence_spans),
        "entities": evidence.detected_entities,
        "stub_present": vulnerability.present,
        "stub_confidence": f"{vulnerability.confidence:.2f}",
        "stub_categories": [category.value for category in vulnerability.categories],
        "executed": record.executed,
        "would_have": outcome.would_have,
        "queued": outcome.queued,
    }


def _find_action_evaluation_record(
    records: list[EvidenceRecord], correlation_id: str | None
) -> EvidenceRecord | None:
    """Find the original `action_evaluation` audit row a queued item escalated from."""

    if correlation_id is None:
        return None
    matches = [
        record
        for record in records
        if record.record_type == RecordType.ACTION_EVALUATION
        and str(record.correlation_id) == correlation_id
    ]
    return matches[-1] if matches else None


def _action_summary(action: Action) -> str:
    """A short, board-readable summary of the proposed action for the approval queue."""

    if action.action_type == ActionType.FINANCIAL_PAYMENT_ISSUE:
        amount = action.parameters.get("amount_gbp")
        return f"Payment of £{amount} to customer {action.resource.id}"
    return f"Email to {action.recipient or 'an external recipient'} regarding customer {action.resource.id}"


def _build_pending_rows(pipeline, records: list[EvidenceRecord]) -> list[dict[str, Any]]:
    rows = []
    for item in pipeline.approval_queue.list_pending():
        original = _find_action_evaluation_record(records, item.correlation_id)
        rows.append(
            {
                "item_id": item.item_id,
                "required_approval_role": item.required_approval_role,
                "control_id": item.control_id,
                "reason": item.reason,
                "summary": _action_summary(original.action) if original else "Action details unavailable.",
                "original_record_hash": original.record_hash if original else None,
            }
        )
    return rows


def _build_actioned_rows(records: list[EvidenceRecord]) -> list[dict[str, Any]]:
    """Actioned escalations, read from the append-only audit trail (spec §5.5)."""

    rows = []
    by_hash = {record.record_hash: record for record in records}
    for record in records:
        if record.record_type != RecordType.APPROVAL_DECISION:
            continue
        original = by_hash.get(record.references_hash)
        rows.append(
            {
                "correlation_id": str(record.correlation_id),
                "approved": record.executed,
                "human_approver": record.human_approver,
                "approval_reason": record.approval_reason,
                "control_id": original.decision.control_id if original else None,
                "summary": _action_summary(original.action) if original else "Action details unavailable.",
                "record_hash": record.record_hash,
                "references_hash": record.references_hash,
            }
        )
    return rows


@router.get("/approvals", response_class=HTMLResponse)
def approvals_page(request: Request, actioned_item: str | None = None, error: str | None = None) -> HTMLResponse:
    """Render the human approval queue: pending escalations plus the actioned trail (spec §8A item 4)."""

    pipeline = get_pipeline()
    records = pipeline.audit_store.read_records()
    return templates.TemplateResponse(
        request,
        "approvals.html",
        {
            "pending_rows": _build_pending_rows(pipeline, records),
            "actioned_rows": _build_actioned_rows(records),
            "actioned_item": actioned_item,
            "error": error,
        },
    )


@router.post("/approvals/{item_id}/decide")
def decide_approval(
    item_id: str,
    decision: str = Form(...),
    reason: str = Form(""),
    human_approver: str = Form(""),
) -> RedirectResponse:
    """Action one pending escalation by appending a linked `approval_decision` record.

    The original `action_evaluation` audit row is never mutated — this only ever
    calls `AuditStore.write_record` to append a new row (spec §5.5).
    """

    if decision not in ("approve", "reject"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid decision: {decision!r}")

    pipeline = get_pipeline()
    queue_item = pipeline.approval_queue.get(item_id)
    if queue_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown approval item: {item_id}")

    cleaned_reason = reason.strip()
    if not cleaned_reason:
        return RedirectResponse(
            url=f"{APPROVAL_QUEUE_PATH}?error=A+reason+is+required+to+approve+or+reject+this+escalation.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    records = pipeline.audit_store.read_records()
    original = _find_action_evaluation_record(records, queue_item.correlation_id)
    if original is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original action_evaluation record not found for this approval item.",
        )

    approved = decision == "approve"
    approver = human_approver.strip() or DEFAULT_HUMAN_APPROVER

    pipeline.approval_queue.record_approval_decision(
        item_id=item_id,
        approved=approved,
        human_approver=approver,
        reason=cleaned_reason,
    )

    appended = pipeline.audit_store.write_record(
        action=original.action,
        context_used=original.context_used,
        evidence=original.evidence,
        decision=original.decision,
        enforcement_mode=original.enforcement_mode,
        executed=approved,
        record_type=RecordType.APPROVAL_DECISION,
        references_hash=original.record_hash,
        human_approver=approver,
        approval_reason=cleaned_reason,
        correlation_id=original.correlation_id,
    )

    return RedirectResponse(
        url=f"{APPROVAL_QUEUE_PATH}?actioned_item={appended.record_hash}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _find_record_by_hash(records: list[EvidenceRecord], record_hash: str) -> EvidenceRecord | None:
    for record in records:
        if record.record_hash == record_hash:
            return record
    return None


def _get_record_or_404(record_hash: str) -> tuple[EvidenceRecord, list[EvidenceRecord]]:
    pipeline = get_pipeline()
    records = pipeline.audit_store.read_records()
    record = _find_record_by_hash(records, record_hash)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit record found with record_hash {record_hash!r}.",
        )
    return record, records


def _record_view_context(record: EvidenceRecord, records: list[EvidenceRecord]) -> dict[str, Any]:
    """Build the readable, sectioned single-record view (spec §8A item 5)."""

    referenced = None
    if record.references_hash is not None:
        referenced = _find_record_by_hash(records, record.references_hash)

    action = record.action
    decision = record.decision

    return {
        "record": record,
        "is_approval_decision": record.record_type == RecordType.APPROVAL_DECISION,
        "action_summary": _action_summary(action),
        "decision_label": DECISION_DISPLAY.get(
            decision.decision.value, {"label": decision.decision.value}
        )["label"],
        "control_id": decision.control_id,
        "framework_mappings": decision.framework_mappings,
        "referenced": referenced,
    }


@router.get("/records/{record_hash}", response_class=HTMLResponse)
def record_view(request: Request, record_hash: str) -> HTMLResponse:
    """Render the single, printable evidence record view (spec §8A item 5)."""

    record, records = _get_record_or_404(record_hash)
    return templates.TemplateResponse(request, "record.html", _record_view_context(record, records))


@router.get("/records/{record_hash}/export.json")
def record_export_json(record_hash: str) -> JSONResponse:
    """Download a faithful JSON export of the persisted evidence record (spec §8A item 5, §12)."""

    record, _records = _get_record_or_404(record_hash)
    payload = record.model_dump(mode="json")
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="evidence-record-{record_hash}.json"'},
    )


@router.get("/records/{record_hash}/export.html", response_class=HTMLResponse)
def record_export_html(request: Request, record_hash: str) -> HTMLResponse:
    """Download a printable, human-readable export of the evidence record (spec §8A item 5)."""

    record, records = _get_record_or_404(record_hash)
    context = _record_view_context(record, records)
    context["generated_at"] = datetime.now().isoformat()
    context["is_export"] = True
    response = templates.TemplateResponse(request, "record.html", context)
    response.headers["Content-Disposition"] = f'attachment; filename="evidence-record-{record_hash}.html"'
    return response
