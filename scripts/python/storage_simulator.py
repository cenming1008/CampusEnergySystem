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
from dataclasses import dataclass
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

    return {
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
        "control_mode": "auto",
        "bms_state": "normal",
        "pcs_state": "running" if current_state.actual_power_kw else "standby",
        "grid_connection_state": "connected",
        "command_source": "scenario",
        "fault_code": 0,
        "alarm_code": 0,
    }


class StorageSimulator:
    """Own MQTT I/O and advance the pure storage model on a virtual clock."""

    def __init__(self, config: SimulatorConfig) -> None:
        self.config = config
        self.asset = StorageAssetConfig(energy_kwh=500.0, power_kw=250.0)
        self.state = StorageState(soc=50.0)
        self.scenario = config.scenario
        self.speed = config.speed
        self.manual_target_power_kw: float | None = None
        self.virtual_minute = 0.0
        self.stop_event = threading.Event()
        self.client: mqtt.Client | None = None

    def _receipt(self, command: dict[str, Any], *, status: str, detail: str) -> dict[str, object]:
        return {
            "message_type": "control_receipt",
            "device_code": self.config.device_code,
            "command_id": command.get("command_id"),
            "status": status,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_source": "simulated",
        }

    def _publish_receipt(self, command: dict[str, Any], *, status: str, detail: str) -> None:
        if self.client is None:
            return
        self.client.publish(
            self.config.telemetry_topic,
            json.dumps(self._receipt(command, status=status, detail=detail), ensure_ascii=False),
            qos=1,
        )

    def _handle_real_control(self, command: dict[str, Any]) -> None:
        try:
            target = float(command["target_active_power"])
        except (KeyError, TypeError, ValueError):
            self._publish_receipt(
                command, status="rejected", detail="target_active_power is required"
            )
            return
        self.manual_target_power_kw = max(-self.asset.power_kw, min(self.asset.power_kw, target))
        self._publish_receipt(command, status="accepted", detail="target power accepted")

    def _handle_simulation_control(self, command: dict[str, Any]) -> None:
        action = command.get("action")
        if action == "set_scenario" and command.get("scenario") in SCENARIO_NAMES:
            self.scenario = str(command["scenario"])
            self.manual_target_power_kw = None
            self._publish_receipt(command, status="accepted", detail="scenario updated")
            return
        if action == "set_speed":
            try:
                speed = float(command["speed"])
            except (KeyError, TypeError, ValueError):
                speed = 0.0
            if math.isfinite(speed) and speed > 0:
                self.speed = speed
                self._publish_receipt(command, status="accepted", detail="speed updated")
                return
        self._publish_receipt(command, status="rejected", detail="invalid simulation command")

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
            self._handle_real_control(command)
        elif message.topic == self.config.simulation_control_topic:
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

    def run(self) -> None:
        self.client = self._build_client()
        self.client.connect(self.config.broker, self.config.port, keepalive=60)
        self.client.loop_start()
        try:
            while not self.stop_event.is_set():
                minute = int(self.virtual_minute) % 1440
                target = self.manual_target_power_kw
                if target is None:
                    target = scenario_target_power_kw(self.scenario, minute_of_day=minute)
                self.state = step_storage(
                    self.asset,
                    self.state,
                    target,
                    self.config.telemetry_interval_seconds,
                )
                payload_config = SimulatorConfig(
                    **{**self.config.__dict__, "scenario": self.scenario, "speed": self.speed}
                )
                payload = build_telemetry_payload(
                    payload_config,
                    minute_of_day=minute,
                    state=self.state,
                    target_power_kw=target,
                )
                self.client.publish(
                    self.config.telemetry_topic,
                    json.dumps(payload, ensure_ascii=False),
                    qos=1,
                )
                self.virtual_minute += self.config.telemetry_interval_seconds / 60.0
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
    parser.add_argument("--username", default=os.getenv("MQTT_USERNAME"))
    parser.add_argument("--password", default=os.getenv("MQTT_PASSWORD"))
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
    )
    if args.print_only:
        print(json.dumps(build_telemetry_payload(config), ensure_ascii=False, sort_keys=True))
        return 0

    simulator = StorageSimulator(config)
    signal.signal(signal.SIGINT, simulator.stop)
    signal.signal(signal.SIGTERM, simulator.stop)
    simulator.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
