import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import data_cleanup
from app.api.endpoints.data_cleanup import admin, basic


class DataCleanupEndpointsTest(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(data_cleanup.router, prefix="/data-cleanup")
        fake_user = SimpleNamespace(username="admin")
        self.app.dependency_overrides[basic.ADMIN_ONLY] = lambda: fake_user
        self.app.dependency_overrides[admin.ADMIN_ONLY] = lambda: fake_user
        self.app.dependency_overrides[basic.get_session] = lambda: object()
        self.app.dependency_overrides[admin.get_session] = lambda: object()
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()

    def test_cleanup_endpoint_returns_all_cleanup_categories(self):
        mocked_result = {
            "status": "success",
            "total_deleted": 58,
            "energy_data": 2,
            "alarm_data": 3,
            "carbon_emission": 5,
            "statistics": 0,
            "mqtt_ingestion": 7,
            "audit_event": 11,
            "svg_telemetry": 13,
            "capacitor_bank_telemetry": 17,
            "errors": [],
            "hours": 6,
            "cutoff_time": "2026-04-23T06:00:00",
            "timestamp": "2026-04-23T12:00:00",
        }

        with patch.object(basic, "cleanup_runtime_data_before", return_value=mocked_result), patch.object(
            basic, "audit_log"
        ):
            response = self.client.post("/data-cleanup/cleanup?hours=6")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        data = payload["data"]
        self.assertEqual(data["total_deleted"], 58)
        self.assertEqual(data["mqtt_ingestion"], 7)
        self.assertEqual(data["audit_event"], 11)
        self.assertEqual(data["svg_telemetry"], 13)
        self.assertEqual(data["capacitor_bank_telemetry"], 17)

    def test_cleanup_all_endpoint_excludes_master_data_categories(self):
        mocked_result = {
            "status": "partial",
            "total_deleted": 180,
            "energy_data": 100,
            "alarm_data": 20,
            "carbon_emission": 15,
            "statistics": 10,
            "mqtt_ingestion": 12,
            "audit_event": 8,
            "svg_telemetry": 9,
            "capacitor_bank_telemetry": 6,
            "errors": ["清空 audit_event 失败: lock timeout"],
            "timestamp": "2026-04-23T12:00:00",
        }

        with patch.object(admin, "cleanup_all_runtime_data", return_value=mocked_result), patch.object(admin, "audit_log"):
            response = self.client.post("/data-cleanup/cleanup-all")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        data = payload["data"]
        self.assertEqual(data["status"], "partial")
        self.assertEqual(data["statistics"], 10)
        self.assertIn("errors", data)
        self.assertNotIn("device", data)
        self.assertNotIn("user", data)
        self.assertNotIn("location", data)
        self.assertNotIn("device_control_log", data)


if __name__ == "__main__":
    unittest.main()
