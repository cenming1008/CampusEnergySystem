import json
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.domain.storage_simulation import StorageState
from scripts.python.storage_simulator import SimulatorConfig, StorageSimulator


class FakeClient:
    def __init__(self):
        self.messages: list[tuple[str, dict[str, object], int]] = []

    def publish(self, topic, payload, qos):
        self.messages.append((topic, json.loads(payload), qos))


def make_simulator(*, simulation_enabled: bool = False) -> tuple[StorageSimulator, FakeClient]:
    simulator = StorageSimulator(
        SimulatorConfig(
            device_code="STO-CONTROL-009",
            telemetry_interval_seconds=60.0,
            simulation_enabled=simulation_enabled,
        )
    )
    client = FakeClient()
    simulator.client = client
    return simulator, client


def dispatch(simulator: StorageSimulator, topic: str, payload: dict[str, object]) -> None:
    simulator._on_message(
        simulator.client,
        None,
        SimpleNamespace(topic=topic, payload=json.dumps(payload).encode()),
    )


def receipts(client: FakeClient, command_id: str) -> list[dict[str, object]]:
    return [
        payload
        for _, payload, _ in client.messages
        if payload.get("message_type") == "control_receipt"
        and payload.get("command_id") == command_id
    ]


def test_active_power_command_reaches_success_after_three_in_tolerance_steps():
    simulator, client = make_simulator()
    command = {
        "command_id": "power-1",
        "command": "set_active_power",
        "target_active_power": 100.0,
    }

    dispatch(simulator, simulator.config.control_topic, command)
    simulator.advance_one_step()
    simulator.advance_one_step()
    simulator.advance_one_step()

    command_receipts = receipts(client, "power-1")
    assert [item["result"] for item in command_receipts] == [
        "accepted",
        "running",
        "success",
    ]
    assert abs(simulator.state.actual_power_kw - 100.0) <= max(2.5, 100.0 * 0.02)


@pytest.mark.parametrize(
    ("soc", "target"),
    [(10.0, -50.0), (90.0, 50.0)],
)
def test_active_power_command_is_rejected_at_soc_boundary(soc, target):
    simulator, client = make_simulator()
    simulator.state = StorageState(soc=soc)

    dispatch(
        simulator,
        simulator.config.control_topic,
        {
            "command_id": "soc-boundary",
            "command": "set_active_power",
            "target_active_power": target,
        },
    )

    assert receipts(client, "soc-boundary")[-1]["result"] == "rejected"
    assert simulator.manual_target_power_kw is None


def test_active_power_command_is_rejected_when_battery_is_overtemperature():
    simulator, client = make_simulator()
    simulator.state = StorageState(soc=50.0, temperature_c=60.0)

    dispatch(
        simulator,
        simulator.config.control_topic,
        {
            "command_id": "hot-battery",
            "command": "set_active_power",
            "target_active_power": 50.0,
        },
    )

    assert receipts(client, "hot-battery")[-1]["result"] == "rejected"
    assert simulator.manual_target_power_kw is None


def test_manual_auto_mode_and_stop_commands_update_simulator_state():
    simulator, client = make_simulator()

    dispatch(
        simulator,
        simulator.config.control_topic,
        {"command_id": "manual-1", "command": "set_control_mode", "control_mode": "manual"},
    )
    simulator.advance_one_step()
    assert simulator.control_mode == "manual"
    assert receipts(client, "manual-1")[-1]["result"] == "success"

    simulator.state = StorageState(soc=50.0, actual_power_kw=-100.0, run_state="discharging")
    dispatch(
        simulator,
        simulator.config.control_topic,
        {"command_id": "stop-1", "command": "stop"},
    )
    for _ in range(3):
        simulator.advance_one_step()
    assert simulator.state.actual_power_kw == 0.0
    assert receipts(client, "stop-1")[-1]["result"] == "success"

    dispatch(
        simulator,
        simulator.config.control_topic,
        {"command_id": "auto-1", "command": "set_control_mode", "control_mode": "auto"},
    )
    simulator.advance_one_step()
    assert simulator.control_mode == "auto"
    assert receipts(client, "auto-1")[-1]["result"] == "success"


