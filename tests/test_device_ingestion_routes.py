import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import devices
from app.api.endpoints.devices import ingestion_health, management


class DeviceIngestionRoutesTest(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(devices.router, prefix="/devices")
        fake_user = SimpleNamespace(username="admin", role="admin")
        self.app.dependency_overrides[ingestion_health.ADMIN_ONLY] = lambda: fake_user
        self.app.dependency_overrides[management.get_current_user] = lambda: fake_user
        self.app.dependency_overrides[ingestion_health.get_session] = lambda: object()
        self.app.dependency_overrides[management.get_session] = lambda: object()
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()

    def test_ingestion_records_route_is_not_shadowed_by_device_detail_route(self):
        mocked_record = SimpleNamespace(
            id=9,
            device_id=16,
            topic="campus/telemetry",
            status="success",
            raw_payload="{}",
            error_reason=None,
            duplicate_count=0,
            replay_count=0,
            retry_count=0,
            next_retry_at=None,
            received_at=datetime(2026, 4, 23, 12, 0, 0),
            last_seen_at=datetime(2026, 4, 23, 12, 0, 1),
            last_replayed_at=None,
            telemetry_timestamp=None,
        )

        with patch.object(
            ingestion_health.MqttReliabilityService,
            "list_records",
            return_value=[mocked_record],
        ):
            response = self.client.get("/devices/ingestion-records?limit=20")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(len(payload["data"]["items"]), 1)
        self.assertEqual(payload["data"]["items"][0]["id"], 9)


if __name__ == "__main__":
    unittest.main()
