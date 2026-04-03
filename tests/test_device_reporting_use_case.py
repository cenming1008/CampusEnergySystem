import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.application.device_reporting import report_device_data_ingestion_use_case


class DeviceReportingIngestionUseCaseTest(unittest.TestCase):
    @patch("app.application.device_reporting.audit_log")
    @patch("app.application.device_reporting.EnergyService.save_energy_data")
    @patch("app.application.device_reporting.normalize_device_report_payload")
    def test_report_device_data_ingestion_use_case_saves_energy_and_audits(
        self,
        mock_normalize_payload,
        mock_save_energy_data,
        mock_audit_log,
    ):
        session = MagicMock()
        session.get.return_value = SimpleNamespace(device_type="load", energy_type="electricity")
        mock_normalize_payload.return_value = SimpleNamespace(
            consumption=2.5,
            flow_rate=1.1,
            optional_fields={"voltage": 220.0},
        )
        fake_record = SimpleNamespace(device_id=7)
        mock_save_energy_data.return_value = fake_record

        result = report_device_data_ingestion_use_case(
            session=session,
            device_id=7,
            data={"consumption": 2.5},
            timestamp=datetime(2026, 4, 3, 9, 0, 0),
        )

        self.assertIs(result, fake_record)
        session.get.assert_called_once()
        mock_save_energy_data.assert_called_once()
        mock_audit_log.assert_called_once_with("device.report_data", "mqtt-ingestion", "device:7")

    def test_report_device_data_ingestion_use_case_raises_for_missing_device(self):
        session = MagicMock()
        session.get.return_value = None

        with self.assertRaises(ValueError) as ctx:
            report_device_data_ingestion_use_case(
                session=session,
                device_id=404,
                data={"consumption": 1.0},
            )

        self.assertEqual(str(ctx.exception), "设备不存在")


if __name__ == "__main__":
    unittest.main()
