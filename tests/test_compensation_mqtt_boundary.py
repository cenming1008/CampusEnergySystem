import unittest

from app.integrations.mqtt.compensation import (
    apply_compensation_field_aliases,
    extract_capacitor_bank_control_profile,
    extract_capacitor_bank_telemetry,
    normalize_compensation_measurements,
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


if __name__ == "__main__":
    unittest.main()
