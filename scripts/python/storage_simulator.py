#!/usr/bin/env python3
"""Reusable MQTT simulator for a campus battery energy storage system."""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import signal
import sys
import threading
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import paho.mqtt.client as mqtt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.domain.storage_simulation import (  # noqa: E402
    StorageAssetConfig,
    StorageState,
    step_storage,
)

SCENARIO_NAMES = (
    "sunny_workday",
    "cloudy_workday",
    "weekend_low_load",
    "pv_surplus",
    "evening_peak",
)
FAULT_NAMES = (
    "low_soc",
    "overtemperature",
    "pcs_fault",
    "communication_loss",
    "pv_drop",
)
SIMULATION_ACTIONS = {"set_scenario", "set_speed", "inject_fault", "clear_fault"}
TERMINAL_RESULTS = {"success", "failed", "timeout", "rejected"}
MAX_SAFE_TEMPERATURE_C = 55.0


@dataclass(frozen=True)
class SimulatorConfig:
    device_code: str = "STO-001"
    scenario: str = "sunny_workday"
    speed: float = 60.0
    seed: int = 20260716
    broker: str = "127.0.0.1"
    port: int = 8883
    username: str | None = None
    password: str | None = None
    tls_enabled: bool = True
    tls_ca_path: str | None = None
    tls_insecure: bool = False
    telemetry_interval_seconds: float = 60.0
    simulation_topic_prefix: str = "campus/simulation/"
    simulation_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.device_code.strip():
            raise ValueError("device_code must not be empty")
        if self.scenario not in SCENARIO_NAMES:
            raise ValueError(f"scenario must be one of {', '.join(SCENARIO_NAMES)}")
        if not math.isfinite(self.speed) or self.speed <= 0:
            raise ValueError("speed must be a positive finite number")
        if (
            not math.isfinite(self.telemetry_interval_seconds)
            or self.telemetry_interval_seconds <= 0
        ):
            raise ValueError("telemetry_interval_seconds must be a positive finite number")

    @property
    def telemetry_topic(self) -> str:
        return f"campus/device/{self.device_code}/telemetry"

    @property
    def control_topic(self) -> str:
        return f"campus/control/{self.device_code}"

    @property
    def simulation_control_topic(self) -> str:
        return f"{self.simulation_topic_prefix.rstrip('/')}/{self.device_code}/control"


def scenario_target_power_kw(scenario: str, *, minute_of_day: int) -> float:
    """Return deterministic target power; positive charges and negative discharges."""
    if scenario not in SCENARIO_NAMES:
        raise ValueError(f"unsupported scenario: {scenario}")
    minute = int(minute_of_day) % 1440
    hour = minute / 60.0
    curves = {
        "sunny_workday": 140.0 if 10 <= hour < 15 else -180.0 if 18 <= hour < 21 else 0.0,
        "cloudy_workday": 70.0 if 11 <= hour < 14 else -120.0 if 18 <= hour < 21 else 0.0,
        "weekend_low_load": 40.0 if 11 <= hour < 15 else -60.0 if 19 <= hour < 21 else 0.0,
        "pv_surplus": 220.0 if 9 <= hour < 16 else -80.0 if 19 <= hour < 21 else 0.0,
        "evening_peak": 100.0 if 0 <= hour < 6 else -250.0 if 17 <= hour < 22 else 0.0,
    }
    return curves[scenario]


def _available_power(config: StorageAssetConfig, state: StorageState) -> tuple[float, float]:
    charge = config.power_kw if state.soc < config.soc_max else 0.0
    discharge = config.power_kw if state.soc > config.soc_min else 0.0
    return charge, discharge


