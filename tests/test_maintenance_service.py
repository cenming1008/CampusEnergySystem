import os
import unittest
from unittest.mock import MagicMock

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.services.maintenance_service import MaintenanceService


class TestMaintenanceService(unittest.TestCase):
    def test_get_maintenance_list_returns_empty_for_empty_allowed_scope(self):
        session = MagicMock()

        result = MaintenanceService.get_maintenance_list(
            session=session,
            allowed_device_ids=set(),
        )

        self.assertEqual(result, [])
        session.exec.assert_not_called()

    def test_get_upcoming_maintenance_returns_empty_for_empty_allowed_scope(self):
        session = MagicMock()

        result = MaintenanceService.get_upcoming_maintenance(
            session=session,
            allowed_device_ids=set(),
        )

        self.assertEqual(result, [])
        session.exec.assert_not_called()

    def test_get_maintenance_statistics_returns_zero_summary_for_empty_scope(self):
        session = MagicMock()

        result = MaintenanceService.get_maintenance_statistics(
            session=session,
            allowed_device_ids=set(),
        )

        self.assertEqual(result["total_count"], 0)
        self.assertEqual(result["cost_statistics"]["total_cost"], 0)
        self.assertEqual(result["duration_statistics"]["completed_count"], 0)
        session.exec.assert_not_called()


if __name__ == "__main__":
    unittest.main()
