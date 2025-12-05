"""
SummaryFlow v3 — lightweight message summarizer API

Input payload schema:
{
    "user_id": str,
    "platform": str,
    "message_id": str,
    "message_text": str,
    "timestamp": str (ISO 8601, UTC 'Z')
}

Output schema (MUST match this structure):
{
    "summary_id": str,
    "user_id": str,
    "platform": str,
    "message_id": str,
    "summary": str,
    "type": str,              # e.g., "meeting"
    "intent": str,            # e.g., "confirm_meeting"
    "urgency": str,           # one of: low | medium | high
    "entities": {
        "person": [str, ...],
        "datetime": str | None
    },
    "generated_at": str       # ISO 8601 UTC 'Z'
}

This module uses simple heuristics (regex and keyword rules) to classify intent,
type, urgency, and to extract basic entities. It is dependency-free.
"""

from __future__ import annotations

import os
import json
import sqlite3
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


# === Public API ===
def summarize_message(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize a single message to the required structure.

    Args:
        payload: Dict with keys user_id, platform, message_id, message_text, timestamp (ISO 8601 UTC "Z").

    Returns:
        Dict matching the required output schema.
    """
    user_id = str(payload.get("user_id", "")).strip()
    platform = str(payload.get("platform", "")).strip()
    message_id = str(payload.get("message_id", "")).strip()
    raw_message_text = str(payload.get("message_text", "")).strip()
    anchor_ts_str = str(payload.get("timestamp", "")).strip()

    anchor_ts = _parse_iso_utc(anchor_ts_str) or datetime.now(timezone.utc)

    # Platform-specific preprocessing
    message_text = _preprocess_text(platform, raw_message_text)

    people = _extract_people(message_text)
    target_dt = _extract_datetime(message_text, anchor_ts)
    msg_type = _classify_type(message_text)
    intent = _classify_intent(message_text, msg_type)
    urgency = _classify_urgency(message_text, target_dt, anchor_ts)

    summary_text = _build_summary(message_text, intent, msg_type, people, target_dt, anchor_ts)

    result = {
        "summary_id": _make_summary_id(),
        "user_id": user_id,
        "platform": platform,
        "message_id": message_id,
        "summary": summary_text,
        "type": msg_type,
        "intent": intent,
        "urgency": urgency,
        "entities": {
            "person": people,
            "datetime": _format_iso_utc(target_dt) if target_dt else None,
        },
        "generated_at": _format_iso_utc(datetime.now(timezone.utc)),
    }

    # Persist summary to assistant_core.db
    try:
        save_summary(result)
    except Exception:
        # Avoid raising DB errors from the core summarization path
        pass

    return result


# === Persistence: SQLite helpers ===
DB_FILENAME = "assistant_core.db"
TABLE_NAME = "summaries"


def _get_db_path() -> str:
    return os.path.join(os.path.dirname(__file__), DB_FILENAME)


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            summary_id   TEXT PRIMARY KEY,
            user_id      TEXT,
            message_id   TEXT,
            summary      TEXT,
            type         TEXT,
            intent       TEXT,
            urgency      TEXT,
            entities     TEXT,
            platform     TEXT,
            generated_at TEXT
        )
        """
    )
    conn.commit()


