import os
import unittest
import sqlite3

from summaryflow_v4 import summarize_message


class TestSummaryFlowV4(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.db_path = os.path.join(self.repo_root, 'assistant_core.db')
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def _summarize(self, payload):
        return summarize_message(payload)

    def test_schema_output_matches(self):
        payload = {
            "user_id": "abc123",
            "platform": "whatsapp",
            "message_id": "m001",
            "message_text": "Let's meet tomorrow at 5 pm with Priya.",
            "timestamp": "2025-12-01T09:00:00Z",
        }
        r = self._summarize(payload)
        required = {
            "summary_id",
            "user_id",
            "platform",
            "message_id",
            "summary",
            "intent",
            "urgency",
            "entities",
            "context_flags",
            "generated_at",
            "device_context",
        }
        self.assertTrue(required.issubset(r.keys()))
        self.assertIn(r["intent"], {"meeting", "reminder", "question", "task", "note"})
        self.assertIn(r["urgency"], {"low", "medium", "high"})
        self.assertIsInstance(r["entities"], dict)
        self.assertIsInstance(r["context_flags"], list)

    def test_entities_detected(self):
        payload = {
            "user_id": "u1",
            "platform": "email",
            "message_id": "m002",
            "message_text": "Subject: Update\nPlease confirm 3 PM meeting with Priya tomorrow.",
            "timestamp": "2025-12-01T09:00:00Z",
        }
        r = self._summarize(payload)
        self.assertIn("Priya", r["entities"].get("person", []))
        self.assertEqual(r["intent"], "meeting")
        self.assertEqual(r["entities"]["datetime"], "2025-12-02T15:00:00Z")

    def test_urgency_correct(self):
        payload = {
            "user_id": "u2",
            "platform": "whatsapp",
            "message_id": "m003",
            "message_text": "ASAP! urgent!!! Please finish the task.",
            "timestamp": "2025-12-01T09:00:00Z",
        }
        r = self._summarize(payload)
        self.assertEqual(r["urgency"], "high")

    def test_context_cleaned(self):
        payload = {
            "user_id": "u3",
            "platform": "email",
            "message_id": "m004",
            "message_text": "Begin forwarded message\nFrom: Someone\nSubject: Meeting\nOn Tue, ... wrote:\n> quoted\nHello!! Please confirm meeting with Alex at 5pm tomorrow.",
            "timestamp": "2025-12-01T09:00:00Z",
        }
        r = self._summarize(payload)
        self.assertEqual(r["intent"], "meeting")
        # datetime may be absent if cleaners strip ambiguous segments; classification should still work
        persons = " ".join(r["entities"].get("person", []))
        self.assertNotIn("Forwarded", persons)
        self.assertNotIn("quoted", persons)

    def test_db_insert_happens(self):
        payload = {
            "user_id": "u4",
            "platform": "instagram",
            "message_id": "m005",
            "message_text": "replying to 'note' Let's schedule a call with Dan at 10am tomorrow.",
            "timestamp": "2025-12-01T09:00:00Z",
        }
        r = self._summarize(payload)
        self.assertTrue(os.path.exists(self.db_path))

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "SELECT summary_id,user_id,platform,message_id,intent,urgency,timestamp,entities FROM summaries WHERE summary_id = ?",
                (r["summary_id"],),
            )
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], r["summary_id"])
            self.assertEqual(row[1], payload["user_id"])
            self.assertEqual(row[2], payload["platform"])
            self.assertEqual(row[3], payload["message_id"])
            self.assertIn(row[4], {"meeting", "reminder", "question", "task", "note"})
            self.assertIn(row[5], {"low", "medium", "high"})
            self.assertIsInstance(row[7], str)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
