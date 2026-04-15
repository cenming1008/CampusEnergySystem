import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from scripts.python import send_capacitor_bank_telemetry as simulator


class TestSendCapacitorBankTelemetry(unittest.TestCase):
    def test_apply_control_command_updates_start_stop_state(self):
        state = simulator.ControlSimulationState(enabled=True)

        accepted, message = simulator._apply_control_command(state, {"command": "stop"})
        self.assertTrue(accepted)
        self.assertFalse(state.enabled)
        self.assertIn("停用", message)

        accepted, message = simulator._apply_control_command(state, {"command": "start"})
        self.assertTrue(accepted)
        self.assertTrue(state.enabled)
        self.assertIn("运行中", message)

    def test_apply_control_command_updates_parameter_override(self):
        state = simulator.ControlSimulationState(enabled=True)

        accepted, message = simulator._apply_control_command(
            state,
            {
                "command": "write_parameter",
                "parameter_key": "switch_on_power_factor",
                "target_value": 98,
            },
        )

        self.assertTrue(accepted)
        self.assertEqual(state.parameter_overrides["switch_on_power_factor"], 98)
        self.assertIn("switch_on_power_factor=98", message)

    def test_apply_control_command_supports_remote_demo_actions(self):
        state = simulator.ControlSimulationState(enabled=True)

        accepted, message = simulator._apply_control_command(state, {"command": "manual_switch_test"})
        self.assertTrue(accepted)
        self.assertEqual(state.parameter_overrides["circuit_state_common_1"], 1)
        self.assertIn("手动投切测试", message)

        accepted, message = simulator._apply_control_command(state, {"command": "reset_alarm"})
        self.assertTrue(accepted)
        self.assertEqual(state.parameter_overrides["jkwf_status"], 0)
        self.assertFalse(state.parameter_overrides["temp_alarm"])
        self.assertIn("报警复位", message)

        accepted, message = simulator._apply_control_command(state, {"command": "switch_control_mode"})
        self.assertTrue(accepted)
        self.assertEqual(state.control_mode, "manual")
        self.assertEqual(state.parameter_overrides["terminal_assignment_scheme"], "手动模式")
        self.assertIn("manual", message)

    def test_apply_control_command_supports_native_manual_switch_payload(self):
        state = simulator.ControlSimulationState(enabled=True)

        accepted, message = simulator._apply_control_command(state, {
            "command": "manual_switch",
            "manual_mode": "manual",
            "phase": "A",
            "switch_action": "on",
        })

        self.assertTrue(accepted)
        self.assertEqual(state.control_mode, "manual")
        self.assertEqual(state.parameter_overrides["circuit_state_phase_a"], 1)
        self.assertIn("A", message)
        self.assertIn("投入", message)

    def test_with_control_state_zeros_runtime_metrics_when_disabled(self):
        payload = {
            "power": 18.2,
            "energy": 2.1,
            "reactive_power": -7.5,
            "voltage": 220.3,
            "current": 88.4,
            "power_factor": 0.96,
            "power_factor_a": 0.95,
            "power_factor_b": 0.96,
            "power_factor_c": 0.97,
            "frequency": 49.98,
            "switch_on_power_factor": 95,
        }
        state = simulator.ControlSimulationState(
            enabled=False,
            parameter_overrides={"switch_on_power_factor": 102},
        )

        updated = simulator._with_control_state(payload, state)

        self.assertEqual(updated["power"], 0)
        self.assertEqual(updated["reactive_power"], 0)
        self.assertEqual(updated["energy"], 0)
        self.assertEqual(updated["power_factor"], 1.0)
        self.assertEqual(updated["switch_on_power_factor"], 102)
        self.assertFalse(updated["simulated_device_enabled"])

    def test_build_payload_applies_parameter_override_after_generation(self):
        device = SimpleNamespace(
            id=16,
            sn="JKWF-TEST-01",
            name="JKWF 测试柜",
            is_active=True,
        )
        options = simulator.ScenarioOptions(
            profile="normal",
            leading=None,
            undercurrent=None,
            voltage_thd_alarm=None,
            current_thd_alarm=None,
            temp_alarm=None,
            phase_a_groups=None,
            phase_b_groups=None,
            phase_c_groups=None,
            common_1_groups=None,
            common_2_groups=None,
            common_3_groups=None,
        )
        payload = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 0, options)
        state = simulator.ControlSimulationState(
            enabled=True,
            parameter_overrides={"temperature_upper_limit": 68.5},
        )

        updated = simulator._with_control_state(payload, state)

        self.assertEqual(updated["temperature_upper_limit"], 68.5)
        self.assertTrue(updated["simulated_device_enabled"])

    @patch("scripts.python.send_capacitor_bank_telemetry._publish_payload")
    def test_publish_control_receipt_emits_structured_receipt(self, mock_publish_payload):
        mock_publish_payload.return_value = True
        runtime = simulator.RuntimeContext(
            device=SimpleNamespace(id=16, sn="JKWF-TEST-01", name="JKWF 测试柜", is_active=True),
            options=simulator.ScenarioOptions(
                profile="normal",
                leading=None,
                undercurrent=None,
                voltage_thd_alarm=None,
                current_thd_alarm=None,
                temp_alarm=None,
                phase_a_groups=None,
                phase_b_groups=None,
                phase_c_groups=None,
                common_1_groups=None,
                common_2_groups=None,
                common_3_groups=None,
            ),
            state=simulator.ControlSimulationState(enabled=True),
            telemetry_topic="campus/telemetry",
            control_topic="campus/control/16",
            publish_on_control=True,
            lock=simulator.threading.Lock(),
        )

        ok = simulator._publish_control_receipt(
            SimpleNamespace(),
            runtime,
            {"command_id": "88", "command": "reset_alarm"},
            result="success",
            detail="模拟器已执行报警复位",
        )

        self.assertTrue(ok)
        mock_publish_payload.assert_called_once()
        _, topic, payload = mock_publish_payload.call_args[0]
        self.assertEqual(topic, "campus/telemetry")
        self.assertEqual(payload["message_type"], "control_receipt")
        self.assertEqual(payload["protocol_version"], "campus-control.v1")
        self.assertEqual(payload["device_id"], 16)
        self.assertEqual(payload["command_id"], "88")
        self.assertEqual(payload["command"], "reset_alarm")
        self.assertEqual(payload["result"], "success")


if __name__ == "__main__":
    unittest.main()