def build_telemetry_payload(
    config: SimulatorConfig,
    *,
    timestamp: str | None = None,
    minute_of_day: int | None = None,
    state: StorageState | None = None,
    target_power_kw: float | None = None,
    simulation_run_id: str | None = None,
    control_mode: str = "auto",
    active_faults: set[str] | None = None,
) -> dict[str, object]:
    """Build one deterministic storage payload suitable for the ingestion topic."""
    current_state = state or StorageState(soc=50.0)
    now = datetime.now(timezone.utc)
    minute = minute_of_day if minute_of_day is not None else now.hour * 60 + now.minute
    target = (
        scenario_target_power_kw(config.scenario, minute_of_day=minute)
        if target_power_kw is None
        else float(target_power_kw)
    )
    asset = StorageAssetConfig(energy_kwh=500.0, power_kw=250.0)
    available_charge, available_discharge = _available_power(asset, current_state)
    jitter = random.Random(f"{config.seed}:{config.scenario}:{minute}")
    temperature = current_state.temperature_c + jitter.uniform(-0.15, 0.15)
    faults = active_faults or set()
    fault_codes = {name: index for index, name in enumerate(FAULT_NAMES, start=1)}
    active_fault_code = next((fault_codes[name] for name in FAULT_NAMES if name in faults), 0)

    payload: dict[str, object] = {
        "device_code": config.device_code,
        "timestamp": timestamp or now.isoformat(),
        "device_category": "storage",
        "device_subtype": "battery_energy_storage_system",
        "energy_type": "electricity",
        "data_source": "simulated",
        "scenario": config.scenario,
        "soc": round(current_state.soc, 4),
        "soh": round(current_state.soh, 4),
        "active_power": round(current_state.actual_power_kw, 4),
        "target_active_power": round(target, 4),
        "available_charge_power": round(available_charge, 4),
        "available_discharge_power": round(available_discharge, 4),
        "cell_temp_max": round(temperature + 0.8, 3),
        "cell_temp_min": round(temperature - 0.8, 3),
        "cell_temp_avg": round(temperature, 3),
        "run_state": current_state.run_state,
        "control_mode": control_mode,
        "bms_state": "fault" if faults & {"low_soc", "overtemperature"} else "normal",
        "pcs_state": (
            "fault"
            if "pcs_fault" in faults
            else "running"
            if current_state.actual_power_kw
            else "standby"
        ),
        "grid_connection_state": "connected",
        "command_source": "scenario",
        "fault_code": active_fault_code,
        "alarm_code": active_fault_code,
    }
    if simulation_run_id is not None:
        payload["simulation_run_id"] = simulation_run_id
    return payload


