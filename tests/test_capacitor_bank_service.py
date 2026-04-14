import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.tables import CapacitorBankControlProfile, DeviceControlLog
from app.services.capacitor_bank_service import CapacitorBankService, ControlProfileWritePreconditionError


class TestCapacitorBankService(unittest.TestCase):
    def test_normalize_write_value_accepts_decimal_pf(self):
        result = CapacitorBankService.normalize_write_value("switch_on_power_factor", 0.95)
        self.assertEqual(result, 95)

    def test_normalize_write_value_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            CapacitorBankService.normalize_write_value("temperature_upper_limit", 120)

    @patch("app.services.capacitor_bank_service.publish_parameter_write_async")
    def test_submit_control_profile_write_records_log_and_publishes(self, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, is_active=True)
        profile = CapacitorBankControlProfile(
            device_id=16,
            source="telemetry",
            snapshot_timestamp=datetime.now(),
        )
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 88))

        with patch.object(CapacitorBankService, "get_control_profile", return_value=profile):
            result = CapacitorBankService.submit_control_profile_write(
                session,
                device,
                parameter_key="switch_on_power_factor",
                target_value=0.95,
                operator="admin",
                reason="联调验证",
            )

        added_log = session.add.call_args[0][0]
        self.assertIsInstance(added_log, DeviceControlLog)
        self.assertEqual(added_log.action, "write:switch_on_power_factor")
        self.assertEqual(added_log.command_source, "control-profile-api")
        self.assertEqual(added_log.result, "accepted")
        self.assertIn("联调验证", added_log.reason)
        mock_publish.assert_called_once_with(
            16,
            "switch_on_power_factor",
            95,
            reason="联调验证",
            register="0xD2",
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["command_id"], "88")

    def test_submit_control_profile_write_requires_real_readback(self):
        session = MagicMock()
        device = SimpleNamespace(id=16, is_active=True)

        with patch.object(CapacitorBankService, "get_control_profile", return_value=None):
            with self.assertRaises(ControlProfileWritePreconditionError):
                CapacitorBankService.submit_control_profile_write(
                    session,
                    device,
                    parameter_key="switch_on_power_factor",
                    target_value=95,
                    operator="admin",
                )

    @patch("app.services.capacitor_bank_service.publish_control_payload_async")
    def test_submit_remote_control_command_records_log_and_publishes(self, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, is_active=True)
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 66))

        result = CapacitorBankService.submit_remote_control_command(
            session,
            device,
            action="reset_alarm",
            operator="operator",
            reason="前端联调",
        )

        added_log = session.add.call_args[0][0]
        self.assertIsInstance(added_log, DeviceControlLog)
        self.assertEqual(added_log.action, "reset_alarm")
        self.assertEqual(added_log.command_source, "remote-control-api")
        self.assertEqual(added_log.result, "accepted")
        mock_publish.assert_called_once_with(
            16,
            {
                "command": "reset_alarm",
                "device_id": 16,
                "reason": "前端联调",
            },
            worker_name="mqtt-remote-reset_alarm",
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["command_id"], "66")


if __name__ == "__main__":
    unittest.main()
