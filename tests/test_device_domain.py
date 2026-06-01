import os
import unittest

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.domain.device_payloads import (
    build_device_create_fields,
    build_device_registry_default_patch,
    describe_device_type_semantics,
    describe_energy_data_fields,
    get_device_type_config,
    normalize_device_report_payload,
)


class TestDeviceDomainHelpers(unittest.TestCase):
    def test_get_device_type_config_raises_for_unknown_type(self):
        with self.assertRaises(ValueError):
            get_device_type_config("unknown_type")

    def test_build_device_create_fields_uses_registry_defaults(self):
        fields = build_device_create_fields(
            name="1号水表",
            sn="W001",
            device_type="water_meter",
        )

        self.assertEqual(fields["energy_type"], "water")
        self.assertEqual(fields["unit"], "m³/h")
        self.assertTrue(fields["is_active"])

    def test_build_device_registry_default_patch_normalizes_legacy_compensation_device(self):
        patch = build_device_registry_default_patch(
            device_type="svg",
            device_subtype=None,
            device_category="load",
            energy_type=None,
            unit=None,
            rated_capacity=None,
        )

        self.assertEqual(patch["device_category"], "compensation")
        self.assertEqual(patch["device_subtype"], "svg")
        self.assertEqual(patch["energy_type"], "electricity")
        self.assertEqual(patch["unit"], "kVAR")
        self.assertGreater(patch["rated_capacity"], 0)

    def test_describe_device_type_semantics_exposes_meter_role(self):
        semantics = describe_device_type_semantics("water_meter")

        self.assertEqual(semantics["object_role"], "meter")
        self.assertEqual(semantics["metering_role"], "dedicated_meter")
        self.assertEqual(semantics["consumption_unit"], "m³")

    def test_describe_energy_data_fields_marks_public_and_specialized_fields(self):
        fields = describe_energy_data_fields("heat_meter")

        self.assertEqual(fields["public_fields"], ["consumption", "flow_rate"])
        self.assertIn("heat_flow", fields["specialized_fields"])

    def test_normalize_device_report_payload_maps_power_to_flow_rate(self):
        payload = normalize_device_report_payload(
            "load",
            {"consumption": 10.5, "power": 3.2, "voltage": 220},
        )

        self.assertEqual(payload.consumption, 10.5)
        self.assertEqual(payload.flow_rate, 3.2)
        self.assertEqual(payload.optional_fields["voltage"], 220)

    def test_normalize_device_report_payload_maps_heat_flow_to_common_flow_rate(self):
        payload = normalize_device_report_payload(
            "heat_meter",
            {"consumption": 5.0, "heat_flow": 1.2, "supply_temp": 60},
        )

        self.assertEqual(payload.flow_rate, 1.2)
        self.assertEqual(payload.optional_fields["heat_flow"], 1.2)

    def test_normalize_device_report_payload_keeps_reactive_power(self):
        payload = normalize_device_report_payload(
            "capacitor_bank_controller",
            {
                "consumption": 5.0,
                "flow_rate": 1.2,
                "reactive_power": -24.0,
                "power_factor": 0.98,
                "voltage": 220.0,
                "current": 8.0,
            },
        )

        self.assertEqual(payload.optional_fields["reactive_power"], -24.0)

    def test_normalize_device_report_payload_requires_required_fields(self):
        with self.assertRaises(ValueError):
            normalize_device_report_payload("water_meter", {"consumption": 5.0})


if __name__ == "__main__":
    unittest.main()