class StorageSimulator:
    """Own MQTT I/O and advance the pure storage model on a virtual clock."""

    def __init__(self, config: SimulatorConfig) -> None:
        self.config = config
        self.asset = StorageAssetConfig(energy_kwh=500.0, power_kw=250.0)
        self.state = StorageState(soc=50.0)
        self.scenario = config.scenario
        self.speed = config.speed
        self.control_mode = "auto"
        self.manual_target_power_kw: float | None = None
        self.virtual_minute = 0.0
        self.stop_event = threading.Event()
        self.client: mqtt.Client | None = None
        self.simulation_run_id = str(uuid.uuid4())
        self.active_faults: set[str] = set()
        self.pending_command: dict[str, Any] | None = None
        self.terminal_receipts: dict[str, dict[str, object]] = {}
        self._state_lock = threading.RLock()

    def _receipt(self, command: dict[str, Any], *, status: str, detail: str) -> dict[str, object]:
        return {
            "message_type": "control_receipt",
            "device_code": self.config.device_code,
            "command_id": command.get("command_id"),
            "status": status,
            "result": status,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_source": "simulated",
            "simulation_run_id": self.simulation_run_id,
        }

    def _publish_payload(self, payload: dict[str, object], *, force: bool = False) -> None:
        if self.client is None:
            return
        if "communication_loss" in self.active_faults and not force:
            return
        self.client.publish(
            self.config.telemetry_topic,
            json.dumps(payload, ensure_ascii=False),
            qos=1,
        )

    def _publish_receipt(
        self,
        command: dict[str, Any],
        *,
        status: str,
        detail: str,
        force: bool = False,
    ) -> dict[str, object]:
        payload = self._receipt(command, status=status, detail=detail)
        command_id = str(command.get("command_id") or "").strip()
        if status in TERMINAL_RESULTS and command_id:
            self.terminal_receipts[command_id] = payload
        self._publish_payload(payload, force=force)
        return payload

    def _republish_terminal(self, command_id: str) -> bool:
        cached = self.terminal_receipts.get(command_id)
        if cached is None:
            return False
        self._publish_payload(cached)
        return True

    def _reject(self, command: dict[str, Any], detail: str, *, force: bool = False) -> None:
        self._publish_receipt(command, status="rejected", detail=detail, force=force)

    def _handle_real_control(self, command: dict[str, Any]) -> None:
        command_id = str(command.get("command_id") or "").strip()
        if command_id and self._republish_terminal(command_id):
            return
        if command.get("action") in SIMULATION_ACTIONS or command.get("command") in SIMULATION_ACTIONS:
            self._reject(command, "simulator-only action is not allowed on the real control topic")
            return
        if not command_id:
            self._reject(command, "command_id is required")
            return
        if self.pending_command is not None:
            if self.pending_command["command_id"] == command_id:
                return
            self._reject(command, "another command is already running")
            return

        action = command.get("command")
        pending: dict[str, Any] = {
            "command_id": command_id,
            "command": action,
            "running_emitted": False,
            "tolerance_hits": 0,
        }
        if action == "set_active_power":
            try:
                target = float(command["target_active_power"])
            except (KeyError, TypeError, ValueError):
                self._reject(command, "target_active_power is required")
                return
            if not math.isfinite(target) or abs(target) > self.asset.power_kw:
                self._reject(command, "target_active_power exceeds simulator capability")
                return
            if target > 0 and self.state.soc >= self.asset.soc_max:
                self._reject(command, "charging is blocked at the SOC upper limit")
                return
            if target < 0 and self.state.soc <= self.asset.soc_min:
                self._reject(command, "discharging is blocked at the SOC lower limit")
                return
            if target != 0 and self.state.temperature_c >= MAX_SAFE_TEMPERATURE_C:
                self._reject(command, "active power is blocked by overtemperature")
                return
            if target != 0 and "pcs_fault" in self.active_faults:
                self._reject(command, "active power is blocked by PCS fault")
                return
            pending["target_active_power"] = target
            self.manual_target_power_kw = target
        elif action == "set_control_mode":
            mode = str(command.get("control_mode") or "").strip().lower()
            if mode not in {"auto", "manual"}:
                self._reject(command, "control_mode must be auto or manual")
                return
            pending["control_mode"] = mode
        elif action == "stop":
            pending["target_active_power"] = 0.0
            self.manual_target_power_kw = 0.0
        else:
            self._reject(command, "unsupported storage command")
            return

        self.pending_command = pending
        self._publish_receipt(command, status="accepted", detail="command accepted")

    def _handle_simulation_control(self, command: dict[str, Any]) -> None:
        command_id = str(command.get("command_id") or "").strip()
        if command_id and self._republish_terminal(command_id):
            return
        if not self.config.simulation_enabled:
            self._reject(command, "storage simulation control is disabled", force=True)
            return
        action = command.get("action")
        if action == "set_scenario" and command.get("scenario") in SCENARIO_NAMES:
            self.scenario = str(command["scenario"])
            self.manual_target_power_kw = None
            self._publish_receipt(command, status="success", detail="scenario updated", force=True)
            return
        if action == "set_speed":
            try:
                speed = float(command["speed"])
            except (KeyError, TypeError, ValueError):
                speed = 0.0
            if math.isfinite(speed) and speed > 0:
                self.speed = speed
                self._publish_receipt(command, status="success", detail="speed updated", force=True)
                return
        if action == "inject_fault" and command.get("fault") in FAULT_NAMES:
            fault = str(command["fault"])
            if fault == "low_soc":
                self.state = replace(self.state, soc=self.asset.soc_min, actual_power_kw=0.0)
            elif fault == "overtemperature":
                self.state = replace(self.state, temperature_c=60.0, actual_power_kw=0.0)
            self._publish_receipt(command, status="success", detail=f"fault injected: {fault}", force=True)
            self.active_faults.add(fault)
            return
        if action == "clear_fault":
            fault_value = command.get("fault")
            if fault_value is not None and fault_value not in FAULT_NAMES:
                self._reject(command, "invalid simulation fault", force=True)
                return
            faults_to_clear = {str(fault_value)} if fault_value else set(self.active_faults)
            self.active_faults.difference_update(faults_to_clear)
            if "overtemperature" in faults_to_clear:
                self.state = replace(self.state, temperature_c=25.0)
            self._publish_receipt(command, status="success", detail="fault cleared", force=True)
            return
        self._reject(command, "invalid simulation command", force=True)

    def _on_connect(self, client: mqtt.Client, _userdata: Any, _flags: Any, rc: int) -> None:
        if rc != 0:
            raise RuntimeError(f"MQTT connection failed with rc={rc}")
        client.subscribe(self.config.control_topic, qos=1)
        client.subscribe(self.config.simulation_control_topic, qos=1)

    def _on_message(self, _client: mqtt.Client, _userdata: Any, message: mqtt.MQTTMessage) -> None:
        try:
            command = json.loads(message.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        if not isinstance(command, dict):
            return
        if message.topic == self.config.control_topic:
            with self._state_lock:
                self._handle_real_control(command)
        elif message.topic == self.config.simulation_control_topic:
            with self._state_lock:
                self._handle_simulation_control(command)

    def _build_client(self) -> mqtt.Client:
        client = mqtt.Client(client_id=f"storage-simulator-{self.config.device_code}")
        if self.config.username:
            client.username_pw_set(self.config.username, self.config.password)
        if self.config.tls_enabled:
            client.tls_set(ca_certs=self.config.tls_ca_path)
            client.tls_insecure_set(self.config.tls_insecure)
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        return client

    def stop(self, *_args: object) -> None:
        self.stop_event.set()

    def _current_target_power(self, minute: int) -> float:
        if self.manual_target_power_kw is not None:
            return self.manual_target_power_kw
        if self.control_mode == "manual":
            return 0.0
        target = scenario_target_power_kw(self.scenario, minute_of_day=minute)
        if "pv_drop" in self.active_faults and target > 0:
            return 0.0
        return target

    def _advance_pending_lifecycle(self) -> None:
        pending = self.pending_command
        if pending is None:
            return
        if not pending["running_emitted"]:
            self._publish_receipt(pending, status="running", detail="command is running")
            pending["running_emitted"] = True
        if pending["command"] == "set_control_mode":
            self.control_mode = pending["control_mode"]
            self._publish_receipt(pending, status="success", detail="control mode updated")
            self.pending_command = None

    def _complete_power_command_if_stable(self) -> None:
        pending = self.pending_command
        if pending is None or pending["command"] not in {"set_active_power", "stop"}:
            return
        target = float(pending["target_active_power"])
        tolerance = max(2.5, abs(target) * 0.02)
        if abs(self.state.actual_power_kw - target) <= tolerance:
            pending["tolerance_hits"] += 1
        else:
            pending["tolerance_hits"] = 0
        if pending["tolerance_hits"] >= 3:
            self._publish_receipt(pending, status="success", detail="target power reached")
            self.pending_command = None

    def advance_one_step(self) -> dict[str, object]:
        """Advance one deterministic step and return the generated telemetry payload."""
        with self._state_lock:
            minute = int(self.virtual_minute) % 1440
            self._advance_pending_lifecycle()
            target = self._current_target_power(minute)
            if self.active_faults & {"low_soc", "overtemperature", "pcs_fault"}:
                target = 0.0
            self.state = step_storage(
                self.asset,
                self.state,
                target,
                self.config.telemetry_interval_seconds,
            )
            payload_config = replace(self.config, scenario=self.scenario, speed=self.speed)
            payload = build_telemetry_payload(
                payload_config,
                minute_of_day=minute,
                state=self.state,
                target_power_kw=target,
                simulation_run_id=self.simulation_run_id,
                control_mode=self.control_mode,
                active_faults=self.active_faults,
            )
            self._publish_payload(payload)
            self._complete_power_command_if_stable()
            self.virtual_minute += self.config.telemetry_interval_seconds / 60.0
            return payload

    def run(self) -> None:
        self.client = self._build_client()
        self.client.connect(self.config.broker, self.config.port, keepalive=60)
        self.client.loop_start()
        try:
            while not self.stop_event.is_set():
                self.advance_one_step()
                self.stop_event.wait(self.config.telemetry_interval_seconds / self.speed)
        finally:
            self.client.loop_stop()
            self.client.disconnect()


def _boolean_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Campus battery storage MQTT simulator")
    parser.add_argument("--device-code", default="STO-001")
    parser.add_argument("--scenario", choices=SCENARIO_NAMES, default="sunny_workday")
    parser.add_argument("--speed", type=float, default=60.0)
    parser.add_argument("--seed", type=int, default=20260716)
    parser.add_argument("--print-only", action="store_true")
    parser.add_argument("--broker", default=os.getenv("MQTT_BROKER", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "8883")))
    parser.add_argument(
        "--username",
        default=os.getenv("MQTT_STORAGE_USERNAME", os.getenv("MQTT_USERNAME")),
    )
    parser.add_argument(
        "--password",
        default=os.getenv("MQTT_STORAGE_PASSWORD", os.getenv("MQTT_PASSWORD")),
    )
    parser.add_argument(
        "--tls-enabled",
        action=argparse.BooleanOptionalAction,
        default=_boolean_env("MQTT_TLS_ENABLED", True),
    )
    parser.add_argument("--tls-ca-path", default=os.getenv("MQTT_TLS_CA_PATH"))
    parser.add_argument(
        "--tls-insecure",
        action=argparse.BooleanOptionalAction,
        default=_boolean_env("MQTT_TLS_INSECURE", False),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    config = SimulatorConfig(
        device_code=args.device_code,
        scenario=args.scenario,
        speed=args.speed,
        seed=args.seed,
        broker=args.broker,
        port=args.port,
        username=args.username,
        password=args.password,
        tls_enabled=args.tls_enabled,
        tls_ca_path=args.tls_ca_path,
        tls_insecure=args.tls_insecure,
        simulation_enabled=_boolean_env("STORAGE_SIMULATION_ENABLED", False),
    )
    if args.print_only:
        print(
            json.dumps(
                build_telemetry_payload(config, simulation_run_id=str(uuid.uuid4())),
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0

    simulator = StorageSimulator(config)
    signal.signal(signal.SIGINT, simulator.stop)
    signal.signal(signal.SIGTERM, simulator.stop)
    simulator.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
