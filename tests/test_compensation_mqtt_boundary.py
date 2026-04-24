import unittest
from unittest.mock import MagicMock, patch

from app.integrations.mqtt.compensation import (
    apply_compensation_field_aliases,
    extract_capacitor_bank_control_profile,
    extract_capacitor_bank_telemetry,
    normalize_compensation_measurements,
    process_control_receipt,
)


class TestCompensationMqttBoundary(unittest.TestCase):
    def test_compensation_mqtt_helpers_live_outside_generic_processor(self):
        payload = apply_compensation_field_aliases(
            {
                "q_a": -2.0,
                "q_b": -3.0,
                "q_c": -4.0,
                "switch_on_pf": 95,
                "running_circuit_count": 5,
            }
        )

        normalized = normalize_compensation_measurements(payload)
        telemetry = extract_capacitor_bank_telemetry(normalized)
        profile = extract_capacitor_bank_control_profile(normalized)

        self.assertEqual(normalized["reactive_power"], -9.0)
        self.assertEqual(telemetry["reactive_power_a"], -2.0)
        self.assertEqual(telemetry["running_circuit_count"], 5)
        self.assertEqual(profile["switch_on_power_factor"], 95)

    def test_gateway_control_receipt_aliases_refused_to_rejected(self):
        session = MagicMock()
        with patch(
            "app.services.devices.compensation.capacitor_bank.control_command_service.CapacitorBankControlCommandService.apply_control_receipt",
        ) as mock_apply:
            process_control_receipt(
                session,
                {
                    "message_type": "control_receipt",
                    "device_code": "CAP-016",
                    "command_id": "88",
                    "result": "refused",
                    "detail": "设备处于就地模式",
                },
                device_id=16,
            )

        mock_apply.assert_called_once()
        self.assertEqual(mock_apply.call_args.kwargs["device_id"], 16)
        self.assertEqual(mock_apply.call_args.kwargs["command_id"], "88")
        self.assertEqual(mock_apply.call_args.kwargs["result"], "rejected")


if __name__ == "__main__":
    unittest.main()
