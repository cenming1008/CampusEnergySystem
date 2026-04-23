import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.services.data_cleanup_service import (
    CLEANUP_RESULT_KEYS,
    _count_carbon_rows_to_delete,
    _count_unresolved_alarms_to_delete,
    _run_vacuum_analyze,
    cleanup_all_runtime_data,
    cleanup_old_data,
    cleanup_runtime_data_before,
)


class TestDataCleanupService(unittest.TestCase):
    def _cleanup_result(self, **counts):
        result = {"status": "success", "errors": []}
        for key in CLEANUP_RESULT_KEYS:
            result[key] = counts.get(key, 0)
        result["total_deleted"] = sum(result[key] for key in CLEANUP_RESULT_KEYS)
        return result

    def test_count_unresolved_alarms_to_delete_handles_tuple_result(self):
        session = MagicMock()
        result = MagicMock()
        result.scalar.return_value = 4
        session.execute.return_value = result

        count = _count_unresolved_alarms_to_delete(session, datetime(2026, 3, 24))

        self.assertEqual(count, 4)

    def test_count_carbon_rows_to_delete_handles_scalar_result(self):
        session = MagicMock()
        result = MagicMock()
        result.scalar.return_value = 9
        session.execute.return_value = result

        count = _count_carbon_rows_to_delete(session, datetime(2026, 3, 24))

        self.assertEqual(count, 9)

    def test_cleanup_runtime_data_before_covers_fast_growing_tables(self):
        session = MagicMock()
        session.execute.return_value.scalar.side_effect = [2, 3, 5, 7, 11, 13, 17]

        result = cleanup_runtime_data_before(session, datetime(2026, 4, 23, 12, 0, 0), hours=6)

        self.assertEqual(result["energy_data"], 2)
        self.assertEqual(result["alarm_data"], 3)
        self.assertEqual(result["carbon_emission"], 5)
        self.assertEqual(result["mqtt_ingestion"], 7)
        self.assertEqual(result["audit_event"], 11)
        self.assertEqual(result["svg_telemetry"], 13)
        self.assertEqual(result["capacitor_bank_telemetry"], 17)
        self.assertEqual(result["total_deleted"], 58)
        executed_sql = "\n".join(str(call.args[0]) for call in session.execute.call_args_list)
        self.assertIn("mqtt_ingestion_record", executed_sql)
        self.assertIn("audit_event", executed_sql)
        self.assertIn("svg_telemetry", executed_sql)
        self.assertIn("capacitor_bank_telemetry", executed_sql)

    def test_cleanup_all_runtime_data_clears_runtime_tables_without_master_data(self):
        session = MagicMock()
        session.execute.return_value.scalar.side_effect = [1, 2, 3, 4, 5, 6, 7, 8]

        result = cleanup_all_runtime_data(session)

        for key in CLEANUP_RESULT_KEYS:
            self.assertIn(key, result)
        self.assertEqual(result["total_deleted"], 36)
        executed_sql = "\n".join(str(call.args[0]) for call in session.execute.call_args_list)
        self.assertIn("energy_statistics", executed_sql)
        self.assertNotIn("TRUNCATE TABLE device", executed_sql)
        self.assertNotIn("TRUNCATE TABLE user", executed_sql)
        self.assertNotIn("TRUNCATE TABLE location", executed_sql)

    @patch("app.services.data_cleanup_service._run_vacuum_analyze")
    @patch("app.services.data_cleanup_service.cleanup_targets_before")
    @patch("app.services.data_cleanup_service.Session")
    def test_cleanup_old_data_covers_fast_growing_tables_and_totals(
        self,
        mock_session_factory,
        mock_cleanup_targets_before,
        mock_vacuum,
    ):
        session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = session
        mock_cleanup_targets_before.side_effect = [
            self._cleanup_result(energy_data=2, carbon_emission=3, svg_telemetry=5, capacitor_bank_telemetry=7),
            self._cleanup_result(alarm_data=11),
            self._cleanup_result(statistics=13),
            self._cleanup_result(mqtt_ingestion=17),
            self._cleanup_result(audit_event=19),
        ]

        with patch.multiple(
            "app.services.data_cleanup_service.settings",
            enable_auto_cleanup=True,
            data_retention_days=7,
            alarm_retention_days=7,
            statistics_retention_days=7,
            mqtt_ingestion_retention_days=3,
            audit_event_retention_days=3,
        ):
            result = cleanup_old_data()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["svg_telemetry"], 5)
        self.assertEqual(result["capacitor_bank_telemetry"], 7)
        self.assertEqual(result["mqtt_ingestion"], 17)
        self.assertEqual(result["audit_event"], 19)
        self.assertEqual(result["total_deleted"], 77)
        mock_vacuum.assert_called_once()

        target_sql = "\n".join(
            table_name
            for call in mock_cleanup_targets_before.call_args_list
            for _key, table_name, _time_column, _where_clause in call.args[2]
        )
        self.assertIn("svg_telemetry", target_sql)
        self.assertIn("capacitor_bank_telemetry", target_sql)
        self.assertIn("mqtt_ingestion_record", target_sql)
        self.assertIn("audit_event", target_sql)

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
