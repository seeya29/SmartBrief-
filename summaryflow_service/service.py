from typing import Any, Dict
from fastapi import APIRouter

from summaryflow_v4 import summarize_message, fetch_summary_v4
from summaryflow_v3 import (
    _preprocess_text,
    _classify_type,
    _classify_intent,
    _classify_urgency,
    _extract_people,
    _extract_datetime,
    _format_iso_utc,
)
from .schemas import SummarizeInput, DecisionHubSummary, ClassifyOutput, EntitiesOutput
from datetime import datetime, timezone

def _parse_anchor(ts: str) -> datetime:
    try:
        if ts.endswith("Z"):
            return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

router = APIRouter()


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "version": "v4"}


@router.post("/summarize", response_model=DecisionHubSummary)
def summarize(payload: SummarizeInput) -> DecisionHubSummary:
    result = summarize_message(payload.dict())
    return DecisionHubSummary(**result)


@router.post("/classify", response_model=ClassifyOutput)
def classify(payload: SummarizeInput) -> ClassifyOutput:
    cleaned = _preprocess_text(payload.platform, payload.message_text)
    msg_type = _classify_type(cleaned)
    intent = _classify_intent(cleaned, msg_type)
    anchor = _parse_anchor(payload.timestamp)
    urgency = _classify_urgency(cleaned, None, anchor)
    api_intent = msg_type if msg_type in {"meeting", "reminder", "question", "task", "note"} else "note"
    return ClassifyOutput(type=api_intent, intent=api_intent, urgency=urgency)


@router.post("/entities", response_model=EntitiesOutput)
def entities(payload: SummarizeInput) -> EntitiesOutput:
    cleaned = _preprocess_text(payload.platform, payload.message_text)
    people = _extract_people(cleaned)
    anchor = _parse_anchor(payload.timestamp)
    dt = _extract_datetime(cleaned, anchor)
    return EntitiesOutput(person=people, datetime=_format_iso_utc(dt) if dt else None)


@router.get("/history/{summary_id}")
def history(summary_id: str) -> Dict[str, Any]:
    rec = fetch_summary_v4(summary_id)
    if not rec:
        return {"error": "not_found", "summary_id": summary_id}
    return rec
