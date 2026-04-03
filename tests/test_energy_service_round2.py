import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.tables import EnergyType
from app.services.energy_service import EnergyService


class EnergyServiceRound2Test(unittest.TestCase):
    def test_list_energy_type_catalog_includes_supported_device_types(self):
        result = EnergyService.list_energy_type_catalog()

        electricity = next(item for item in result if item["category"] == "electricity")
        self.assertIn("supported_device_types", electricity)
        self.assertIn("consumption_unit", electricity)
        self.assertEqual(electricity["energy_type"], "EnergyType.ELECTRICITY")

    def test_get_energy_type_profile_collects_specialized_fields(self):
        profile = EnergyService.get_energy_type_profile("water")

        self.assertEqual(profile["data_object_kind"], "energy_point_series")
        self.assertIn("specialized_fields", profile)
        self.assertIn("public_fields", profile)

    def test_save_energy_data_raises_when_device_missing(self):
        with patch("app.services.energy_service.DeviceRepository.get_by_id", return_value=None):
            with self.assertRaises(ValueError) as ctx:
                EnergyService.save_energy_data(
                    session=MagicMock(),
                    device_id=404,
                    energy_type="electricity",
                    consumption=1.2,
                )

        self.assertIn("不存在", str(ctx.exception))

    def test_save_energy_data_raises_when_energy_type_mismatch(self):
        device = SimpleNamespace(id=7, energy_type="water")

        with patch("app.services.energy_service.DeviceRepository.get_by_id", return_value=device):
            with self.assertRaises(ValueError) as ctx:
                EnergyService.save_energy_data(
                    session=MagicMock(),
                    device_id=7,
                    energy_type="electricity",
                    consumption=2.4,
                )

        self.assertIn("能源类型不匹配", str(ctx.exception))

    def test_calculate_carbon_emission_updates_existing_record_without_commit(self):
        session = MagicMock()
        record = SimpleNamespace(
            carbon_emission=0.0,
            consumption=0.0,
            energy_type="water",
            consumption_unit="m³",
            carbon_factor=0.0,
        )

        with patch("app.services.energy_service.EnergyRepository.get_carbon_record", return_value=record):
            result = EnergyService.calculate_carbon_emission(
                session=session,
                device_id=1,
                energy_type="water",
                consumption=10.0,
                timestamp=datetime(2026, 4, 3, 10, 0, 0),
                auto_commit=False,
            )

        self.assertIs(result, record)
        session.flush.assert_called_once()
        session.commit.assert_not_called()
        session.refresh.assert_called_once_with(record)
        self.assertGreater(record.carbon_emission, 0)

    def test_get_statistics_by_type_returns_zero_payload_when_empty(self):
        with patch("app.services.energy_service.EnergyRepository.list_energy_statistics_rows", return_value=[]):
            result = EnergyService.get_statistics_by_type(
                session=MagicMock(),
                start_time=datetime(2026, 4, 1, 0, 0, 0),
                end_time=datetime(2026, 4, 2, 0, 0, 0),
                energy_types=["electricity"],
            )

        self.assertEqual(result["electricity"]["total_consumption"], 0.0)
        self.assertEqual(result["electricity"]["data_count"], 0)
        self.assertIn("supported_device_types", result["electricity"])

    def test_get_statistics_by_type_uses_summary_when_rows_exist(self):
        fake_rows = [("r1",), ("r2",)]

        with patch("app.services.energy_service.EnergyRepository.list_energy_statistics_rows", return_value=fake_rows):
            with patch("app.services.energy_service.summarize_energy_statistics", return_value={"total_consumption": 8.8, "data_count": 2}):
                result = EnergyService.get_statistics_by_type(
                    session=MagicMock(),
                    start_time=datetime(2026, 4, 1, 0, 0, 0),
                    end_time=datetime(2026, 4, 2, 0, 0, 0),
                    energy_types=["water"],
                )

        self.assertEqual(result["water"]["total_consumption"], 8.8)
        self.assertEqual(result["water"]["data_count"], 2)

    def test_get_carbon_summary_marks_summary_basis(self):
        with patch("app.services.energy_service.EnergyRepository.list_energy_statistics_rows", return_value=[]):
            result = EnergyService.get_carbon_summary(
                session=MagicMock(),
                start_time=datetime(2026, 4, 1, 0, 0, 0),
                end_time=datetime(2026, 4, 2, 0, 0, 0),
            )

        self.assertEqual(result["summary_basis"], "energy_period_delta")
        self.assertIn("total_carbon", result)

    def test_save_statistics_delegates_to_repository(self):
        session = MagicMock()
        fake_saved = SimpleNamespace(id=3)

        with patch("app.services.energy_service.EnergyRepository.save_statistics_record", return_value=fake_saved) as mock_save:
            result = EnergyService.save_statistics(
                session=session,
                device_id=1,
                energy_type=EnergyType.ELECTRICITY,
                stat_time=datetime(2026, 4, 3, 11, 0, 0),
                period_type="day",
                stats={"total_consumption": 12.3, "avg_flow_rate": 1.1, "peak_flow_rate": 2.2, "total_carbon": 5.5},
            )

        self.assertIs(result, fake_saved)
        mock_save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
