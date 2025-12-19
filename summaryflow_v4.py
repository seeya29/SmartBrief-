from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import os
import sqlite3
import json

from summaryflow_v3 import (
    _preprocess_text,
    _extract_people,
    _extract_datetime,
    _classify_type,
    _classify_intent,
    _classify_urgency,
    _format_iso_utc,
    _make_summary_id,
    _build_summary,
)
from context_cleaner_v4 import clean_all


def summarize_message(payload: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(payload.get("user_id", "")).strip()
    platform = str(payload.get("platform", "")).strip()
    message_id = str(payload.get("message_id", "")).strip()
    raw_message_text = str(payload.get("message_text", "")).strip()
    anchor_ts_str = str(payload.get("timestamp", "")).strip()

    anchor_ts = _parse_iso_utc(anchor_ts_str) or datetime.now(timezone.utc)

    base_clean, meta = clean_all(platform, raw_message_text)
    message_text = _preprocess_text(platform, base_clean)

    people = _extract_people(message_text)
    target_dt = _extract_datetime(message_text, anchor_ts)
    msg_type = _classify_type(message_text)
    detailed_intent = _classify_intent(message_text, msg_type)
    urgency = _classify_urgency(message_text, target_dt, anchor_ts)

    summary_text = _build_summary(message_text, detailed_intent, msg_type, people, target_dt, anchor_ts)

    api_intent = _map_type_to_api_intent(msg_type)

    context_flags: List[str] = []
    if target_dt:
        context_flags.append("has_date")
    if people:
        context_flags.append("has_person")
    if detailed_intent == "follow_up" or "follow up" in message_text.lower() or "follow-up" in message_text.lower() or meta.get("is_reply") == "true":
        context_flags.append("follow_up")

    device_ctx = _detect_device_context(platform, raw_message_text)

    result = {
        "summary_id": _make_summary_id(),
        "user_id": user_id,
        "platform": platform,
        "message_id": message_id,
        "summary": summary_text,
        "intent": api_intent,
        "urgency": urgency,
        "entities": {
            "person": people,
            "datetime": _format_iso_utc(target_dt) if target_dt else None,
        },
        "context_flags": context_flags,
        "generated_at": _format_iso_utc(datetime.now(timezone.utc)),
        "device_context": device_ctx,
    }

    try:
        save_summary_v4(result)
    except Exception:
        pass

    return result


def _parse_iso_utc(ts: str) -> Optional[datetime]:
    try:
        if ts.endswith("Z"):
            return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _map_type_to_api_intent(msg_type: str) -> str:
    t = (msg_type or "").lower()
    if t == "meeting":
        return "meeting"
    if t == "reminder":
        return "reminder"
    if t == "question":
        return "question"
    if t == "task":
        return "task"
    return "note"


def _detect_device_context(platform: str, raw_text: str) -> str:
    t = (raw_text or "").lower()
    if "sent from my iphone" in t or "ios" in t:
        return "ios"
    if "sent from my android" in t or "android" in t:
        return "android"
    if "windows" in t:
        return "windows"
    if "mac os x" in t or "macos" in t or "mac" in t:
        return "macos"
    if "web" in t or "via web" in t:
        return "web"
    return "unknown"


DB_FILENAME = "assistant_core.db"
TABLE_NAME = "summaries"


def _get_db_path() -> str:
    return os.path.join(os.path.dirname(__file__), DB_FILENAME)


def _ensure_schema_v4(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            summary_id   TEXT PRIMARY KEY,
            user_id      TEXT,
            platform     TEXT,
            message_id   TEXT,
            summary      TEXT,
            intent       TEXT,
            urgency      TEXT,
            entities     TEXT,
            timestamp    TEXT
        )
        """
    )
    cur = conn.execute(f"PRAGMA table_info({TABLE_NAME})")
    cols = {r[1] for r in cur.fetchall()}
    if "timestamp" not in cols:
        conn.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN timestamp TEXT")
    conn.commit()


def save_summary_v4(summary_dict: Dict[str, Any]) -> None:
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        _ensure_schema_v4(conn)
        entities_json = json.dumps(summary_dict.get("entities", {}), ensure_ascii=False)
        ts = summary_dict.get("generated_at")
        conn.execute(
            f"""
            INSERT OR REPLACE INTO {TABLE_NAME} (
                summary_id, user_id, platform, message_id, summary,
                intent, urgency, entities, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                summary_dict.get("summary_id"),
                summary_dict.get("user_id"),
                summary_dict.get("platform"),
                summary_dict.get("message_id"),
                summary_dict.get("summary"),
                summary_dict.get("intent"),
                summary_dict.get("urgency"),
                entities_json,
                ts,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def fetch_summary_v4(summary_id: str) -> Optional[Dict[str, Any]]:
    db_path = _get_db_path()
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    try:
        _ensure_schema_v4(conn)
        cur = conn.execute(
            f"SELECT summary_id, user_id, platform, message_id, summary, intent, urgency, entities, timestamp FROM {TABLE_NAME} WHERE summary_id = ?",
            (summary_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        try:
            entities = json.loads(row[7]) if row[7] else {}
        except Exception:
            entities = row[7]
        return {
            "summary_id": row[0],
            "user_id": row[1],
            "platform": row[2],
            "message_id": row[3],
            "summary": row[4],
            "intent": row[5],
            "urgency": row[6],
            "entities": entities,
            "generated_at": row[8],
        }
    finally:
        conn.close()

