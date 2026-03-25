import unittest
import os
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints import alarms


class TestAlarmEndpoints(unittest.TestCase):
    def test_get_alarms_supports_history_filters(self):
        fake_alarm = SimpleNamespace(id=1, message="告警", device_id=1)
        with patch.object(alarms.AlarmService, "list_alarms", return_value=[fake_alarm]) as mock_list:
            result = alarms.get_alarms(limit=30, device_id=1, resolved=True, start_time=None, end_time=None, session=object())

        mock_list.assert_called_once()
        self.assertEqual(result[0].id, 1)

    def test_resolve_alarm_records_operator(self):
        user = SimpleNamespace(username="admin")
        session = object()
        with patch.object(alarms.AlarmService, "resolve_alarm", return_value=True) as mock_resolve:
            result = alarms.resolve_alarm(
                alarm_id=3,
                handling_note="已复位",
                session=session,
                current_user=user,
            )

        mock_resolve.assert_called_once_with(
            session,
            3,
            resolved_by="admin",
            handling_note="已复位",
        )
        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()
