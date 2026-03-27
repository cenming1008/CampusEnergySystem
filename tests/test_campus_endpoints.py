import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints import campus


class TestCampusEndpoints(unittest.TestCase):
    def test_get_campus_overview_uses_allowed_device_scope(self):
        fake_user = SimpleNamespace(role="admin")
        fake_session = object()
        fake_payload = {"campus_entities": []}

        with patch.object(campus, "get_allowed_device_ids", return_value={1, 2}) as mock_allowed:
            with patch.object(campus.CampusService, "get_campus_overview", return_value=fake_payload) as mock_service:
                result = campus.get_campus_overview(
                    start_time=datetime(2026, 3, 1, 0, 0, 0),
                    end_time=datetime(2026, 3, 2, 0, 0, 0),
                    session=fake_session,
                    current_user=fake_user,
                )

        mock_allowed.assert_called_once_with(fake_session, fake_user)
        mock_service.assert_called_once()
        self.assertIs(result, fake_payload)

    def test_get_alarm_summary_uses_default_window(self):
        fake_user = SimpleNamespace(role="admin")
        fake_session = object()
        fake_payload = {
            "time_window": {
                "start_time": datetime(2026, 3, 1, 0, 0, 0),
                "end_time": datetime(2026, 3, 2, 0, 0, 0),
            },
            "total_count": 0,
            "unresolved_count": 0,
            "resolved_count": 0,
            "by_severity": {},
            "top_locations": [],
            "latest": [],
        }

        with patch.object(campus, "get_allowed_device_ids", return_value=None):
            with patch.object(campus.CampusService, "get_alarm_summary", return_value=fake_payload) as mock_service:
                result = campus.get_alarm_summary(
                    start_time=None,
                    end_time=datetime(2026, 3, 2, 0, 0, 0),
                    session=fake_session,
                    current_user=fake_user,
                )

        mock_service.assert_called_once()
        self.assertEqual(result["total_count"], 0)


if __name__ == "__main__":
    unittest.main()