def save_summary(summary_dict: Dict[str, Any]) -> None:
    """Save a summary dict into SQLite `assistant_core.db` summaries table.

    Required keys: summary_id, user_id, message_id, summary, type, intent,
    urgency, entities (dict), platform, generated_at.
    """
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        _ensure_schema(conn)

        entities_json = json.dumps(summary_dict.get("entities", {}), ensure_ascii=False)
        conn.execute(
            f"""
            INSERT OR REPLACE INTO {TABLE_NAME} (
                summary_id, user_id, message_id, summary,
                type, intent, urgency, entities, platform, generated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                summary_dict.get("summary_id"),
                summary_dict.get("user_id"),
                summary_dict.get("message_id"),
                summary_dict.get("summary"),
                summary_dict.get("type"),
                summary_dict.get("intent"),
                summary_dict.get("urgency"),
                entities_json,
                summary_dict.get("platform"),
                summary_dict.get("generated_at"),
            ),
        )
        conn.commit()
    finally:
     conn.close()


def get_summary(summary_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a summary by `summary_id` from SQLite.

    Returns the full dict with `entities` parsed back into a Python object,
    or None if not found.
    """
    db_path = _get_db_path()
    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect(db_path)
    try:
        _ensure_schema(conn)
        cur = conn.execute(
            f"SELECT summary_id, user_id, message_id, summary, type, intent, urgency, entities, platform, generated_at FROM {TABLE_NAME} WHERE summary_id = ?",
            (summary_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        entities = None
        if row[7]:
            try:
                entities = json.loads(row[7])
            except Exception:
                entities = row[7]

        return {
            "summary_id": row[0],
            "user_id": row[1],
            "message_id": row[2],
            "summary": row[3],
            "type": row[4],
            "intent": row[5],
            "urgency": row[6],
            "entities": entities,
            "platform": row[8],
            "generated_at": row[9],
        }
    finally:
        conn.close()


# === Platform-specific preprocessing ===
def _preprocess_text(platform: str, text: str) -> str:
    p = (platform or "").lower()
    if p == "whatsapp":
        return _normalize_spacing(_remove_duplicates(_strip_emojis(text)))
    if p == "email":
        return _email_clean(text)
    if p in {"instagram", "instagram dm", "ig", "insta"}:
        return _instagram_clean(text)
    return _normalize_spacing(text)


def _strip_emojis(text: str) -> str:
    return re.sub(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E6-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]", "", text)


def _remove_duplicates(text: str) -> str:
    # Collapse repeated characters (e.g., "Helloooo" -> "Helloo")
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    # Remove consecutive duplicate words
    tokens = text.split()
    if not tokens:
        return text
    dedup = [tokens[0]]
    for tok in tokens[1:]:
        if tok != dedup[-1]:
            dedup.append(tok)
    return " ".join(dedup)


def _normalize_spacing(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _email_clean(text: str) -> str:
    lines = text.splitlines()
    subject = None
    cleaned_lines = []
    signature_started = False

    signature_markers = {"--", "__", "Sent from my iPhone", "Sent from my Android", "Regards", "Best", "Thanks"}
    forwarded_markers = {"Forwarded message", "Begin forwarded message", "-----Original Message-----", "----- Forwarded Message -----", "From:", "Sent:", "To:"}

    for line in lines:
        lstr = line.strip()
        if not lstr:
            continue
        if lstr.lower().startswith("subject:") and subject is None:
            subject = lstr.split(":", 1)[1].strip() if ":" in lstr else lstr
            continue
        if lstr.startswith(">"):
            continue
        if any(lstr.startswith(m) for m in forwarded_markers):
            continue
        if re.match(r"^On .+ wrote:\s*$", lstr, re.IGNORECASE):
            continue
        if any(lstr.startswith(m) for m in signature_markers):
            signature_started = True
        if signature_started:
            continue
        cleaned_lines.append(lstr)

    body = " ".join(cleaned_lines)
    body = _normalize_spacing(body)
    body = re.sub(r"(?i)\bBegin forwarded message\b.*", "", body)
    body = re.sub(r"(?i)\bForwarded message\b.*", "", body)
    body = re.sub(r"(?i)\bOn .+ wrote:\b", "", body)
    body = re.sub(r"(?i)\bFrom:\b.*", "", body)
    body = re.sub(r"(?i)\bSent:\b.*", "", body)
    body = re.sub(r"(?i)\bTo:\b.*", "", body)
    body = re.sub(r"\s>[^\n]*", "", body)
    body = _normalize_spacing(body)
    if subject:
        return f"{subject} — {body}" if body else subject
    return body


def _instagram_clean(text: str) -> str:
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)
    # Remove hashtags
    text = re.sub(r"#[\w_]+", "", text)

    # Preserve context if message is a reply
    # Heuristic: capture quoted or referenced snippet after 'replying to'/'replied to'
    reply_context = None
    m = re.search(r"\b(replying to|replied to)\b[:\s]*([\"']?)(.+?)\2(\.|!|\?|$)", text, re.IGNORECASE)
    if m:
        reply_context = m.group(3).strip()

    text = _normalize_spacing(text)
    if reply_context and reply_context not in text:
        text = f"In reply to: {reply_context}. {text}"
    return text


# === Helpers: IDs, time parsing/formatting ===
def _make_summary_id() -> str:
    # Short stable identifier
    return f"s_{uuid.uuid4().hex[:8]}"


def _parse_iso_utc(ts: str) -> Optional[datetime]:
    try:
        # Accept both with 'Z' and offset forms
        if ts.endswith("Z"):
            return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        # Try common forms
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _format_iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# === Helpers: entity extraction ===
def _extract_people(text: str) -> List[str]:
    people: List[str] = []

    for m in re.finditer(r"\b(?:with|from|to|cc|attn)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text):
        name = m.group(1).strip()
        if name and name not in people:
            people.append(name)

    honorific = re.findall(r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)
    for name in honorific:
        if name and name not in people:
            people.append(name)

    tokens_text = text
    if "—" in tokens_text:
        left, right = tokens_text.split("—", 1)
        tokens_text = right
    elif " - " in tokens_text:
        left, right = tokens_text.split(" - ", 1)
        tokens_text = right
    if tokens_text.lower().startswith("subject:"):
        tokens_text = tokens_text.split(":", 1)[1]
    tokens_text = re.sub(r"^(\s*Reminder\b[\s:\-–—]*)", "", tokens_text)
    tokens = re.findall(r"\b([A-Z][a-z]+)\b", tokens_text)
    for tok in tokens:
        if tok.lower() in {"hey", "please", "confirm", "tomorrow", "meeting", "pm", "am", "hello", "update", "subject", "let", "thanks", "regards", "reminder"}:
            continue
        if tok not in people:
            people.append(tok)

    stop = {"hey","please","confirm","tomorrow","meeting","pm","am","hello","update","subject","let","thanks","regards","reminder"}
    people = [p for p in people if p.lower() not in stop]
    return people


def _extract_datetime(text: str, anchor: datetime) -> Optional[datetime]:
    text_lower = text.lower()
    day_offset = 0
    if "tomorrow" in text_lower:
        day_offset = 1
    elif "today" in text_lower:
        day_offset = 0

    weekdays = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    for i, wd in enumerate(weekdays):
        if wd in text_lower:
            current_idx = anchor.weekday()
            target_idx = i
            diff = (target_idx - current_idx) % 7
            if diff == 0:
                diff = 7
            day_offset = diff
            break

    default_times = {
        "morning": (9, 0),
        "afternoon": (15, 0),
        "evening": (18, 0),
        "tonight": (20, 0),
        "eod": (17, 0),
        "end of day": (17, 0),
    }
    for k, (h, m) in default_times.items():
        if k in text_lower:
            target_date = (anchor + timedelta(days=day_offset)).date()
            return datetime(target_date.year, target_date.month, target_date.day, h, m, tzinfo=timezone.utc)

    rel = re.search(r"\bin\s+(\d+)\s+(minutes|minute|hours|hour|days|day)\b", text_lower)
    if rel:
        val = int(rel.group(1))
        unit = rel.group(2)
        if unit.startswith("minute"):
            return anchor + timedelta(minutes=val)
        if unit.startswith("hour"):
            return anchor + timedelta(hours=val)
        if unit.startswith("day"):
            return anchor + timedelta(days=val)

    time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?\b", text)
    if not time_match:
        iso_date = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
        if iso_date:
            year, month, day = map(int, iso_date.groups())
            return datetime(year, month, day, tzinfo=timezone.utc)
        month_day = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\b", text)
        if month_day:
            months = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
            month = months[month_day.group(1)]
            day = int(month_day.group(2))
            year = anchor.year
            return datetime(year, month, day, tzinfo=timezone.utc)
        return None

    hour = int(time_match.group(1))
    minute = int(time_match.group(2)) if time_match.group(2) else 0
    ampm = time_match.group(3)
    if ampm:
        ampm_lower = ampm.lower()
        if ampm_lower == "pm" and hour != 12:
            hour += 12
        elif ampm_lower == "am" and hour == 12:
            hour = 0
    target_date = (anchor + timedelta(days=day_offset)).date()
    return datetime(target_date.year, target_date.month, target_date.day, hour, minute, tzinfo=timezone.utc)


# === Helpers: classification ===
def _classify_type(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["meeting", "meet", "appointment", "call", "schedule", "reschedule", "cancel", "talk", "chat"]):
        return "meeting"
    if any(w in t for w in ["reminder", "don't forget", "dont forget", "remember", "due", "deadline", "by eod", "eod", "by "]):
        return "reminder"
    if any(w in t for w in ["fyi", "for your information", "note", "heads up", "update"]):
        return "note"
    if any(w in t for w in ["task", "todo", "action item", "assign", "please", "can you", "could you"]):
        return "task"
    if any(w in t for w in ["question", "?", "ask", "clarify", "who", "what", "when", "where", "how", "why"]):
        return "question"
    return "message"


def _classify_intent(text: str, msg_type: str) -> str:
    t = text.lower()
    if msg_type == "meeting":
        if "confirm" in t or "confirmation" in t:
            return "confirm_meeting"
        if "schedule" in t or "set up" in t or "book" in t:
            return "schedule_meeting"
        if "reschedule" in t or "move" in t or "postpone" in t:
            return "reschedule_meeting"
        if "cancel" in t:
            return "cancel_meeting"
        return "inform_meeting"

    if msg_type == "reminder" or any(w in t for w in ["reminder", "don't forget", "dont forget", "remember", "due", "deadline", "by eod", "eod"]):
        return "reminder"
    if msg_type == "note":
        return "informational"

    if any(w in t for w in ["urgent", "asap", "immediately", "high priority", "priority"]):
        return "urgent_request"
    if any(w in t for w in ["can you", "please", "could you", "send", "share", "help", "assign", "finish", "complete"]):
        return "request"
    if any(w in t for w in ["update", "any update", "follow up", "follow-up", "status"]):
        return "follow_up"
    if any(w in t for w in ["question", "?", "how", "what", "why", "when", "where"]):
        return "question"
    return "informational"


def _classify_urgency(text: str, target_dt: Optional[datetime], anchor: datetime) -> str:
    t = text.lower()
    if any(w in t for w in ["emergency", "critical", "urgent", "asap", "immediately", "high priority", "priority"]):
        return "high"
    if t.count("!") >= 3:
        return "high"

    if target_dt:
        delta = target_dt - anchor
        hours = delta.total_seconds() / 3600.0
        if hours <= 6:
            return "high"
        if hours <= 48:
            return "medium"
        return "low"

    if any(w in t for w in ["soon", "tomorrow", "today", "eod", "end of day", "tonight"]):
        return "medium"
    return "low"


# === Helpers: summary text ===
def _build_summary(
    message_text: str,
    intent: str,
    msg_type: str,
    people: List[str],
    target_dt: Optional[datetime],
    anchor_ts: datetime,
) -> str:
    parts: List[str] = []

    # Intent phrasing
    intent_map = {
        "confirm_meeting": "User wants confirmation",
        "schedule_meeting": "User wants to schedule",
        "reschedule_meeting": "User wants to reschedule",
        "cancel_meeting": "User wants to cancel",
        "inform_meeting": "User shares an update",
        "reminder": "User shares a reminder",
        "urgent_request": "User has an urgent request",
        "request": "User requests",
        "follow_up": "User is following up",
        "question": "User asks a question",
        "informational": "User shares information",
    }
    lead = intent_map.get(intent, "User message")

    # Type phrasing
    if msg_type == "meeting":
        # Time phrase
        when_phrase = None
        if target_dt:
            day_diff = (target_dt.date() - anchor_ts.date()).days
            if day_diff == 0:
                when_phrase = "today"
            elif day_diff == 1:
                when_phrase = "tomorrow"
            else:
                when_phrase = target_dt.strftime("on %Y-%m-%d")

            # Windows-compatible hour formatting without leading zero and minutes
            hour_12 = target_dt.hour % 12 or 12
            ampm = "AM" if target_dt.hour < 12 else "PM"
            time_phrase = f"{hour_12}"
            if target_dt.minute:
                time_phrase += f":{target_dt.minute:02d}"
            time_phrase += f" {ampm}"
        else:
            time_phrase = None
            when_phrase = None

        person_phrase = (
            f" with {', '.join(people)}" if people else ""
        )

        if intent == "confirm_meeting":
            if time_phrase and when_phrase:
                parts.append(f"{lead} for a {time_phrase} meeting{person_phrase} {when_phrase}.")
            elif time_phrase:
                parts.append(f"{lead} for a {time_phrase} meeting{person_phrase}.")
            else:
                parts.append(f"{lead} for a meeting{person_phrase}.")
        else:
            # Generic meeting wording
            if time_phrase and when_phrase:
                parts.append(f"{lead} about a {time_phrase} meeting{person_phrase} {when_phrase}.")
            elif time_phrase:
                parts.append(f"{lead} about a {time_phrase} meeting{person_phrase}.")
            else:
                parts.append(f"{lead} about a meeting{person_phrase}.")
    else:
        # Non-meeting: fallback short summary based on intent
        parts.append(f"{lead}.")

    return " ".join(parts)


if __name__ == "__main__":
    import sys, json
    data = json.loads(sys.stdin.read()) if not sys.stdin.closed else {}
    print(json.dumps(summarize_message(data), ensure_ascii=False))
