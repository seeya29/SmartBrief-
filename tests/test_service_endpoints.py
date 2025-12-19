import os
import unittest
from fastapi.testclient import TestClient

from summaryflow_service.main import app


class TestServiceEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        db_path = os.path.join(os.path.dirname(__file__), "..", "assistant_core.db")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("version"), "v4")

    def test_summarize_and_history(self):
        payload = {
            "user_id": "u1",
            "platform": "whatsapp",
            "message_id": "m1",
            "message_text": "Let's meet tomorrow at 5 pm with Priya.",
            "timestamp": "2025-12-05T09:00:00Z",
        }
        r = self.client.post("/summarize", json=payload)
        self.assertEqual(r.status_code, 200)
        out = r.json()
        self.assertIn("summary_id", out)
        sid = out["summary_id"]
        hr = self.client.get(f"/history/{sid}")
        self.assertEqual(hr.status_code, 200)
        hist = hr.json()
        self.assertEqual(hist.get("summary"), out.get("summary"))
        self.assertEqual(hist.get("intent"), out.get("intent"))

    def test_classify(self):
        payload = {
            "user_id": "u2",
            "platform": "email",
            "message_id": "m2",
            "message_text": "Reminder: submit the report by EOD.",
            "timestamp": "2025-12-05T09:00:00Z",
        }
        r = self.client.post("/classify", json=payload)
        self.assertEqual(r.status_code, 200)
        out = r.json()
        self.assertIn(out["intent"], ["meeting", "reminder", "question", "task", "note"])
        self.assertIn(out["urgency"], ["low", "medium", "high"])

    def test_entities(self):
        payload = {
            "user_id": "u3",
            "platform": "email",
            "message_id": "m3",
            "message_text": "Please confirm meeting with Alex at 5pm tomorrow.",
            "timestamp": "2025-12-05T09:00:00Z",
        }
        r = self.client.post("/entities", json=payload)
        self.assertEqual(r.status_code, 200)
        out = r.json()
        self.assertIn("person", out)
        self.assertIsInstance(out["person"], list)


if __name__ == "__main__":
    unittest.main()