def test_duplicate_terminal_command_republishes_receipt_without_reapplying_action():
    simulator, client = make_simulator()
    command = {
        "command_id": "duplicate-1",
        "command": "set_active_power",
        "target_active_power": 80.0,
    }
    dispatch(simulator, simulator.config.control_topic, command)
    for _ in range(3):
        simulator.advance_one_step()
    terminal = receipts(client, "duplicate-1")[-1]
    simulator.manual_target_power_kw = 17.0

    dispatch(simulator, simulator.config.control_topic, command)

    assert receipts(client, "duplicate-1")[-1] == terminal
    assert simulator.manual_target_power_kw == 17.0


def test_simulation_controls_require_gate_and_never_run_on_real_control_topic():
    disabled, disabled_client = make_simulator()
    scenario_command = {
        "command_id": "scenario-disabled",
        "action": "set_scenario",
        "scenario": "evening_peak",
    }
    dispatch(disabled, disabled.config.simulation_control_topic, scenario_command)
    assert disabled.scenario == "sunny_workday"
    assert receipts(disabled_client, "scenario-disabled")[-1]["result"] == "rejected"

    enabled, enabled_client = make_simulator(simulation_enabled=True)
    dispatch(enabled, enabled.config.control_topic, scenario_command)
    assert enabled.scenario == "sunny_workday"
    assert receipts(enabled_client, "scenario-disabled")[-1]["result"] == "rejected"

    enabled_scenario_command = {**scenario_command, "command_id": "scenario-enabled"}
    dispatch(enabled, enabled.config.simulation_control_topic, enabled_scenario_command)
    dispatch(
        enabled,
        enabled.config.simulation_control_topic,
        {"command_id": "speed-1", "action": "set_speed", "speed": 288},
    )
    assert enabled.scenario == "evening_peak"
    assert enabled.speed == 288
    assert receipts(enabled_client, "scenario-enabled")[-1]["result"] == "success"
    assert receipts(enabled_client, "speed-1")[-1]["result"] == "success"


def test_fault_injection_is_fixed_and_communication_loss_causes_receipt_timeout():
    simulator, client = make_simulator(simulation_enabled=True)
    dispatch(
        simulator,
        simulator.config.simulation_control_topic,
        {"command_id": "bad-fault", "action": "inject_fault", "fault": "arbitrary_code"},
    )
    assert receipts(client, "bad-fault")[-1]["result"] == "rejected"

    dispatch(
        simulator,
        simulator.config.simulation_control_topic,
        {
            "command_id": "communication-loss",
            "action": "inject_fault",
            "fault": "communication_loss",
        },
    )
    messages_before_command = len(client.messages)
    dispatch(
        simulator,
        simulator.config.control_topic,
        {
            "command_id": "will-timeout",
            "command": "set_active_power",
            "target_active_power": 60.0,
        },
    )
    for _ in range(5):
        simulator.advance_one_step()

    assert len(client.messages) == messages_before_command
    assert simulator.pending_command is None
    assert simulator.terminal_receipts["will-timeout"]["result"] == "success"


def test_faults_change_safety_state_and_clear_fault_restores_operation():
    simulator, client = make_simulator(simulation_enabled=True)
    dispatch(
        simulator,
        simulator.config.simulation_control_topic,
        {"command_id": "low-soc", "action": "inject_fault", "fault": "low_soc"},
    )
    assert simulator.state.soc == simulator.asset.soc_min

    dispatch(
        simulator,
        simulator.config.simulation_control_topic,
        {"command_id": "clear-low", "action": "clear_fault", "fault": "low_soc"},
    )
    simulator.state = StorageState(soc=50.0)
    dispatch(
        simulator,
        simulator.config.control_topic,
        {
            "command_id": "after-clear",
            "command": "set_active_power",
            "target_active_power": -50.0,
        },
    )
    assert receipts(client, "after-clear")[-1]["result"] == "accepted"


def test_all_telemetry_and_receipts_share_stable_simulation_run_id():
    simulator, client = make_simulator()
    UUID(simulator.simulation_run_id)
    dispatch(
        simulator,
        simulator.config.control_topic,
        {"command_id": "run-id", "command": "stop"},
    )
    simulator.advance_one_step()

    simulated_messages = [
        payload
        for _, payload, _ in client.messages
        if payload.get("data_source") == "simulated"
    ]
    assert simulated_messages
    assert {payload["simulation_run_id"] for payload in simulated_messages} == {
        simulator.simulation_run_id
    }
