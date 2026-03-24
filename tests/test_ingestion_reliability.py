import os
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.tables import EnergyType
from app.services.energy_service import (
    EnergyService,
    _collect_carbon_fields,
    _collect_energy_fields,
)
from app.services.mqtt_device_resolver import extract_device_code
from app.services.mqtt_processor import (
    apply_field_aliases,
    build_data_dict,
    normalize_metrics,
    parse_numeric,
    process_payload_dict,
    validate_payload_content,
    validate_timestamp,
)


class TestMqttProcessorReliability(unittest.TestCase):
    def test_apply_field_aliases_maps_common_protocol_fields(self):
        normalized = apply_field_aliases({
            "device_sn": "GW-001",
            "active_power": 5.6,
            "meter_reading": 12.3,
            "pf": 0.98,
        })

        self.assertEqual(normalized["device_code"], "GW-001")
        self.assertEqual(normalized["power"], 5.6)
        self.assertEqual(normalized["consumption"], 12.3)
        self.assertEqual(normalized["power_factor"], 0.98)

    def test_parse_numeric_rejects_nan(self):
        with self.assertRaises(ValueError):
            parse_numeric("nan", "power")

    def test_validate_payload_content_requires_measurements(self):
        with self.assertRaises(ValueError):
            validate_payload_content({"device_code": "A-1"})

    def test_validate_timestamp_rejects_far_future(self):
        with self.assertRaises(ValueError):
            validate_timestamp(datetime.now() + timedelta(hours=1))

    def test_build_data_dict_prefers_consumption_aliases(self):
        data = build_data_dict({"meter_reading": 9.5, "consumption": 8.0}, 380.0, 10.0, 3.8, 0.0)

        self.assertEqual(data["consumption"], 8.0)

    def test_normalize_metrics_uses_alias_values(self):
        voltage, current, power, energy = normalize_metrics({"voltage": 380, "current": 5, "power": "2.2", "energy": "10"})

        self.assertEqual((voltage, current, power, energy), (380.0, 5.0, 2.2, 10.0))

    @patch("app.services.mqtt_processor.IngestionHealthService.mark_ingestion_failure")
    @patch("app.services.mqtt_processor.IngestionHealthService.mark_message_received")
    @patch("app.services.mqtt_processor.persist_device_data")
    @patch("app.services.mqtt_processor.resolve_device_id")
    def test_process_payload_dict_skips_invalid_payload(
        self,
        mock_resolve_device_id,
        mock_persist_device_data,
        mock_mark_message_received,
        mock_mark_ingestion_failure,
    ):
        mock_resolve_device_id.return_value = 7

        result = process_payload_dict({"device_id": 7}, topic="mine/telemetry")

        self.assertIsNone(result)
        mock_persist_device_data.assert_not_called()
        mock_mark_message_received.assert_called_once()
        mock_mark_ingestion_failure.assert_called_once()


class TestMqttDeviceResolverReliability(unittest.TestCase):
    def test_extract_device_code_strips_whitespace(self):
        self.assertEqual(extract_device_code({"device_code": "  GW-001  "}, None), "GW-001")
        self.assertEqual(extract_device_code({}, "mine/device/ GW-002 /telemetry"), "GW-002")


class TestEnergyServiceReliability(unittest.TestCase):
    def test_collect_energy_fields_merges_optional_values(self):
        fields = _collect_energy_fields(EnergyType.ELECTRICITY, 12.5, 3.4, {"voltage": 380.0})

        self.assertEqual(fields["consumption"], 12.5)
        self.assertEqual(fields["flow_rate"], 3.4)
        self.assertEqual(fields["voltage"], 380.0)

    def test_collect_carbon_fields_uses_energy_type_defaults(self):
        fields = _collect_carbon_fields(EnergyType.WATER, 10.0)

        self.assertEqual(fields["consumption_unit"], "m³")
        self.assertAlmostEqual(fields["carbon_emission"], 1.67, places=2)

    def test_save_energy_data_updates_existing_record_for_same_timestamp(self):
        timestamp = datetime(2026, 3, 24, 12, 0, 0)
        existing_record = SimpleNamespace(
            device_id=1,
            timestamp=timestamp,
            energy_type=EnergyType.ELECTRICITY,
            consumption=10.0,
            flow_rate=2.0,
            voltage=220.0,
        )
        device = SimpleNamespace(id=1, energy_type=EnergyType.ELECTRICITY)
        query_result = MagicMock()
        query_result.first.return_value = existing_record
        session = MagicMock()
        session.get.return_value = device
        session.exec.return_value = query_result

        with patch.object(EnergyService, "calculate_carbon_emission") as mock_carbon:
            result = EnergyService.save_energy_data(
                session=session,
                device_id=1,
                energy_type=EnergyType.ELECTRICITY,
                consumption=12.0,
                flow_rate=3.5,
                timestamp=timestamp,
                voltage=230.0,
            )

        self.assertIs(result, existing_record)
        self.assertEqual(existing_record.consumption, 12.0)
        self.assertEqual(existing_record.flow_rate, 3.5)
        self.assertEqual(existing_record.voltage, 230.0)
        session.add.assert_not_called()
        session.commit.assert_called_once()
        mock_carbon.assert_called_once()


if __name__ == "__main__":
    unittest.main()
