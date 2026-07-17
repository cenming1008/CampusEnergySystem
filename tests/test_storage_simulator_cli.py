import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.python.storage_simulator import (
    SCENARIO_NAMES,
    SimulatorConfig,
    StorageSimulator,
    build_telemetry_payload,
    main,
    scenario_target_power_kw,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_simulator_payload_is_explicitly_simulated():
    payload = build_telemetry_payload(
        SimulatorConfig(device_code="STO-001"),
        timestamp="2026-07-16T10:00:00+08:00",
    )

    assert payload["device_code"] == "STO-001"
    assert payload["device_category"] == "storage"
    assert payload["device_subtype"] == "battery_energy_storage_system"
    assert payload["data_source"] == "simulated"
    assert payload["active_power"] == 0.0
    assert payload["timestamp"] == "2026-07-16T10:00:00+08:00"


def test_five_scenario_curves_are_deterministic_and_bounded():
    assert SCENARIO_NAMES == (
        "sunny_workday",
        "cloudy_workday",
        "weekend_low_load",
        "pv_surplus",
        "evening_peak",
    )

    first = [scenario_target_power_kw(name, minute_of_day=720) for name in SCENARIO_NAMES]
    second = [scenario_target_power_kw(name, minute_of_day=720) for name in SCENARIO_NAMES]

    assert first == second
    assert all(-250.0 <= power <= 250.0 for power in first)
    assert len(set(first)) > 1


def test_same_seed_produces_same_payload_except_timestamp():
    first = build_telemetry_payload(
        SimulatorConfig(seed=20260716, scenario="cloudy_workday"),
        timestamp="first",
        minute_of_day=615,
    )
    second = build_telemetry_payload(
        SimulatorConfig(seed=20260716, scenario="cloudy_workday"),
        timestamp="second",
        minute_of_day=615,
    )
    first.pop("timestamp")
    second.pop("timestamp")

    assert first == second


def test_print_only_outputs_one_json_payload_without_creating_mqtt_client(capsys, monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("print-only must not create an MQTT client")

    monkeypatch.setattr("paho.mqtt.client.Client", fail_if_called)

    exit_code = main(
        [
            "--device-code",
            "STO-PRINT-001",
            "--scenario",
            "sunny_workday",
            "--seed",
            "20260716",
            "--print-only",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["device_code"] == "STO-PRINT-001"
    assert payload["data_source"] == "simulated"


def test_documented_direct_script_entrypoint_runs_from_project_root():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/python/storage_simulator.py",
            "--print-only",
            "--seed",
            "20260716",
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["data_source"] == "simulated"


def test_mqtt_topics_separate_real_control_from_simulation_control():
    config = SimulatorConfig(device_code="STO-TOPIC-001")
    simulator = StorageSimulator(config)

    class FakeClient:
        def __init__(self):
            self.subscriptions = []

        def subscribe(self, topic, qos):
            self.subscriptions.append((topic, qos))

    client = FakeClient()
    simulator._on_connect(client, None, None, 0)

    assert config.telemetry_topic == "campus/device/STO-TOPIC-001/telemetry"
    assert client.subscriptions == [
        ("campus/control/STO-TOPIC-001", 1),
        ("campus/simulation/STO-TOPIC-001/control", 1),
    ]


def test_real_control_publishes_simulated_receipt_and_does_not_switch_scenario():
    simulator = StorageSimulator(SimulatorConfig(device_code="STO-CONTROL-001"))

    class FakeClient:
        def __init__(self):
            self.messages = []

        def publish(self, topic, payload, qos):
            self.messages.append((topic, json.loads(payload), qos))

    client = FakeClient()
    simulator.client = client
    simulator._on_message(
        client,
        None,
        SimpleNamespace(
            topic=simulator.config.control_topic,
            payload=json.dumps(
                {
                    "command_id": "cmd-1",
                    "action": "set_scenario",
                    "scenario": "evening_peak",
                    "target_active_power": -300,
                }
            ).encode(),
        ),
    )

    assert simulator.scenario == "sunny_workday"
    assert simulator.manual_target_power_kw == -250.0
    topic, receipt, qos = client.messages[0]
    assert topic == simulator.config.telemetry_topic
    assert receipt["command_id"] == "cmd-1"
    assert receipt["status"] == "accepted"
    assert receipt["data_source"] == "simulated"
    assert qos == 1


@pytest.mark.parametrize("speed", [0, -1])
def test_simulator_config_rejects_non_positive_speed(speed):
    with pytest.raises(ValueError, match="speed"):
        SimulatorConfig(speed=speed)
