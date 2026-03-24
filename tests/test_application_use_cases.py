import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.application.device_reporting import report_device_data_use_case
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
from app.application.telemetry_ingestion import ingest_telemetry_use_case


class TestApplicationUseCases(unittest.TestCase):
    @patch("app.application.device_reporting.DeviceService.report_device_data")
    def test_report_device_data_use_case_delegates_to_device_service(self, mock_report_device_data):
        session = MagicMock()
        fake_record = SimpleNamespace(device_id=1)
        mock_report_device_data.return_value = fake_record

        result = report_device_data_use_case(
            session=session,
            device_id=1,
            data={"consumption": 1.2, "power": 0.8},
            timestamp=datetime(2026, 3, 24, 12, 0, 0),
        )

        self.assertIs(result, fake_record)
        mock_report_device_data.assert_called_once()

    @patch("app.application.telemetry_ingestion.IngestionHealthService.mark_ingestion_success")
    @patch("app.application.telemetry_ingestion.AlarmService.check_and_create_alarm")
    @patch("app.application.telemetry_ingestion.report_device_data_use_case")
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
