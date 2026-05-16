import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.devices import storage
from app.models.storage import StorageTelemetry


def _make_user() -> SimpleNamespace:
    return SimpleNamespace(role="admin", id=1, username="tester", location_scope=None)


class TestStorageNestedApi(unittest.TestCase):
    def test_storage_telemetry_latest_uses_service(self):
        user = _make_user()
        mock_session = object()
        telemetry = StorageTelemetry(device_id=1, timestamp=datetime.fromisoformat("2026-04-14T10:00:00"))
        with patch.object(storage, "ensure_device_access") as mock_access:
            with patch.object(storage.StorageMonitorService, "get_latest_telemetry", return_value=telemetry) as mock_get:
                result = storage.get_storage_telemetry_latest(1, mock_session, user)

        mock_access.assert_called_once_with(mock_session, user, 1)
        mock_get.assert_called_once_with(mock_session, 1)
        self.assertEqual(result, telemetry)

    def test_storage_telemetry_latest_returns_404_when_missing(self):
        user = _make_user()
        mock_session = object()
        with patch.object(storage, "ensure_device_access"):
            with patch.object(storage.StorageMonitorService, "get_latest_telemetry", return_value=None):
                with self.assertRaises(HTTPException) as ctx:
                    storage.get_storage_telemetry_latest(1, mock_session, user)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "暂无遥测数据")

    def test_storage_telemetry_history_uses_service(self):
        user = _make_user()
        mock_session = object()
        start = datetime.fromisoformat("2026-04-14T10:00:00")
        end = datetime.fromisoformat("2026-04-14T11:00:00")
        expected = [StorageTelemetry(device_id=1, timestamp=start)]
        with patch.object(storage, "ensure_device_access") as mock_access:
            with patch.object(storage.StorageMonitorService, "list_telemetry_history", return_value=expected) as mock_list:
                result = storage.get_storage_telemetry_history(
                    1,
                    start,
                    end,
                    50,
                    mock_session,
                    user,
                )

        mock_access.assert_called_once_with(mock_session, user, 1)
        mock_list.assert_called_once_with(mock_session, 1, start_time=start, end_time=end, limit=50)
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
