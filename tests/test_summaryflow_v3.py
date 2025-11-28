import os
import unittest
from datetime import datetime

from summaryflow_v3 import summarize_message, get_summary


class TestSummaryFlowV3(unittest.TestCase):
    def setUp(self):
        # Ensure a clean DB state per run by removing file if present
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'assistant_core.db')
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    # 1. Summary contains all required fields
    def test_required_fields(self):
        payload = {
            "user_id": "abc123",
            "platform": "whatsapp",
            "message_id": "m001",
            "message_text": "Hey, please confirm tomorrow's 5 PM meeting with Priya.",
            "timestamp": "2025-11-20T14:00:00Z",
        }
        result = summarize_message(payload)
        required = {
            "summary_id", "user_id", "platform", "message_id", "summary",
            "type", "intent", "urgency", "entities", "generated_at"
        }
        self.assertTrue(required.issubset(result.keys()))
        self.assertEqual(result["user_id"], payload["user_id"])  
        self.assertEqual(result["platform"], payload["platform"])  
        self.assertEqual(result["message_id"], payload["message_id"])  

    # 2. Type / intent classification
    def test_classification_meeting(self):
        payload = {
            "user_id": "u1",
            "platform": "email",
            "message_id": "m-meet",
            "message_text": "Please confirm the meeting at 3 PM with Alex.",
            "timestamp": "2025-11-20T09:00:00Z",
        }
        r = summarize_message(payload)
        self.assertEqual(r["type"], "meeting")
        self.assertEqual(r["intent"], "confirm_meeting")

    def test_classification_reminder(self):
        payload = {
            "user_id": "u2",
            "platform": "email",
            "message_id": "m-rem",
            "message_text": "Reminder: submit the report by EOD.",
            "timestamp": "2025-11-20T09:00:00Z",
        }
        r = summarize_message(payload)
        self.assertEqual(r["type"], "reminder")
        self.assertEqual(r["intent"], "reminder")

    def test_classification_follow_up(self):
        payload = {
            "user_id": "u3",
            "platform": "slack",
            "message_id": "m-fup",
            "message_text": "Any update on the project status?",
            "timestamp": "2025-11-20T09:00:00Z",
        }
        r = summarize_message(payload)
        self.assertEqual(r["intent"], "follow_up")

    def test_classification_note(self):
        payload = {
            "user_id": "u4",
            "platform": "email",
            "message_id": "m-note",
            "message_text": "FYI - servers will be restarted tonight.",
            "timestamp": "2025-11-20T09:00:00Z",
        }
        r = summarize_message(payload)
        self.assertEqual(r["type"], "note")
        self.assertEqual(r["intent"], "informational")

    # 3. Datetime extraction produces valid ISO8601 when clear
    def test_datetime_extraction(self):
        payload = {
            "user_id": "u5",
            "platform": "whatsapp",
            "message_id": "m-dt",
            "message_text": "Let's meet tomorrow at 5 pm with Priya.",
            "timestamp": "2025-11-20T14:00:00Z",
        }
        r = summarize_message(payload)
        self.assertEqual(r["entities"]["datetime"], "2025-11-21T17:00:00Z")

    # 4. Summary is inserted correctly into DB
    def test_db_insert_and_get(self):
        payload = {
            "user_id": "u6",
            "platform": "email",
            "message_id": "m-db",
            "message_text": "Please confirm the meeting with Priya at 5 PM tomorrow.",
            "timestamp": "2025-11-20T10:00:00Z",
        }
        r = summarize_message(payload)
        fetched = get_summary(r["summary_id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["summary_id"], r["summary_id"])  
        self.assertEqual(fetched["user_id"], payload["user_id"])  
        self.assertEqual(fetched["platform"], payload["platform"])  
        self.assertEqual(fetched["message_id"], payload["message_id"])  
        self.assertEqual(fetched["type"], "meeting")
        self.assertIn("Priya", fetched["entities"].get("person", []))

    # 5. Multi-platform cleaning is correct
    def test_platform_cleaning_whatsapp(self):
        payload = {
            "user_id": "u7",
            "platform": "whatsapp",
            "message_id": "m-wa",
            "message_text": "Helloooo 😂😂 please confirm meeting with Priya tomorrow 5 PM",
            "timestamp": "2025-11-20T09:00:00Z",
        }
        r = summarize_message(payload)
        self.assertEqual(r["type"], "meeting")
        self.assertEqual(r["intent"], "confirm_meeting")
        self.assertIn("Priya", r["entities"].get("person", []))

    def test_platform_cleaning_email(self):
        payload = {
            "user_id": "u8",
            "platform": "email",
            "message_id": "m-em",
            "message_text": "Subject: Meeting with Priya\nHi, confirm 5 PM tomorrow.\n--\nRegards, Sam",
            "timestamp": "2025-11-20T09:00:00Z",
        }
        r = summarize_message(payload)
        # Signature "Sam" should not interfere; Priya should be detected via subject/body
        self.assertIn("Priya", r["entities"].get("person", []))
        self.assertEqual(r["type"], "meeting")

    def test_platform_cleaning_instagram(self):
        payload = {
            "user_id": "u9",
            "platform": "instagram",
            "message_id": "m-ig",
            "message_text": "Check this https://example.com #update replying to 'Your post' We confirm meeting with Priya?",
            "timestamp": "2025-11-20T09:00:00Z",
        }
        r = summarize_message(payload)
        # URLs/hashtags removed; classification still detects meeting intent
        self.assertEqual(r["type"], "meeting")
        self.assertIn(r["intent"], {"confirm_meeting", "request", "question"})
        self.assertIn("Priya", r["entities"].get("person", []))


if __name__ == "__main__":
    unittest.main()