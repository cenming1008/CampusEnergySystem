import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.services.mqtt_models import TelemetryBroadcastData
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

    @patch("app.services.mqtt_processor.persist_device_data")
    @patch("app.services.mqtt_processor.resolve_device_id")
    def test_process_payload_dict_returns_broadcast_model(self, mock_resolve_device_id, mock_persist_device_data):
        mock_resolve_device_id.return_value = 7
        mock_persist_device_data.return_value = TelemetryBroadcastData(
            device_id=7,
            voltage=380.0,
            current=12.0,
            power=4.56,
            energy=8.9,
            timestamp="2026-01-01 08:00:00",
        )

        message = process_payload_dict({"device_id": 7, "power": 4.56}, topic="mine/telemetry")

        self.assertIsNotNone(message)
        self.assertEqual(message.type, "telemetry_update")
        self.assertEqual(message.data.device_id, 7)
        mock_resolve_device_id.assert_called_once()
        mock_persist_device_data.assert_called_once()

    @patch("app.services.mqtt_processor.process_payload_dict")
    def test_process_payload_wraps_model_as_dict(self, mock_process_payload_dict):
        mock_process_payload_dict.return_value = type(
            "FakeMessage",
            (),
            {"to_dict": lambda self: {"type": "telemetry_update", "data": {"device_id": 3}}},
        )()

        result = process_payload('{"device_id": 3}')

        self.assertEqual(result, {"type": "telemetry_update", "data": {"device_id": 3}})


if __name__ == "__main__":
    unittest.main()
