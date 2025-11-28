SummaryFlow v3 Documentation

Overview
- SummaryFlow v3 provides a lightweight, dependency-free API to classify messages and extract key entities.
- It standardizes outputs for downstream consumers, including Sankalp (task engine) and Nilesh (decision hub).
- It also persists summaries to a local SQLite database (`assistant_core.db`) for retrieval and analytics.

Supported Fields
- Input payload (required):
  - `user_id` (TEXT)
  - `platform` (TEXT) — e.g., `whatsapp`, `email`, `slack`, `instagram`
  - `message_id` (TEXT)
  - `message_text` (TEXT)
  - `timestamp` (TEXT, ISO8601, UTC, `Z`)
- Output summary (always returned):
  - `summary_id` (TEXT)
  - `user_id` (TEXT)
  - `platform` (TEXT)
  - `message_id` (TEXT)
  - `summary` (TEXT) — concise, user-action phrasing
  - `type` (TEXT) — examples: `meeting`, `reminder`, `note`, `task`, `question`, `message`
  - `intent` (TEXT) — examples: `confirm_meeting`, `schedule_meeting`, `reschedule_meeting`, `cancel_meeting`, `reminder`, `request`, `follow_up`, `question`, `informational`, `urgent_request`
  - `urgency` (TEXT) — `low` | `medium` | `high`
  - `entities` (JSON):
    - `person` (list of strings)
    - `datetime` (TEXT, ISO8601 UTC) or `null`
  - `generated_at` (TEXT, ISO8601 UTC)

Sample Input
- Python payload example:
  - `{ "user_id": "abc123", "platform": "whatsapp", "message_id": "m001", "message_text": "Hey, please confirm tomorrow's 5 PM meeting with Priya.", "timestamp": "2025-11-20T14:00:00Z" }`

Sample Output
- Returned structure:
  - `{ "summary_id": "s_8f3a2bcd", "user_id": "abc123", "platform": "whatsapp", "message_id": "m001", "summary": "User wants confirmation for a 5 PM meeting with Priya tomorrow.", "type": "meeting", "intent": "confirm_meeting", "urgency": "medium", "entities": { "person": ["Priya"], "datetime": "2025-11-21T17:00:00Z" }, "generated_at": "2025-11-20T14:00:02Z" }`

DB Insert Example
- The API automatically saves summaries into `assistant_core.db` under the `summaries` table.
- Manual usage:
  - `from summaryflow_v3 import summarize_message, save_summary, get_summary`
  - `result = summarize_message(payload)`  — auto-inserts into DB
  - `save_summary(result)`  — explicit insert/replace if needed
  - `row = get_summary(result["summary_id"])`  — fetches a single summary dict
- Table schema (`summaries`):
  - `summary_id` (TEXT, primary key)
  - `user_id` (TEXT)
  - `message_id` (TEXT)
  - `summary` (TEXT)
  - `type` (TEXT)
  - `intent` (TEXT)
  - `urgency` (TEXT)
  - `entities` (TEXT, JSON string)
  - `platform` (TEXT)
  - `generated_at` (TEXT)

Platform Preprocessing
- Applied before classification and entity extraction:
  - `whatsapp`: removes emojis, deduplicates consecutive words, normalizes whitespace.
  - `email`: extracts `Subject:` if present, ignores common signature blocks, normalizes whitespace.
  - `instagram`: removes URLs/hashtags, preserves basic reply context; normalizes whitespace.

How Sankalp & Nilesh Use the Output
- Sankalp (task engine):
  - Uses `type`, `intent`, `urgency`, and `entities` to route tasks (e.g., create/confirm/reschedule meeting tasks; set priority from `urgency`; attach `person` and `datetime` to calendar/task payloads).
- Nilesh (decision hub):
  - Uses `type`/`intent` to determine action policy (confirm vs. schedule vs. informational), and `entities.datetime` to decide timing; urgency informs escalation or notification channels; `entities.person` supports recipient mapping.

Quick Start
- `from summaryflow_v3 import summarize_message`
- `result = summarize_message(payload)`
- `print(result["summary"], result["type"], result["intent"], result["urgency"])`
- `row = get_summary(result["summary_id"])`

Notes
- Time parsing anchors to the input `timestamp` and produces ISO8601 UTC.
- `INSERT OR REPLACE` is used for idempotent writes by `summary_id`.
- No external dependencies; suitable for constrained environments.