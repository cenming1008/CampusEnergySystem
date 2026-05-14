import os
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.services.ingestion_health_service import IngestionHealthService


class TestIngestionHealthService(unittest.TestCase):
    def test_mark_message_received_increments_total_messages(self):
        session = MagicMock()
        status = SimpleNamespace(
            device_id=1,
            total_messages=2,
            total_failures=1,
            consecutive_failures=1,
            last_message_at=None,
            last_success_at=None,
            last_failure_at=None,
            last_failure_reason=None,
            updated_at=None,
        )

        with patch.object(IngestionHealthService, "_get_or_create", return_value=status):
            IngestionHealthService.mark_message_received(session, 1, datetime(2026, 3, 24, 12, 0, 0))

        self.assertEqual(status.total_messages, 3)
        session.add.assert_called_once_with(status)

    def test_mark_ingestion_failure_tracks_reason_and_counter(self):
        session = MagicMock()
        status = SimpleNamespace(
            device_id=1,
            total_messages=3,
            total_failures=1,
            consecutive_failures=0,
            last_message_at=None,
            last_success_at=None,
            last_failure_at=None,
            last_failure_reason=None,
            updated_at=None,
        )

        with patch.object(IngestionHealthService, "_get_or_create", return_value=status):
            IngestionHealthService.mark_ingestion_failure(session, 1, "bad payload", datetime(2026, 3, 24, 12, 0, 0))

        self.assertEqual(status.total_failures, 2)
        self.assertEqual(status.consecutive_failures, 1)
        self.assertEqual(status.last_failure_reason, "bad payload")

    def test_mark_ingestion_success_recovers_platform_comm_alarm(self):
        session = MagicMock()
        success_at = datetime(2026, 5, 14, 10, 3, 0)
        status = SimpleNamespace(
            device_id=1,
            total_messages=3,
            total_failures=1,
            consecutive_failures=2,
            last_message_at=None,
            last_success_at=None,
            last_failure_at=None,
            last_failure_reason="timeout",
            updated_at=None,
        )

        with patch.object(IngestionHealthService, "_get_or_create", return_value=status), \
            patch("app.services.alarm_service.AlarmService.sync_platform_comm_alarm") as sync_alarm:
            IngestionHealthService.mark_ingestion_success(session, 1, success_at)

        sync_alarm.assert_called_once_with(
            session=session,
            device_id=1,
            is_offline=False,
            timestamp=success_at,
            last_success_at=success_at,
        )

    def test_get_device_health_creates_platform_comm_alarm_when_offline(self):
        session = MagicMock()
        device = SimpleNamespace(id=1)
        status = SimpleNamespace(
            device_id=1,
            last_success_at=datetime(2026, 5, 14, 9, 50, 0),
        )
        session.get.side_effect = [device, status]
        serialized = {
            "device_id": 1,
            "is_online": False,
            "status": "offline",
            "last_message_at": datetime(2026, 5, 14, 9, 50, 0),
            "last_success_at": datetime(2026, 5, 14, 9, 50, 0),
        }

        with patch.object(IngestionHealthService, "serialize_status", return_value=serialized), \
            patch("app.services.alarm_service.AlarmService.sync_platform_comm_alarm") as sync_alarm:
            result = IngestionHealthService.get_device_health(session, 1)

        self.assertEqual(result, serialized)
        sync_alarm.assert_called_once()
        self.assertEqual(sync_alarm.call_args.kwargs["session"], session)
        self.assertEqual(sync_alarm.call_args.kwargs["device_id"], 1)
        self.assertTrue(sync_alarm.call_args.kwargs["is_offline"])
        self.assertEqual(sync_alarm.call_args.kwargs["last_success_at"], serialized["last_success_at"])

    @patch("app.services.ingestion_health_service.settings")
    def test_serialize_status_returns_online(self, mock_settings):
        mock_settings.mqtt_online_timeout_seconds = 300
        now = datetime.now()
        status = SimpleNamespace(
            device_id=1,
            last_message_at=now,
            last_success_at=now - timedelta(seconds=30),
            last_failure_at=None,
            last_failure_reason=None,
            consecutive_failures=0,
            total_messages=10,
            total_failures=1,
            updated_at=now,
        )

        result = IngestionHealthService.serialize_status(status)

        self.assertTrue(result["is_online"])
        self.assertEqual(result["status"], "online")
        self.assertEqual(result["success_rate"], 90.0)

    @patch("app.services.ingestion_health_service.settings")
    def test_serialize_status_returns_offline_when_timed_out(self, mock_settings):
        mock_settings.mqtt_online_timeout_seconds = 60
        now = datetime.now()
        status = SimpleNamespace(
            device_id=1,
            last_message_at=now - timedelta(minutes=10),
            last_success_at=now - timedelta(minutes=10),
            last_failure_at=now - timedelta(minutes=5),
            last_failure_reason="timeout",
            consecutive_failures=2,
            total_messages=10,
            total_failures=3,
            updated_at=now,
        )

        result = IngestionHealthService.serialize_status(status)

        self.assertFalse(result["is_online"])
        self.assertEqual(result["status"], "offline")


if __name__ == "__main__":
    unittest.main()
