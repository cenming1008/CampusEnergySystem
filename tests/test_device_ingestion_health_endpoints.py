import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.devices import ingestion_health


class DeviceIngestionHealthEndpointTest(unittest.TestCase):
    def test_get_device_ingestion_health_enforces_device_access(self):
        session = object()
        current_user = SimpleNamespace(role="viewer", location_scope="1")

        with patch.object(ingestion_health, "ensure_device_access") as mock_ensure_access:
            with patch.object(
                ingestion_health.IngestionHealthService,
                "get_device_health",
                return_value={"device_id": 5, "status": "online"},
            ) as mock_get_health:
                result = ingestion_health.get_device_ingestion_health(
                    device_id=5,
                    session=session,
                    current_user=current_user,
                )

        mock_ensure_access.assert_called_once_with(session, current_user, 5)
        mock_get_health.assert_called_once_with(session, 5)
        self.assertEqual(result["data"]["device_id"], 5)

    def test_list_device_ingestion_health_filters_by_allowed_device_ids(self):
        session = object()
        current_user = SimpleNamespace(role="viewer", location_scope="2")
        items = [
            {"device_id": 1, "status": "online"},
            {"device_id": 2, "status": "offline"},
        ]

        with patch.object(
            ingestion_health.IngestionHealthService,
            "list_device_health",
            return_value=items,
        ) as mock_list_health:
            with patch.object(ingestion_health, "get_allowed_device_ids", return_value={2}) as mock_allowed_ids:
                result = ingestion_health.list_device_ingestion_health(
                    session=session,
                    current_user=current_user,
                )

        mock_list_health.assert_called_once_with(session)
        mock_allowed_ids.assert_called_once_with(session, current_user)
        self.assertEqual(result["data"]["items"], [{"device_id": 2, "status": "offline"}])
