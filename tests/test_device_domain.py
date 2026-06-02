import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.domain import device_payloads
from app.domain.device_payloads import (
    build_device_create_fields,
    build_device_registry_default_patch,
    build_device_update_identity_patch,
    describe_device_type_semantics,
    describe_energy_data_fields,
    get_device_type_config,
    normalize_device_category,
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

    def test_normalize_device_category_maps_legacy_compensation_load(self):
        self.assertEqual(
            normalize_device_category(
                device_type="reactive_power_compensator",
                device_subtype=None,
                current_category="load",
            ),
            "compensation",
        )
        self.assertEqual(
            normalize_device_category(
                device_type="water_meter",
                device_subtype=None,
                current_category="water_meter",
            ),
            "water_meter",
        )

    def test_resolve_effective_device_type_prefers_compensation_subtype(self):
        device = SimpleNamespace(
            device_type="compensation",
            device_subtype="svg",
        )

        self.assertEqual(device_payloads.resolve_effective_device_type(device), "svg")

    def test_resolve_effective_device_type_normalizes_legacy_type_alias(self):
        device = SimpleNamespace(
            device_type="reactive_power_compensator",
            device_subtype=None,
        )

        self.assertEqual(device_payloads.resolve_effective_device_type(device), "capacitor_bank_controller")

    def test_build_device_read_normalization_patch_returns_empty_when_category_already_current(self):
        device = SimpleNamespace(
            device_type="water_meter",
            device_subtype=None,
            device_category="water_meter",
        )

        self.assertEqual(device_payloads.build_device_read_normalization_patch(device), {})

    def test_build_device_read_normalization_patch_adds_compensation_category_and_subtype(self):
        device = SimpleNamespace(
            device_type="reactive_power_compensator",
            device_subtype=None,
            device_category="load",
        )

        self.assertEqual(
            device_payloads.build_device_read_normalization_patch(device),
            {
                "device_category": "compensation",
                "device_subtype": "capacitor_bank_controller",
            },
        )

    def test_is_device_archive_complete_requires_core_profile_fields(self):
        incomplete = SimpleNamespace(
            sn="PENDING-001",
            name="待完善设备-PENDING-001",
            device_type="load",
            device_category="load",
            device_subtype=None,
            energy_type="electricity",
            location="北区",
            rated_capacity=100.0,
        )
        complete = SimpleNamespace(
            sn="LOAD-001",
            name="1号负荷",
            device_type="load",
            device_category="load",
            device_subtype=None,
            energy_type="electricity",
            location="北区",
            rated_capacity=100.0,
        )

        self.assertFalse(device_payloads.is_device_archive_complete(incomplete))
        self.assertTrue(device_payloads.is_device_archive_complete(complete))

    def test_is_device_archive_complete_requires_compensation_subtype(self):
        missing_subtype = SimpleNamespace(
            sn="CAP-001",
            name="1号补偿柜",
            device_type="compensation",
            device_category="compensation",
            device_subtype=None,
            energy_type="electricity",
            location="北区",
            rated_capacity=100.0,
        )
        with_subtype = SimpleNamespace(
            sn="CAP-002",
            name="2号补偿柜",
            device_type="compensation",
            device_category="compensation",
            device_subtype="capacitor_bank_controller",
            energy_type="electricity",
            location="北区",
            rated_capacity=100.0,
        )

        self.assertFalse(device_payloads.is_device_archive_complete(missing_subtype))
        self.assertTrue(device_payloads.is_device_archive_complete(with_subtype))

    def test_is_pending_device_archive_matches_pending_status_only(self):
        pending = SimpleNamespace(archive_status="pending")
        complete = SimpleNamespace(archive_status="complete")
        missing = SimpleNamespace()

        self.assertTrue(device_payloads.is_pending_device_archive(pending))
        self.assertFalse(device_payloads.is_pending_device_archive(complete))
        self.assertFalse(device_payloads.is_pending_device_archive(missing))

    def test_build_device_update_identity_patch_normalizes_type_and_adds_missing_unit(self):
        device = SimpleNamespace(
            device_type="load",
            device_category="load",
            unit=None,
        )

        self.assertEqual(
            build_device_update_identity_patch(
                device,
                device_type="reactive_power_compensator",
                device_subtype=None,
            ),
            {
                "device_type": "capacitor_bank_controller",
                "device_subtype": "capacitor_bank_controller",
                "device_category": "compensation",
                "energy_type": "electricity",
                "unit": "kVAR",
            },
        )

    def test_build_device_update_identity_patch_preserves_existing_unit(self):
        device = SimpleNamespace(
            device_type="water_meter",
            device_category="water_meter",
            unit="custom-unit",
        )

        self.assertEqual(
            build_device_update_identity_patch(
                device,
                device_type="water_meter",
                device_subtype=None,
            ),
            {
                "device_type": "water_meter",
                "device_subtype": None,
                "device_category": "water_meter",
                "energy_type": "water",
            },
        )

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
