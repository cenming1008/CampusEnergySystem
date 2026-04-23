import os
import math
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from scripts.python import send_capacitor_bank_telemetry as simulator


class TestSendCapacitorBankTelemetry(unittest.TestCase):
    def test_expand_capacity_slots_uses_capacity_code_pattern(self):
        slots = simulator._expand_capacity_slots("4:1233", 30.0, 12)

        self.assertEqual(slots[:8], [30.0, 60.0, 90.0, 90.0, 30.0, 60.0, 90.0, 90.0])
        self.assertEqual(len(slots), 12)

    def test_build_split_phase_slot_kvar_distributes_from_capacity_code(self):
        split_slots = simulator._build_split_phase_slot_kvar("7:1124", 12.0, 8)

        self.assertEqual(split_slots["phase_a_groups"], [12.0, 48.0, 24.0])
        self.assertEqual(split_slots["phase_b_groups"], [12.0, 12.0, 48.0])
        self.assertEqual(split_slots["phase_c_groups"], [24.0, 12.0])

    def test_with_control_state_uses_true_capacity_slots_for_reactive_power(self):
        payload = {
            "power": 60.0,
            "active_power_a": 20.0,
            "active_power_b": 20.0,
            "active_power_c": 20.0,
            "jkwf_status": 0,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "_load_reactive_demand_a": 60.0,
            "_load_reactive_demand_b": 30.0,
            "_load_reactive_demand_c": 30.0,
            "_split_phase_slot_kvar": {
                "phase_a_groups": [12.0, 48.0],
                "phase_b_groups": [12.0],
                "phase_c_groups": [12.0],
            },
            "_common_stage_slot_kvar": {
                "common_1_groups": [],
                "common_2_groups": [],
                "common_3_groups": [],
            },
        }
        state = simulator.ControlSimulationState(
            enabled=True,
            parameter_overrides={"phase_a_groups": 2, "phase_b_groups": 0, "phase_c_groups": 0},
        )

        updated = simulator._with_control_state(dict(payload), state)

        self.assertEqual(updated["reactive_power_a"], 0.0)
        self.assertEqual(updated["reactive_power"], 60.0)

    def test_auto_control_state_selects_best_common_stage_by_remaining_gap(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        state.parameter_overrides.update({
            "phase_a_groups": 8,
            "phase_b_groups": 8,
            "phase_c_groups": 8,
            "common_1_groups": 0,
            "common_2_groups": 0,
            "common_3_groups": 0,
        })
        payload = {
            "power_factor": 0.90,
            "reactive_power": 14.0,
            "reactive_power_a": 4.0,
            "reactive_power_b": 5.0,
            "reactive_power_c": 5.0,
            "leading_a": False,
            "leading_b": False,
            "leading_c": False,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 4,
            "switch_off_delay_seconds": 8,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "_common_stage_slot_kvar": {
                "common_1_groups": [30.0],
                "common_2_groups": [12.0],
                "common_3_groups": [6.0],
            },
            "_split_phase_slot_kvar": {
                "phase_a_groups": [12.0] * 8,
                "phase_b_groups": [12.0] * 8,
                "phase_c_groups": [12.0] * 8,
            },
        }

        simulator._apply_auto_control_step(payload, state)
        changed = simulator._apply_auto_control_step(payload, state)

        self.assertTrue(changed)
        self.assertEqual(state.parameter_overrides["common_2_groups"], 1)
        self.assertEqual(state.parameter_overrides["common_1_groups"], 0)

    def test_auto_control_state_uses_next_true_stage_kvar_for_stage_selection(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        state.parameter_overrides.update({
            "phase_a_groups": 8,
            "phase_b_groups": 8,
            "phase_c_groups": 8,
            "common_1_groups": 0,
            "common_2_groups": 1,
            "common_3_groups": 0,
        })
        payload = {
            "power_factor": 0.90,
            "reactive_power": 58.0,
            "reactive_power_a": 19.0,
            "reactive_power_b": 20.0,
            "reactive_power_c": 19.0,
            "leading_a": False,
            "leading_b": False,
            "leading_c": False,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 4,
            "switch_off_delay_seconds": 8,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "_common_stage_slot_kvar": {
                "common_1_groups": [30.0],
                "common_2_groups": [30.0, 60.0],
                "common_3_groups": [6.0],
            },
            "_split_phase_slot_kvar": {
                "phase_a_groups": [12.0] * 8,
                "phase_b_groups": [12.0] * 8,
                "phase_c_groups": [12.0] * 8,
            },
        }

        simulator._apply_auto_control_step(payload, state)
        changed = simulator._apply_auto_control_step(payload, state)

        self.assertTrue(changed)
        self.assertEqual(state.parameter_overrides["common_2_groups"], 2)
        self.assertEqual(state.parameter_overrides["common_1_groups"], 0)

    def test_auto_control_state_prefers_global_best_two_step_common_plan(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        state.parameter_overrides.update({
            "phase_a_groups": 8,
            "phase_b_groups": 8,
            "phase_c_groups": 8,
            "common_1_groups": 0,
            "common_2_groups": 0,
            "common_3_groups": 0,
        })
        payload = {
            "power_factor": 0.90,
            "reactive_power": 38.0,
            "reactive_power_a": 12.0,
            "reactive_power_b": 13.0,
            "reactive_power_c": 13.0,
            "leading_a": False,
            "leading_b": False,
            "leading_c": False,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 4,
            "switch_off_delay_seconds": 8,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "_common_stage_slot_kvar": {
                "common_1_groups": [45.0],
                "common_2_groups": [20.0],
                "common_3_groups": [18.0],
            },
            "_split_phase_slot_kvar": {
                "phase_a_groups": [12.0] * 8,
                "phase_b_groups": [12.0] * 8,
                "phase_c_groups": [12.0] * 8,
            },
        }

        simulator._apply_auto_control_step(payload, state)
        changed = simulator._apply_auto_control_step(payload, state)

        self.assertTrue(changed)
        self.assertEqual(state.parameter_overrides["common_2_groups"], 1)
        self.assertEqual(state.parameter_overrides["common_1_groups"], 0)

    def test_auto_control_state_prefers_global_best_two_step_common_cutback(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        state.parameter_overrides.update({
            "phase_a_groups": 8,
            "phase_b_groups": 8,
            "phase_c_groups": 8,
            "common_1_groups": 1,
            "common_2_groups": 1,
            "common_3_groups": 1,
        })
        payload = {
            "power_factor": 0.998,
            "reactive_power": -38.0,
            "reactive_power_a": -0.8,
            "reactive_power_b": -1.0,
            "reactive_power_c": -1.2,
            "leading_a": True,
            "leading_b": True,
            "leading_c": True,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 8,
            "switch_off_delay_seconds": 4,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "_common_stage_slot_kvar": {
                "common_1_groups": [45.0],
                "common_2_groups": [20.0],
                "common_3_groups": [18.0],
            },
            "_split_phase_slot_kvar": {
                "phase_a_groups": [12.0] * 8,
                "phase_b_groups": [12.0] * 8,
                "phase_c_groups": [12.0] * 8,
            },
        }

        simulator._apply_auto_control_step(payload, state)
        changed = simulator._apply_auto_control_step(payload, state)

        self.assertTrue(changed)
        self.assertEqual(state.parameter_overrides["common_2_groups"], 0)
        self.assertEqual(state.parameter_overrides["common_1_groups"], 1)

    def test_build_payload_derives_power_factor_from_power_and_reactive_power(self):
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

        with patch("scripts.python.send_capacitor_bank_telemetry.random.uniform", return_value=0.0):
            payload = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 0, options)

        expected_total_pf = round(
            abs(payload["power"]) / math.sqrt(payload["power"] ** 2 + payload["reactive_power"] ** 2),
            4,
        )
        expected_phase_a_pf = round(
            abs(payload["active_power_a"]) / math.sqrt(payload["active_power_a"] ** 2 + payload["reactive_power_a"] ** 2),
            4,
        )
        expected_phase_b_pf = round(
            abs(payload["active_power_b"]) / math.sqrt(payload["active_power_b"] ** 2 + payload["reactive_power_b"] ** 2),
            4,
        )
        expected_phase_c_pf = round(
            abs(payload["active_power_c"]) / math.sqrt(payload["active_power_c"] ** 2 + payload["reactive_power_c"] ** 2),
            4,
        )

        self.assertEqual(payload["power_factor"], expected_total_pf)
        self.assertEqual(payload["power_factor_a"], expected_phase_a_pf)
        self.assertEqual(payload["power_factor_b"], expected_phase_b_pf)
        self.assertEqual(payload["power_factor_c"], expected_phase_c_pf)

    def test_build_payload_uses_true_split_slot_kvar_directly(self):
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

        with patch("scripts.python.send_capacitor_bank_telemetry.random.uniform", return_value=0.0):
            base_payload = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 0, options)

        low = simulator._with_control_state(
            dict(base_payload),
            simulator.ControlSimulationState(
                enabled=True,
                parameter_overrides={
                    "phase_a_groups": 1,
                    "phase_b_groups": 0,
                    "phase_c_groups": 0,
                    "common_1_groups": 0,
                    "common_2_groups": 0,
                    "common_3_groups": 0,
                },
            ),
        )
        high = simulator._with_control_state(
            dict(base_payload),
            simulator.ControlSimulationState(
                enabled=True,
                parameter_overrides={
                    "phase_a_groups": 2,
                    "phase_b_groups": 0,
                    "phase_c_groups": 0,
                    "common_1_groups": 0,
                    "common_2_groups": 0,
                    "common_3_groups": 0,
                },
            ),
        )

        self.assertEqual(round(low["reactive_power"] - high["reactive_power"], 2), 48.0)

    def test_circuit_group_overrides_change_reactive_power(self):
        device = SimpleNamespace(
            id=16,
            sn="JKWF-TEST-01",
            name="JKWF 测试柜",
            is_active=True,
        )
        base_options = dict(
            profile="normal",
            leading=None,
            undercurrent=None,
            voltage_thd_alarm=None,
            current_thd_alarm=None,
            temp_alarm=None,
            common_2_groups=None,
            common_3_groups=None,
        )

        low_compensation = simulator.ScenarioOptions(
            **base_options,
            phase_a_groups=0,
            phase_b_groups=0,
            phase_c_groups=0,
            common_1_groups=0,
        )
        high_compensation = simulator.ScenarioOptions(
            **base_options,
            phase_a_groups=3,
            phase_b_groups=3,
            phase_c_groups=2,
            common_1_groups=4,
        )

        with patch("scripts.python.send_capacitor_bank_telemetry.random.uniform", return_value=0.0):
            low = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 0, low_compensation)
            high = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 0, high_compensation)

        self.assertGreater(low["reactive_power"], high["reactive_power"])
        self.assertLess(low["power_factor"], high["power_factor"])

    def test_additional_common_stages_also_change_reactive_power(self):
        device = SimpleNamespace(
            id=16,
            sn="JKWF-TEST-01",
            name="JKWF 测试柜",
            is_active=True,
        )
        with patch("scripts.python.send_capacitor_bank_telemetry.random.uniform", return_value=0.0):
            base_payload = simulator._build_payload(
                device,
                simulator.datetime(2026, 4, 14, 12, 0, 0),
                0,
                simulator.ScenarioOptions(
                    profile="normal",
                    leading=None,
                    undercurrent=None,
                    voltage_thd_alarm=None,
                    current_thd_alarm=None,
                    temp_alarm=None,
                    phase_a_groups=3,
                    phase_b_groups=3,
                    phase_c_groups=2,
                    common_1_groups=1,
                    common_2_groups=0,
                    common_3_groups=0,
                ),
            )
        low_state = simulator.ControlSimulationState(enabled=True)
        high_state = simulator.ControlSimulationState(
            enabled=True,
            parameter_overrides={"common_2_groups": 1, "common_3_groups": 1},
        )

        low = simulator._with_control_state(dict(base_payload), low_state)
        high = simulator._with_control_state(dict(base_payload), high_state)

        self.assertGreater(low["reactive_power"], high["reactive_power"])

    def test_auto_control_state_adds_compensation_after_on_delay(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        payload = {
            "power_factor": 0.91,
            "reactive_power": 8.0,
            "leading_a": False,
            "leading_b": False,
            "leading_c": False,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 4,
            "switch_off_delay_seconds": 8,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "split_output_circuit_count": 8,
            "common_output_circuit_count": 24,
        }

        first = simulator._apply_auto_control_step(payload, state)
        second = simulator._apply_auto_control_step(payload, state)

        self.assertFalse(first)
        self.assertTrue(second)
        self.assertEqual(state.parameter_overrides["phase_a_groups"], 1)

    def test_auto_control_state_removes_compensation_after_off_delay(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        state.parameter_overrides.update({
            "phase_a_groups": 2,
            "phase_b_groups": 2,
            "phase_c_groups": 1,
            "common_1_groups": 3,
        })
        payload = {
            "power_factor": 0.99,
            "reactive_power": -6.0,
            "leading_a": True,
            "leading_b": True,
            "leading_c": False,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 10,
            "switch_off_delay_seconds": 4,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "split_output_circuit_count": 8,
            "common_output_circuit_count": 24,
        }

        first = simulator._apply_auto_control_step(payload, state)
        second = simulator._apply_auto_control_step(payload, state)

        self.assertFalse(first)
        self.assertTrue(second)
        self.assertEqual(state.parameter_overrides["common_1_groups"], 2)

    def test_auto_control_state_does_not_act_inside_deadband(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        payload = {
            "power_factor": 0.955,
            "reactive_power": 0.2,
            "leading_a": False,
            "leading_b": False,
            "leading_c": False,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 4,
            "switch_off_delay_seconds": 4,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "split_output_circuit_count": 8,
            "common_output_circuit_count": 24,
        }

        changed = simulator._apply_auto_control_step(payload, state)

        self.assertFalse(changed)
        self.assertEqual(state.parameter_overrides, {})

    def test_auto_control_state_respects_min_action_interval(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        state.min_action_interval_seconds = 6.0
        payload = {
            "power_factor": 0.91,
            "reactive_power": 8.0,
            "leading_a": False,
            "leading_b": False,
            "leading_c": False,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 4,
            "switch_off_delay_seconds": 8,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "split_output_circuit_count": 8,
            "common_output_circuit_count": 24,
        }

        simulator._apply_auto_control_step(payload, state)
        first_action = simulator._apply_auto_control_step(payload, state)
        blocked_retry = simulator._apply_auto_control_step(payload, state)
        blocked_retry_2 = simulator._apply_auto_control_step(payload, state)
        cooldown_rearmed = simulator._apply_auto_control_step(payload, state)
        second_action = simulator._apply_auto_control_step(payload, state)

        self.assertTrue(first_action)
        self.assertFalse(blocked_retry)
        self.assertFalse(blocked_retry_2)
        self.assertFalse(cooldown_rearmed)
        self.assertTrue(second_action)
        self.assertEqual(state.parameter_overrides["phase_a_groups"], 2)

    def test_auto_control_state_prioritizes_most_undercompensated_phase(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        state.parameter_overrides.update({
            "phase_a_groups": 1,
            "phase_b_groups": 0,
            "phase_c_groups": 1,
        })
        payload = {
            "power_factor": 0.90,
            "reactive_power": 9.0,
            "reactive_power_a": 1.2,
            "reactive_power_b": 5.6,
            "reactive_power_c": 2.2,
            "leading_a": False,
            "leading_b": False,
            "leading_c": False,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 4,
            "switch_off_delay_seconds": 8,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "split_output_circuit_count": 8,
            "common_output_circuit_count": 24,
        }

        simulator._apply_auto_control_step(payload, state)
        changed = simulator._apply_auto_control_step(payload, state)

        self.assertTrue(changed)
        self.assertEqual(state.parameter_overrides["phase_b_groups"], 1)

    def test_auto_control_state_prioritizes_most_overcompensated_phase_on_cutback(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        state.parameter_overrides.update({
            "phase_a_groups": 2,
            "phase_b_groups": 2,
            "phase_c_groups": 1,
            "common_1_groups": 3,
        })
        payload = {
            "power_factor": 0.995,
            "reactive_power": -5.0,
            "reactive_power_a": -0.8,
            "reactive_power_b": -4.2,
            "reactive_power_c": -1.1,
            "leading_a": True,
            "leading_b": True,
            "leading_c": False,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 10,
            "switch_off_delay_seconds": 4,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "split_output_circuit_count": 8,
            "common_output_circuit_count": 12,
        }

        simulator._apply_auto_control_step(payload, state)
        changed = simulator._apply_auto_control_step(payload, state)

        self.assertTrue(changed)
        self.assertEqual(state.parameter_overrides["phase_b_groups"], 1)
        self.assertEqual(state.parameter_overrides["common_1_groups"], 3)

    def test_auto_control_state_uses_common_groups_after_split_groups_are_full(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        state.parameter_overrides.update({
            "phase_a_groups": 8,
            "phase_b_groups": 8,
            "phase_c_groups": 8,
            "common_1_groups": 0,
        })
        payload = {
            "power_factor": 0.88,
            "reactive_power": 12.0,
            "reactive_power_a": 3.0,
            "reactive_power_b": 4.0,
            "reactive_power_c": 5.0,
            "leading_a": False,
            "leading_b": False,
            "leading_c": False,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 4,
            "switch_off_delay_seconds": 8,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "split_output_circuit_count": 8,
            "common_output_circuit_count": 12,
        }

        simulator._apply_auto_control_step(payload, state)
        changed = simulator._apply_auto_control_step(payload, state)

        self.assertTrue(changed)
        self.assertEqual(state.parameter_overrides["common_1_groups"], 1)

    def test_auto_control_state_prefers_smaller_common_stage_for_small_remaining_gap(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        state.parameter_overrides.update({
            "phase_a_groups": 8,
            "phase_b_groups": 8,
            "phase_c_groups": 8,
            "common_1_groups": 0,
            "common_2_groups": 0,
            "common_3_groups": 0,
        })
        payload = {
            "power_factor": 0.944,
            "reactive_power": 0.7,
            "reactive_power_a": 0.2,
            "reactive_power_b": 0.2,
            "reactive_power_c": 0.3,
            "leading_a": False,
            "leading_b": False,
            "leading_c": False,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 4,
            "switch_off_delay_seconds": 8,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "split_output_circuit_count": 8,
            "common_output_circuit_count": 24,
        }

        simulator._apply_auto_control_step(payload, state)
        changed = simulator._apply_auto_control_step(payload, state)

        self.assertTrue(changed)
        self.assertEqual(state.parameter_overrides["common_3_groups"], 1)
        self.assertEqual(state.parameter_overrides["common_1_groups"], 0)

    def test_auto_control_state_prefers_common_cutback_when_phase_overcompensation_is_mild(self):
        state = simulator.ControlSimulationState(enabled=True)
        state.tick_interval_seconds = 2.0
        state.parameter_overrides.update({
            "phase_a_groups": 2,
            "phase_b_groups": 2,
            "phase_c_groups": 2,
            "common_1_groups": 2,
        })
        payload = {
            "power_factor": 0.996,
            "reactive_power": -3.0,
            "reactive_power_a": -0.8,
            "reactive_power_b": -1.0,
            "reactive_power_c": -1.2,
            "leading_a": True,
            "leading_b": True,
            "leading_c": True,
            "switch_on_power_factor": 95,
            "switch_off_power_factor": 105,
            "switch_on_delay_seconds": 10,
            "switch_off_delay_seconds": 4,
            "circuit_state_1": 0,
            "circuit_state_2": 0,
            "circuit_state_3": 0,
            "split_output_circuit_count": 8,
            "common_output_circuit_count": 12,
        }

        simulator._apply_auto_control_step(payload, state)
        changed = simulator._apply_auto_control_step(payload, state)

        self.assertTrue(changed)
        self.assertEqual(state.parameter_overrides["common_1_groups"], 1)
        self.assertEqual(state.parameter_overrides["phase_b_groups"], 2)

    def test_overtemp_profile_keeps_power_and_pf_stable_across_ticks(self):
        device = SimpleNamespace(
            id=16,
            sn="JKWF-TEST-01",
            name="JKWF 测试柜",
            is_active=True,
        )
        options = simulator.ScenarioOptions(
            profile="overtemp",
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

        with patch("scripts.python.send_capacitor_bank_telemetry.random.uniform", return_value=0.0):
            first = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 0, options)
            second = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 15, options)

        self.assertEqual(first["power"], second["power"])
        self.assertEqual(first["reactive_power"], second["reactive_power"])
        self.assertEqual(first["power_factor"], second["power_factor"])
        self.assertNotEqual(first["temperature"], second["temperature"])

    def test_overvoltage_profile_keeps_power_and_pf_stable_across_ticks(self):
        device = SimpleNamespace(
            id=16,
            sn="JKWF-TEST-01",
            name="JKWF 测试柜",
            is_active=True,
        )
        options = simulator.ScenarioOptions(
            profile="overvoltage",
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

        with patch("scripts.python.send_capacitor_bank_telemetry.random.uniform", return_value=0.0):
            first = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 0, options)
            second = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 15, options)

        self.assertEqual(first["power"], second["power"])
        self.assertEqual(first["reactive_power"], second["reactive_power"])
        self.assertEqual(first["power_factor"], second["power_factor"])
        self.assertNotEqual(first["voltage"], second["voltage"])

    def test_harmonic_profile_keeps_power_and_pf_stable_across_ticks(self):
        device = SimpleNamespace(
            id=16,
            sn="JKWF-TEST-01",
            name="JKWF 测试柜",
            is_active=True,
        )
        options = simulator.ScenarioOptions(
            profile="harmonic",
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

        with patch("scripts.python.send_capacitor_bank_telemetry.random.uniform", return_value=0.0):
            first = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 0, options)
            second = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 15, options)

        self.assertEqual(first["power"], second["power"])
        self.assertEqual(first["reactive_power"], second["reactive_power"])
        self.assertEqual(first["power_factor"], second["power_factor"])
        self.assertNotEqual(first["voltage_thd_a"], second["voltage_thd_a"])
        self.assertNotEqual(first["current_harmonic_a"], second["current_harmonic_a"])

    def test_undercurrent_profile_keeps_runtime_metrics_stable_across_ticks(self):
        device = SimpleNamespace(
            id=16,
            sn="JKWF-TEST-01",
            name="JKWF 测试柜",
            is_active=True,
        )
        options = simulator.ScenarioOptions(
            profile="undercurrent",
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

        with patch("scripts.python.send_capacitor_bank_telemetry.random.uniform", return_value=0.0):
            first = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 0, options)
            second = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 15, options)

        self.assertEqual(first["power"], second["power"])
        self.assertEqual(first["reactive_power"], second["reactive_power"])
        self.assertEqual(first["power_factor"], second["power_factor"])
        self.assertLess(first["current_a"], 20.0)
        self.assertLess(first["current_b"], 20.0)
        self.assertLess(first["current_c"], 20.0)
        self.assertTrue(first["jkwf_status"] & (1 << 3))
        self.assertTrue(first["jkwf_status"] & (1 << 4))
        self.assertTrue(first["jkwf_status"] & (1 << 5))

    def test_unbalance_profile_keeps_phase_spread_stable_across_ticks(self):
        device = SimpleNamespace(
            id=16,
            sn="JKWF-TEST-01",
            name="JKWF 测试柜",
            is_active=True,
        )
        options = simulator.ScenarioOptions(
            profile="unbalance",
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

        with patch("scripts.python.send_capacitor_bank_telemetry.random.uniform", return_value=0.0):
            first = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 0, options)
            second = simulator._build_payload(device, simulator.datetime(2026, 4, 14, 12, 0, 0), 15, options)

        self.assertEqual(first["power"], second["power"])
        self.assertEqual(first["reactive_power"], second["reactive_power"])
        self.assertEqual(first["power_factor"], second["power_factor"])
        self.assertGreater(first["current_a"], first["current_b"])
        self.assertGreater(first["current_c"], first["current_b"])
        self.assertGreater(first["active_power_a"], first["active_power_b"])
        self.assertGreater(
            max(first["reactive_power_a"], first["reactive_power_b"], first["reactive_power_c"])
            - min(first["reactive_power_a"], first["reactive_power_b"], first["reactive_power_c"]),
            3.0,
        )

    def test_build_payload_respects_configured_circuit_limits(self):
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

        phase_a = (payload["circuit_state_1"] >> 8) & 0xFF
        phase_b = payload["circuit_state_1"] & 0xFF
        phase_c = (payload["circuit_state_2"] >> 8) & 0xFF
        common_1 = payload["circuit_state_2"] & 0xFF
        common_2 = (payload["circuit_state_3"] >> 8) & 0xFF
        common_3 = payload["circuit_state_3"] & 0xFF

        split_total = sum(bin(value).count("1") for value in (phase_a, phase_b, phase_c))
        common_total = sum(bin(value).count("1") for value in (common_1, common_2, common_3))

        self.assertLessEqual(split_total, payload["split_output_circuit_count"])
        self.assertLessEqual(common_total, payload["common_output_circuit_count"])

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
        self.assertEqual(state.parameter_overrides["terminal_assignment_scheme"], "手动模式")
        self.assertEqual(state.parameter_overrides["circuit_state_phase_a"], 1)
        self.assertIn("A", message)
        self.assertIn("投入", message)

    def test_apply_control_command_switches_manual_payload_back_to_auto_profile_mode(self):
        state = simulator.ControlSimulationState(
            enabled=True,
            control_mode="manual",
            parameter_overrides={"terminal_assignment_scheme": "手动模式"},
        )

        accepted, message = simulator._apply_control_command(state, {
            "command": "manual_switch",
            "manual_mode": "auto",
            "phase": "COMMON",
            "switch_action": "none",
        })

        self.assertTrue(accepted)
        self.assertEqual(state.control_mode, "auto")
        self.assertEqual(state.parameter_overrides["terminal_assignment_scheme"], "自动模式")
        self.assertIn("自动模式", message)

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
