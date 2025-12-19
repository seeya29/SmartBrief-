from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

Platform = Literal["whatsapp", "email", "instagram", "sms"]
DeviceContext = Literal["ios", "android", "web", "windows", "macos", "unknown"]
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
    device_context: DeviceContext


class ClassifyOutput(BaseModel):
    type: Intent
    intent: Intent
    urgency: Urgency


class EntitiesOutput(BaseModel):
    person: List[str] = Field(default_factory=list)
    datetime: Optional[str] = None

