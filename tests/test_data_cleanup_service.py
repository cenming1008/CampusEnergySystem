import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.services.data_cleanup_service import (
    _count_carbon_rows_to_delete,
    _count_unresolved_alarms_to_delete,
    _run_vacuum_analyze,
)


class TestDataCleanupService(unittest.TestCase):
    def test_count_unresolved_alarms_to_delete_handles_tuple_result(self):
        session = MagicMock()
        result = MagicMock()
        result.one.return_value = (4,)
        session.exec.return_value = result

        count = _count_unresolved_alarms_to_delete(session, datetime(2026, 3, 24))

        self.assertEqual(count, 4)

    def test_count_carbon_rows_to_delete_handles_scalar_result(self):
        session = MagicMock()
        result = MagicMock()
        result.one.return_value = 9
        session.exec.return_value = result

        count = _count_carbon_rows_to_delete(session, datetime(2026, 3, 24))

        self.assertEqual(count, 9)

    @patch("app.services.data_cleanup_service.logger")
    @patch("app.services.data_cleanup_service.engine")
    def test_run_vacuum_analyze_uses_autocommit_connection(self, mock_engine, mock_logger):
        connection = MagicMock()
        execution_connection = MagicMock()
        execution_connection.__enter__.return_value = connection
        execution_connection.__exit__.return_value = False

        mock_engine.connect.return_value.execution_options.return_value = execution_connection

        _run_vacuum_analyze()

        mock_engine.connect.assert_called_once()
        mock_engine.connect.return_value.execution_options.assert_called_once_with(isolation_level="AUTOCOMMIT")
        connection.execute.assert_called_once()
        mock_logger.debug.assert_called_with("执行了 VACUUM ANALYZE 优化")


if __name__ == "__main__":
    unittest.main()
