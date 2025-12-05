# SummaryFlow v4 — Production API and Usage Guide

## Overview
- SummaryFlow v4 is the first stage (“first brain”) every message passes through.
- Outputs a stable, predictable schema that matches Nilesh’s Decision Hub expectations.
- Cross‑platform cleaner normalizes iOS/Android/Email/CRM inputs before summarization.

## Endpoints
- `POST /api/summarize`
- `GET /api/context`
- `POST /api/message_cleaner`

## Request/Response Schemas
- `POST /api/summarize` body:
```
{
  "user_id": "abc123",
  "platform": "whatsapp|email|instagram|sms",
  "message_id": "m123",
  "message_text": "...",
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ"
}
```
- `POST /api/summarize` response (Decision Hub schema):
```
{
  "summary_id": "s_123",
  "user_id": "abc123",
  "platform": "whatsapp|email|instagram|sms",
  "message_id": "m123",
  "summary": "...",
  "intent": "meeting|reminder|question|task|note",
  "urgency": "low|medium|high",
  "entities": {
    "person": ["..."],
    "datetime": "YYYY-MM-DDTHH:MM:SSZ" | null
  },
  "context_flags": ["has_date", "has_person", "follow_up"],
  "generated_at": "YYYY-MM-DDTHH:MM:SSZ",
  "device_context": "ios|android|web|windows|macos|unknown"
}
```
- `GET /api/context` query:
  - `user_id`: string
  - `platform`: `whatsapp|email|instagram|sms`
  - `limit`: integer (default 3)
- `POST /api/message_cleaner` body:
```
{
  "platform": "whatsapp|email|instagram|sms",
  "message_text": "..."
}
```
- `POST /api/message_cleaner` response:
```
{ "cleaned_text": "..." }
```

## Example Calls
- PowerShell — Summarize:
```
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/summarize -ContentType 'application/json' -Body '{
  "user_id":"abc123",
  "platform":"whatsapp",
  "message_id":"m123",
  "message_text":"Let\u2019s meet tomorrow at 5 pm with Priya.",
  "timestamp":"2025-12-05T09:00:00Z"
}' | ConvertTo-Json -Depth 6
```
- PowerShell — Message Cleaner:
```
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/message_cleaner -ContentType 'application/json' -Body '{
  "platform":"email",
  "message_text":"Subject: Update\nBegin forwarded message\n... Hello!! Please confirm 5pm tomorrow."
}' | ConvertTo-Json -Depth 5
```
- PowerShell — Context:
```
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/api/context?user_id=abc123&platform=whatsapp&limit=3' | ConvertTo-Json -Depth 5
```

## Frontend Integration
- Always send `platform`, `user_id`, `message_id`, `timestamp`, and raw `message_text` to `/api/summarize`.
- `timestamp` must be ISO8601 UTC with `Z`, e.g. `2025-12-05T09:00:00Z`.
- Do not pre-clean; backend runs cross‑platform cleaner automatically.
- For UI previews, you may call `/api/message_cleaner` to show the cleaned text.
- `device_context` is populated by SummaryFlow heuristics (e.g., “Sent from my iPhone” → `ios`). No extra frontend field required.

## Decision Hub Payload
- Forward the `/api/summarize` response as-is to Nilesh’s `/api/decision_hub`:
  - Required keys: `summary_id`, `user_id`, `platform`, `message_id`, `summary`, `intent`, `urgency`, `entities`, `context_flags`, `generated_at`, `device_context`.
  - `intent` is one of `meeting|reminder|question|task|note`.
  - `urgency` is one of `low|medium|high`.
  - `entities.person` is a string array; `entities.datetime` is ISO8601 or `null`.
  - `context_flags` contains zero or more of `["has_date", "has_person", "follow_up"]`.

## Persistence
- Summaries are automatically written to `assistant_core.db` → `summaries` with fields:
  - `summary_id`, `user_id`, `platform`, `message_id`, `summary`, `intent`, `urgency`, `entities` (JSON), `timestamp` (ISO8601)

## Quick Start
- Install deps: `python -m pip install fastapi uvicorn pydantic emoji`
- Run: `python -m uvicorn server:app --host 127.0.0.1 --port 8000`
- Call the endpoints as shown above.

## Notes
- The cleaner standardizes emojis, punctuation, removes forwarded/quoted blocks, and collapses noisy repetitions.
- Extraction is rule-based and lightweight, prioritizing predictability over ML.
