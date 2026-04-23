import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.models.tables import CapacitorBankControlProfile, DeviceControlLog
from app.services.devices.compensation.capacitor_bank.parameter_write_service import CapacitorBankParameterWriteService
from app.services.devices.compensation.capacitor_bank.service import ControlProfileWritePreconditionError


class TestCapacitorBankParameterWriteServiceBoundary(unittest.TestCase):
    def test_normalize_write_value_lives_in_parameter_write_layer(self):
        self.assertEqual(CapacitorBankParameterWriteService.normalize_write_value("switch_on_power_factor", 0.95), 95)
        self.assertEqual(CapacitorBankParameterWriteService.normalize_write_value("baud_rate", 9600), 9600)
        self.assertEqual(CapacitorBankParameterWriteService.normalize_write_value("current_polarity_identification_enabled", True), 0)

        with self.assertRaises(ValueError):
            CapacitorBankParameterWriteService.normalize_write_value("temperature_upper_limit", 120)

    def test_submit_write_requires_online_device_and_real_readback(self):
        session = MagicMock()
        device = SimpleNamespace(id=16, sn="CAP-016", is_active=True)

        with patch(
            "app.services.devices.compensation.capacitor_bank.parameter_write_service.IngestionHealthService.get_device_health",
            return_value={"is_online": False},
        ):
            with self.assertRaises(ControlProfileWritePreconditionError):
                CapacitorBankParameterWriteService.submit_control_profile_write(
                    session,
                    device,
                    parameter_key="switch_on_power_factor",
                    target_value=95,
                    operator="admin",
                )

        with patch(
            "app.services.devices.compensation.capacitor_bank.parameter_write_service.IngestionHealthService.get_device_health",
            return_value={"is_online": True},
        ):
            with patch(
                "app.services.devices.compensation.capacitor_bank.parameter_write_service.CapacitorBankControlProfileService.get_control_profile",
                return_value=None,
            ):
                with self.assertRaises(ControlProfileWritePreconditionError):
                    CapacitorBankParameterWriteService.submit_control_profile_write(
                        session,
                        device,
                        parameter_key="switch_on_power_factor",
                        target_value=95,
                        operator="admin",
                    )

    @patch("app.services.devices.compensation.capacitor_bank.parameter_write_service.publish_parameter_write_async")
    @patch("app.services.devices.compensation.capacitor_bank.parameter_write_service.IngestionHealthService.get_device_health")
    def test_submit_write_records_log_and_publishes(self, mock_health, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, sn="CAP-016", is_active=True)
        profile = CapacitorBankControlProfile(
            device_id=16,
            source="telemetry",
            snapshot_timestamp=datetime.now(),
        )
        mock_health.return_value = {"is_online": True}
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 88))

        with patch(
            "app.services.devices.compensation.capacitor_bank.parameter_write_service.CapacitorBankControlProfileService.get_control_profile",
            return_value=profile,
        ):
            result = CapacitorBankParameterWriteService.submit_control_profile_write(
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
        mock_publish.assert_called_once_with(
            16,
            "switch_on_power_factor",
            95,
            device_code="CAP-016",
            command_id="88",
            reason="联调验证",
            register="0xD2",
            protocol_version="campus-control.v1",
            message_type="control_command",
            sent_at=unittest.mock.ANY,
        )
        self.assertEqual(result["command_id"], "88")


if __name__ == "__main__":
    unittest.main()
