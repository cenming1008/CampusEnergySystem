import unittest

from app.domain.device_payloads import describe_energy_data_fields
from app.services.device_service import DeviceService


class TestCompensationDeviceContract(unittest.TestCase):
    def test_svg_type_info_uses_public_and_extension_split(self):
        result = DeviceService.get_device_type_info("svg")

        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "compensation")
        self.assertEqual(result["subtype_name_zh"], "SVG")
        self.assertEqual(
            result["public_data_fields"],
            ["timestamp", "voltage", "current", "power_factor", "reactive_power", "flow_rate", "temperature"],
        )
        self.assertIn("svg_reactive_output", result["specialized_fields"])
        self.assertNotIn("reactive_power", result["specialized_fields"])
        self.assertEqual(
            result["energy_data_fields"]["supported_subtypes"],
            ["capacitor_bank_controller", "svg"],
        )

    def test_capacitor_bank_energy_data_fields_expose_contract(self):
        fields = describe_energy_data_fields("capacitor_bank_controller")

        self.assertEqual(
            fields["public_fields"],
            ["timestamp", "voltage", "current", "power_factor", "reactive_power", "flow_rate", "temperature"],
        )
        self.assertIn("active_power_a", fields["specialized_fields"])
        self.assertIn("circuit_state_common_3", fields["specialized_fields"])
        self.assertNotIn("reactive_power", fields["specialized_fields"])
        self.assertEqual(fields["planned_subtypes"], ["apf", "hybrid_compensation"])


if __name__ == "__main__":
    unittest.main()
