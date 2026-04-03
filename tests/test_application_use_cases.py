import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.application.analysis import analyze_device_use_case
from app.application.device_reporting import report_device_data_use_case
from app.application.device_reporting import (
    get_device_data_use_case,
    get_device_statistics_use_case,
)
from app.application.energy_management import (
    get_carbon_summary_use_case,
    get_energy_statistics_use_case,
    save_energy_data_use_case,
)
from app.application.forecasting import (
    evaluate_prediction_accuracy_use_case,
    forecast_load_use_case,
    train_lstm_model_use_case,
)
from app.application.reporting import list_energy_report_rows_use_case
from app.application.reporting import build_report_csv_export_use_case
from app.application.telemetry_ingestion import ingest_telemetry_use_case


class TestApplicationUseCases(unittest.TestCase):
    @patch("app.application.device_reporting.audit_log")
    @patch("app.application.device_reporting.EnergyService.save_energy_data")
    @patch("app.application.device_reporting.normalize_device_report_payload")
    @patch("app.application.device_reporting.ensure_device_access")
    def test_report_device_data_use_case_orchestrates_access_audit_and_energy_save(
        self,
        mock_ensure_access,
        mock_normalize_payload,
        mock_save_energy_data,
        mock_audit_log,
    ):
        session = MagicMock()
        current_user = SimpleNamespace(username="admin", role="admin")
        mock_ensure_access.return_value = SimpleNamespace(device_type="load", energy_type="electricity")
        mock_normalize_payload.return_value = SimpleNamespace(
            consumption=1.2,
            flow_rate=0.8,
            optional_fields={"voltage": 220.0},
        )
        fake_record = SimpleNamespace(device_id=1)
        mock_save_energy_data.return_value = fake_record

        result = report_device_data_use_case(
            session=session,
            current_user=current_user,
            device_id=1,
            data={"consumption": 1.2, "power": 0.8},
            timestamp=datetime(2026, 3, 24, 12, 0, 0),
        )

        self.assertIs(result, fake_record)
        mock_ensure_access.assert_called_once_with(session, current_user, 1)
        mock_save_energy_data.assert_called_once()
        mock_audit_log.assert_called_once()

    @patch("app.application.device_reporting.DeviceService.get_device_data")
    @patch("app.application.device_reporting.ensure_device_access")
    def test_get_device_data_use_case_checks_access_then_reads_service(self, mock_ensure_access, mock_get_device_data):
        session = MagicMock()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        fake_rows = [SimpleNamespace(device_id=1)]
        mock_get_device_data.return_value = fake_rows

        result = get_device_data_use_case(
            session=session,
            current_user=current_user,
            device_id=1,
            start_time=datetime(2026, 3, 24, 0, 0, 0),
            end_time=datetime(2026, 3, 24, 23, 59, 59),
            limit=200,
        )

        self.assertEqual(result, fake_rows)
        mock_ensure_access.assert_called_once_with(session, current_user, 1)
        mock_get_device_data.assert_called_once()

    @patch("app.application.device_reporting.DeviceService.get_device_semantic_profile")
    @patch("app.application.device_reporting.DeviceService.get_device_statistics")
    @patch("app.application.device_reporting.ensure_device_access")
    def test_get_device_statistics_use_case_checks_access_then_reads_service(
        self,
        mock_ensure_access,
        mock_get_device_statistics,
        mock_get_device_semantic_profile,
    ):
        session = MagicMock()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        mock_get_device_statistics.return_value = {"total_consumption": 42}
        mock_get_device_semantic_profile.return_value = {"device_type": "load"}

        result = get_device_statistics_use_case(
            session=session,
            current_user=current_user,
            device_id=1,
            start_time=datetime(2026, 3, 24, 0, 0, 0),
            end_time=datetime(2026, 3, 24, 23, 59, 59),
            period_type="day",
        )

        self.assertEqual(result["total_consumption"], 42)
        self.assertEqual(result["device_semantics"]["device_type"], "load")
        mock_ensure_access.assert_called_once_with(session, current_user, 1)
        mock_get_device_statistics.assert_called_once()

    @patch("app.application.telemetry_ingestion.IngestionHealthService.mark_ingestion_success")
    @patch("app.application.telemetry_ingestion.AlarmService.check_and_create_alarm")
    @patch("app.application.telemetry_ingestion.report_device_data_ingestion_use_case")
    @patch("app.application.telemetry_ingestion.IngestionHealthService.mark_message_received")
    def test_ingest_telemetry_use_case_orchestrates_services(
        self,
        mock_mark_message_received,
        mock_report_device_data,
        mock_check_and_create_alarm,
        mock_mark_ingestion_success,
    ):
        session = MagicMock()
        timestamp = datetime(2026, 3, 24, 12, 0, 0)
        mock_report_device_data.return_value = SimpleNamespace(
            voltage=380.0,
            current=12.0,
            flow_rate=4.56,
            consumption=8.9,
            timestamp=timestamp,
        )

        result = ingest_telemetry_use_case(
            session=session,
            device_id=7,
            data={"consumption": 8.9, "power": 4.56},
            timestamp=timestamp,
        )

        self.assertEqual(result.broadcast_data.device_id, 7)
        self.assertEqual(result.broadcast_data.power, 4.56)
        mock_mark_message_received.assert_called_once()
        mock_report_device_data.assert_called_once()
        mock_check_and_create_alarm.assert_called_once()
        mock_mark_ingestion_success.assert_called_once()

    @patch("app.application.analysis.AnalysisService.analyze_device")
    @patch("app.application.analysis.ensure_device_access")
    def test_analyze_device_use_case_builds_response_in_application(self, mock_ensure_access, mock_analyze_device):
        session = MagicMock()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        mock_analyze_device.return_value = {
            "is_active": True,
            "energy_type": "gas",
            "semantics": {
                "label": "气",
                "flow_label": "实时流量",
                "flow_unit": "m³/h",
                "supports_electrical_quality": False,
                "consumption_label": "累计气量",
                "consumption_unit": "m³",
                "consumption_stat_basis": "period_delta_from_cumulative_reading",
            },
            "latest": SimpleNamespace(flow_rate=4.567, voltage=219.95, current=10.127),
            "today_consumption": 9.812,
            "today_cost": 5.436,
        }

        result = analyze_device_use_case(session=session, current_user=current_user, device_id=7)

        self.assertEqual(result["device_id"], 7)
        self.assertEqual(result["energy_type"], "gas")
        self.assertEqual(result["today_energy"], 9.81)
        self.assertEqual(result["current_power"], 4.57)
        self.assertEqual(result["today_consumption_unit"], "m³")
        mock_ensure_access.assert_called_once_with(session, current_user, 7)
        mock_analyze_device.assert_called_once_with(session, 7)

    @patch("app.application.reporting.ReportService.list_energy_report_rows")
    def test_list_energy_report_rows_use_case_delegates_to_report_service(self, mock_list_rows):
        session = MagicMock()
        mock_list_rows.return_value = [(SimpleNamespace(device_id=1), "Device A")]

        result = list_energy_report_rows_use_case(session=session, limit=123)

        self.assertEqual(len(result), 1)
        mock_list_rows.assert_called_once_with(
            session=session,
            current_user=None,
            device_id=None,
            energy_type=None,
            start_time=None,
            end_time=None,
            limit=123,
        )

    @patch("app.application.reporting.list_energy_report_rows_use_case")
    def test_build_report_csv_export_use_case_builds_csv_payload(self, mock_list_energy_rows):
        session = MagicMock()
        mock_list_energy_rows.return_value = [
            (
                SimpleNamespace(
                    timestamp=SimpleNamespace(strftime=lambda fmt: "2026-03-26 10:00:00"),
                    device_id=1,
                    energy_type="electricity",
                    voltage=380.0,
                    current=10.0,
                    flow_rate=5.5,
                    consumption=12.3,
                ),
                "一号设备",
                "load",
                "load",
            )
        ]

        payload = build_report_csv_export_use_case(
            session=session,
            current_user=None,
            report_type="energy_detail",
            limit=10,
        )

        self.assertEqual(payload.filename, f"energy_detail_{datetime.now().strftime('%Y%m%d')}.csv")
        self.assertIn("设备名称", payload.content)
        self.assertIn("一号设备", payload.content)
        self.assertIn("对象语义", payload.content)

    @patch("app.application.reporting.EnergyService.get_carbon_summary")
    @patch("app.application.reporting.EnergyService.get_statistics_by_type")
    @patch("app.application.reporting.get_allowed_device_ids", return_value=None)
    @patch("app.application.reporting.EnergyService.list_energy_type_catalog")
    def test_build_report_csv_export_use_case_supports_multi_energy_summary(
        self,
        mock_catalog,
        mock_allowed_ids,
        mock_statistics,
        mock_carbon_summary,
    ):
        session = MagicMock()
        mock_catalog.return_value = [
            {"energy_type": "electricity"},
            {"energy_type": "heat"},
        ]
        mock_statistics.return_value = {
            "electricity": {
                "total_consumption": 10.5,
                "avg_flow_rate": 4.0,
                "peak_flow_rate": 6.2,
                "data_count": 3,
                "consumption_unit": "kWh",
                "flow_unit": "kW",
            },
            "heat": {
                "total_consumption": 0.0,
                "avg_flow_rate": 0.0,
                "peak_flow_rate": 0.0,
                "data_count": 0,
                "consumption_unit": "GJ",
                "flow_unit": "GJ/h",
            },
        }
        mock_carbon_summary.return_value = {
            "boundary": "display_estimate",
            "by_energy_type": {
                "electricity": {"carbon_emission": 6.13, "boundary": "display_estimate"},
            },
        }

        payload = build_report_csv_export_use_case(
            session=session,
            current_user=None,
            report_type="multi_energy_summary",
            start_time=datetime(2026, 3, 1),
            end_time=datetime(2026, 3, 2),
        )

        self.assertIn("能源类型", payload.content)
        self.assertIn("电", payload.content)
        self.assertIn("display_estimate", payload.content)

    @patch("app.application.energy_management.EnergyService.save_energy_data")
    def test_save_energy_data_use_case_delegates_to_energy_service(self, mock_save_energy_data):
        session = MagicMock()
        fake_record = SimpleNamespace(device_id=2)
        mock_save_energy_data.return_value = fake_record

        result = save_energy_data_use_case(
            session=session,
            device_id=2,
            energy_type="water",
            consumption=12.5,
            flow_rate=1.5,
        )

        self.assertIs(result, fake_record)
        mock_save_energy_data.assert_called_once()

    @patch("app.application.energy_management.EnergyService.calculate_statistics")
    def test_get_energy_statistics_use_case_delegates_to_energy_service(self, mock_calculate_statistics):
        session = MagicMock()
        mock_calculate_statistics.return_value = {"total_consumption": 5.0}

        result = get_energy_statistics_use_case(
            session=session,
            energy_type="electricity",
            start_time=datetime(2026, 3, 1),
            end_time=datetime(2026, 3, 24),
            device_id=1,
            period_type="day",
        )

        self.assertEqual(result["total_consumption"], 5.0)
        mock_calculate_statistics.assert_called_once()

    @patch("app.application.energy_management.EnergyService.get_carbon_summary")
    def test_get_carbon_summary_use_case_delegates_to_energy_service(self, mock_get_carbon_summary):
        session = MagicMock()
        mock_get_carbon_summary.return_value = {"total_carbon": 1.23}

        result = get_carbon_summary_use_case(
            session=session,
            start_time=datetime(2026, 3, 1),
            end_time=datetime(2026, 3, 24),
            device_id=1,
        )

        self.assertEqual(result["total_carbon"], 1.23)
        mock_get_carbon_summary.assert_called_once()

    @patch("app.application.forecasting.get_forecast_adapter")
    def test_forecast_load_use_case_delegates_to_adapter(self, mock_get_forecast_adapter):
        session = MagicMock()
        adapter = MagicMock()
        adapter.forecast_load.return_value = [{"forecast_time": "t1", "predicted_value": 4.2}]
        mock_get_forecast_adapter.return_value = adapter

        result = forecast_load_use_case(
            session=session,
            device_id=1,
            hours=24,
            algorithm="moving_average",
        )

        self.assertEqual(result["count"], 1)
        adapter.forecast_load.assert_called_once()

    @patch("app.application.forecasting.get_forecast_adapter")
    def test_evaluate_prediction_accuracy_use_case_delegates_to_adapter(self, mock_get_forecast_adapter):
        session = MagicMock()
        adapter = MagicMock()
        adapter.evaluate_prediction_accuracy.return_value = {"mae": 1.0, "count": 3}
        mock_get_forecast_adapter.return_value = adapter

        result = evaluate_prediction_accuracy_use_case(
            session=session,
            prediction_type="load",
            device_id=1,
            days=7,
        )

        self.assertEqual(result["mae"], 1.0)
        adapter.evaluate_prediction_accuracy.assert_called_once()

    @patch("app.application.forecasting.get_forecast_adapter")
    def test_train_lstm_model_use_case_generates_version_when_missing(self, mock_get_forecast_adapter):
        session = MagicMock()
        adapter = MagicMock()
        adapter.train_lstm_model.return_value = {"status": "success"}
        mock_get_forecast_adapter.return_value = adapter

        result = train_lstm_model_use_case(
            session=session,
            prediction_type="load",
            device_id=1,
            days=60,
        )

        self.assertEqual(result["status"], "success")
        self.assertTrue(adapter.train_lstm_model.call_args.kwargs["version"].startswith("v"))


if __name__ == "__main__":
    unittest.main()
