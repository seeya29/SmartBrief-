from typing import Any, Dict, List, Optional, Literal
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from summaryflow_v4 import summarize_message
from summaryflow_v3 import _preprocess_text
from context_cleaner_v4 import clean_all
from context_loader import ContextLoader


Platform = Literal["whatsapp", "email", "instagram", "sms"]
Device = Literal["ios", "android", "web", "windows", "macos", "unknown"]
Intent = Literal["meeting", "reminder", "question", "task", "note"]
Urgency = Literal["low", "medium", "high"]


class SummarizeInput(BaseModel):
    user_id: str
    platform: Platform
    message_id: str
    message_text: str
    timestamp: str


class DecisionHubSummary(BaseModel):
    summary_id: str
    user_id: str
    platform: Platform
    message_id: str
    summary: str
    intent: Intent
    urgency: Urgency
    entities: Dict[str, Any]
    context_flags: List[str]
    generated_at: str
    device_context: Device


class CleanInput(BaseModel):
    platform: Platform
    message_text: str


class CleanOutput(BaseModel):
    cleaned_text: str


app = FastAPI()
loader = ContextLoader()


@app.post("/api/summarize", response_model=DecisionHubSummary)
def api_summarize(payload: SummarizeInput):
    result = summarize_message(payload.dict())
    return DecisionHubSummary(**result)


@app.get("/api/context")
def api_context(
    user_id: str = Query(...),
    platform: Platform = Query(...),
    limit: int = Query(3, ge=1, le=50),
):
    return loader.get_context(user_id, platform, limit)


@app.post("/api/message_cleaner", response_model=CleanOutput)
def api_message_cleaner(payload: CleanInput):
    base_clean, _ = clean_all(payload.platform, payload.message_text)
    if payload.platform == "email":
        cleaned = base_clean
    else:
        cleaned = _preprocess_text(payload.platform, base_clean)
    return CleanOutput(cleaned_text=cleaned)

