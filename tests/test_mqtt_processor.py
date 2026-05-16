import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.services.mqtt_processor import (
    build_data_dict,
    normalize_metrics,
    parse_payload,
    parse_timestamp,
    process_payload,
    process_payload_dict,
)


class TestMqttProcessor(unittest.TestCase):
    def test_parse_payload_returns_dict(self):
        payload = '{"device_id": 1, "power": 12.5}'
        self.assertEqual(parse_payload(payload), {"device_id": 1, "power": 12.5})

    def test_parse_payload_rejects_invalid_json(self):
        self.assertIsNone(parse_payload("not-json"))

    def test_normalize_metrics_falls_back_to_voltage_current(self):
        voltage, current, power, energy = normalize_metrics(
            {"voltage": 400, "current": 10, "energy": 5}
        )
        self.assertEqual((voltage, current, power, energy), (400.0, 10.0, 4.0, 5.0))

    def test_parse_timestamp_supports_iso_string(self):
        parsed = parse_timestamp({"timestamp": "2026-03-24T11:00:00"})
        self.assertEqual(parsed.isoformat(), "2026-03-24T11:00:00")

    def test_build_data_dict_keeps_zero_values_and_filters_none(self):
        data_dict = build_data_dict(
            {
                "consumption": 0.0,
                "power_factor": None,
                "temperature": 0,
                "flow_rate": None,
            },
            voltage=380.0,
            current=0.0,
            power=0.0,
            energy=0.0,
        )
        self.assertEqual(data_dict["power"], 0.0)
        self.assertEqual(data_dict["current"], 0.0)
        self.assertEqual(data_dict["temperature"], 0)
        self.assertNotIn("power_factor", data_dict)
        self.assertNotIn("flow_rate", data_dict)

    @patch("app.integrations.mqtt.processor.process_payload_dict")
    def test_legacy_process_payload_dict_delegates_to_canonical_processor(self, mock_canonical):
        mock_canonical.return_value = MagicMock(device_id=7)

        message = process_payload_dict({"device_id": 7, "power": 4.56}, topic="campus/telemetry")

        self.assertIsNotNone(message)
        self.assertEqual(message.device_id, 7)
        mock_canonical.assert_called_once_with({"device_id": 7, "power": 4.56}, topic="campus/telemetry")

    @patch("app.integrations.mqtt.processor.process_payload_dict")
    def test_legacy_process_payload_dict_preserves_none_result(self, mock_canonical):
        mock_canonical.return_value = None

        message = process_payload_dict(
            {
                "message_type": "control_receipt",
                "device_id": 16,
                "command_id": "88",
                "command": "write_parameter",
                "result": "success",
                "detail": "网关已写入参数",
            },
            topic="campus/telemetry",
        )

        self.assertIsNone(message)
        mock_canonical.assert_called_once()

    @patch("app.integrations.mqtt.processor.process_payload")
    def test_legacy_process_payload_delegates_to_canonical_processor(self, mock_canonical):
        mock_canonical.return_value = {"type": "telemetry_update", "data": {"device_id": 3}}

        result = process_payload('{"device_id": 3}')

        self.assertEqual(result, {"type": "telemetry_update", "data": {"device_id": 3}})
        mock_canonical.assert_called_once_with('{"device_id": 3}', topic=None)


if __name__ == "__main__":
    unittest.main()
