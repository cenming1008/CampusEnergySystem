import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.core.exceptions import DatabaseException, ResourceNotFoundException
from app.services.device_service import DeviceService


class DeviceServiceRound2Test(unittest.TestCase):
    def test_get_device_by_id_raises_when_missing(self):
        with patch("app.services.device_service.DeviceRepository.get_by_id", return_value=None):
            with self.assertRaises(ResourceNotFoundException):
                DeviceService.get_device_by_id(session=object(), device_id=404)

    def test_create_device_smart_returns_existing_device_for_duplicate_sn(self):
        existing = SimpleNamespace(id=7, sn="DUP-001")

        with patch.object(DeviceService, "get_device_by_sn", return_value=existing):
            result = DeviceService.create_device_smart(
                session=MagicMock(),
                name="重复设备",
                sn="DUP-001",
                device_type="water_meter",
            )

        self.assertIs(result, existing)

    def test_create_device_smart_wraps_repository_failure(self):
        session = MagicMock()

        with patch.object(DeviceService, "get_device_by_sn", return_value=None):
            with patch("app.services.device_service.build_device_create_fields", return_value={"name": "设备", "sn": "SN-001", "device_type": "load"}):
                with patch("app.services.device_service.get_device_type_config", return_value=SimpleNamespace(energy_type=SimpleNamespace(value="electricity"), category=SimpleNamespace(value="load"))):
                    with patch("app.services.device_service.DeviceRepository.save", side_effect=RuntimeError("db down")):
                        with self.assertRaises(DatabaseException) as ctx:
                            DeviceService.create_device_smart(
                                session=session,
                                name="设备",
                                sn="SN-001",
                                device_type="load",
                            )

        self.assertIn("创建设备失败", str(ctx.exception))
        session.rollback.assert_called_once()

    def test_create_device_autofills_fields_from_registry_config(self):
        session = MagicMock()
        device = SimpleNamespace(
            sn="AUTO-001",
            device_type="water_meter",
            device_category=None,
            energy_type=None,
            unit=None,
            rated_capacity=None,
        )
        config = SimpleNamespace(
            category=SimpleNamespace(value="water_meter"),
            energy_type=SimpleNamespace(value="water"),
            unit="m³",
            default_capacity=9.5,
        )

        with patch("app.services.device_service.device_registry.get", return_value=config):
            with patch("app.services.device_service.DeviceRepository.save", return_value=device) as mock_save:
                result = DeviceService.create_device(session, device)

        self.assertIs(result, device)
        self.assertEqual(device.device_category, "water_meter")
        self.assertEqual(device.energy_type, "water")
        self.assertEqual(device.unit, "m³")
        self.assertEqual(device.rated_capacity, 9.5)
        mock_save.assert_called_once_with(session, device)

    def test_create_device_returns_existing_on_duplicate_after_rollback(self):
        session = MagicMock()
        device = SimpleNamespace(sn="AUTO-002", device_type="load")
        existing = SimpleNamespace(id=9, sn="AUTO-002")

        with patch("app.services.device_service.device_registry.get", return_value=None):
            with patch("app.services.device_service.DeviceRepository.save", side_effect=RuntimeError("duplicate")):
                with patch("app.services.device_service.DeviceRepository.get_by_sn", return_value=existing):
                    result = DeviceService.create_device(session, device)

        self.assertIs(result, existing)
        session.rollback.assert_called_once()

    def test_update_device_updates_fields_and_timestamp(self):
        session = MagicMock()
        device = SimpleNamespace(
            id=3,
            name="旧设备",
            location="旧位置",
            description="旧描述",
            rated_capacity=1.0,
            updated_at=None,
        )

        with patch.object(DeviceService, "get_device_by_id", return_value=device):
            with patch("app.services.device_service.DeviceRepository.save", return_value=device) as mock_save:
                result = DeviceService.update_device(
                    session=session,
                    device_id=3,
                    name="新设备",
                    location="新位置",
                    description="新描述",
                    rated_capacity=2.5,
                )

        self.assertIs(result, device)
        self.assertEqual(device.name, "新设备")
        self.assertEqual(device.location, "新位置")
        self.assertEqual(device.description, "新描述")
        self.assertEqual(device.rated_capacity, 2.5)
        self.assertIsInstance(device.updated_at, datetime)
        mock_save.assert_called_once_with(session, device)

    def test_get_device_data_delegates_energy_type(self):
        device = SimpleNamespace(id=4, energy_type="water")

        with patch.object(DeviceService, "get_device_by_id", return_value=device):
            with patch("app.services.device_service.EnergyService.get_energy_data", return_value=["row"]) as mock_get_data:
                result = DeviceService.get_device_data(
                    session=MagicMock(),
                    device_id=4,
                    start_time=datetime(2026, 4, 3, 0, 0, 0),
                    end_time=datetime(2026, 4, 3, 23, 0, 0),
                    limit=50,
                )

        self.assertEqual(result, ["row"])
        mock_get_data.assert_called_once()
        self.assertEqual(mock_get_data.call_args.kwargs["energy_type"], "water")

    def test_get_device_statistics_delegates_energy_type(self):
        device = SimpleNamespace(id=8, energy_type="electricity")

        with patch.object(DeviceService, "get_device_by_id", return_value=device):
            with patch("app.services.device_service.EnergyService.calculate_statistics", return_value={"total_consumption": 9.9}) as mock_stats:
                result = DeviceService.get_device_statistics(
                    session=MagicMock(),
                    device_id=8,
                    start_time=datetime(2026, 4, 1, 0, 0, 0),
                    end_time=datetime(2026, 4, 2, 0, 0, 0),
                )

        self.assertEqual(result["total_consumption"], 9.9)
        self.assertEqual(mock_stats.call_args.kwargs["energy_type"], "electricity")

    def test_get_device_type_info_returns_none_when_type_unknown(self):
        with patch("app.services.device_service.device_registry.get", return_value=None):
            result = DeviceService.get_device_type_info("unknown")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
