import unittest

from app.services.devices.compensation.capacitor_bank.specs import (
    CONTROL_COMMAND_MESSAGE_TYPE,
    CONTROL_PROTOCOL_VERSION,
    PARAMETER_WRITE_SPECS,
    REMOTE_COMMAND_SPECS,
)


class TestCapacitorBankControlSpecsBoundary(unittest.TestCase):
    def test_control_specs_are_available_without_loading_service(self):
        self.assertEqual(CONTROL_PROTOCOL_VERSION, "campus-control.v1")
        self.assertEqual(CONTROL_COMMAND_MESSAGE_TYPE, "control_command")
        self.assertEqual(PARAMETER_WRITE_SPECS["switch_on_power_factor"].register, "0xD2")
        self.assertEqual(PARAMETER_WRITE_SPECS["temperature_upper_limit"].value_kind, "float")
        self.assertEqual(REMOTE_COMMAND_SPECS["reset_alarm"]["command"], "reset_alarm")


if __name__ == "__main__":
    unittest.main()
