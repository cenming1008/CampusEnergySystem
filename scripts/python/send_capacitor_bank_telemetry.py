#!/usr/bin/env python3
"""
向指定电容补偿控制器发送模拟 MQTT 遥测数据。

发送内容同时覆盖：
  - 公共层字段：voltage/current/power/reactive_power/power_factor/temperature
  - 控制器专属字段：三相功率、电压 THD、谐波电流、状态位、投切状态
  - 控制台参数字段：投入/切除 PF、延时、保护门限、通讯速率、容量编码

联调边界：
  - 可直接驱动：实时指标、三相快照、投切状态、状态位标签、历史趋势
  - 不直接驱动：启停记录、人工控制日志、完整事件时间线、运维档案

用法：
  # 查看当前系统中的电容补偿控制器列表
  python scripts/python/send_capacitor_bank_telemetry.py --list

  # 正常实时联调：向 device_id=1 的设备持续发送 30 条
  python scripts/python/send_capacitor_bank_telemetry.py --id 1 --profile normal --loop 30 --interval 5

  # 24 小时历史补数：每 5 分钟一条
  python scripts/python/send_capacitor_bank_telemetry.py --id 1 --profile normal --backfill 288 --backfill-step 300

  # 谐波告警联调：点亮 THD / 谐波电流告警标签
  python scripts/python/send_capacitor_bank_telemetry.py --id 1 --profile harmonic --loop 10 --interval 3

  # 过温 + 投切状态联调：触发温度告警并固定投入组数
  python scripts/python/send_capacitor_bank_telemetry.py --id 1 --profile overtemp --phase-a-groups 6 --phase-b-groups 5 --phase-c-groups 7 --common-1-groups 4
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("请先安装: pip install paho-mqtt")
    raise SystemExit(1)

from sqlmodel import Session, select

from app.core.database import engine
from app.core.settings import settings
from app.domain.device_payloads import resolve_compensation_subtype
from app.models.tables import Device

BROKER = os.getenv("MQTT_BROKER", settings.mqtt_broker)
PORT = int(os.getenv("MQTT_PORT", str(settings.mqtt_port)))
USERNAME = os.getenv("MQTT_USERNAME", settings.mqtt_username or "campus_mqtt")
PASSWORD = os.getenv("MQTT_PASSWORD", settings.mqtt_password or "campus_mqtt_secret_2026")
TOPIC = os.getenv("MQTT_TOPIC", settings.mqtt_topic)
BROKER_CONTAINER_CANDIDATES = (
    "campusenergysystem-mqtt-1",
    "campus_mqtt",
    "campus_mqtt_dev",
    "campus_mqtt_prod",
)
PROFILE_CHOICES = ("normal", "overvoltage", "harmonic", "overtemp", "undercurrent", "unbalance", "custom")
PHASE_FLAG_CHOICES = ("a", "b", "c", "all", "none")


@dataclass(frozen=True)
class ScenarioOptions:
    profile: str
    leading: str | None
    undercurrent: str | None
    voltage_thd_alarm: str | None
    current_thd_alarm: str | None
    temp_alarm: str | None
    phase_a_groups: int | None
    phase_b_groups: int | None
    phase_c_groups: int | None
    common_1_groups: int | None
    common_2_groups: int | None
    common_3_groups: int | None


@dataclass
class ControlSimulationState:
    enabled: bool = True
    parameter_overrides: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.parameter_overrides is None:
            self.parameter_overrides = {}


@dataclass
class RuntimeContext:
    device: Device
    options: ScenarioOptions
    state: ControlSimulationState
    telemetry_topic: str
    control_topic: str
    publish_on_control: bool
    lock: threading.Lock
    tick: int = 0


def _wave(base: float, amplitude: float, t: float, period: float = 60.0) -> float:
    return base + amplitude * math.sin(2 * math.pi * t / period) + random.uniform(-amplitude * 0.1, amplitude * 0.1)


def _build_mask(enabled: int, total: int = 8) -> int:
    enabled = max(0, min(total, enabled))
    return sum(1 << i for i in range(enabled))


def _clamp_group(value: int | None) -> int | None:
    if value is None:
        return None
    return max(0, min(8, value))


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _apply_profile(base: dict[str, float], profile: str) -> None:
    if profile == "overvoltage":
        base.update({
            "voltage_a_base": 234.6,
            "voltage_b_base": 233.8,
            "voltage_c_base": 235.1,
            "voltage_amp": 1.1,
        })
    elif profile == "harmonic":
        base.update({
            "voltage_thd_a_base": 4.6,
            "voltage_thd_b_base": 4.8,
            "voltage_thd_c_base": 4.7,
            "current_harmonic_a_base": 2.9,
            "current_harmonic_b_base": 2.8,
            "current_harmonic_c_base": 3.0,
        })
    elif profile == "overtemp":
        base.update({
            "temperature_base": 54.5,
            "temperature_amp": 2.2,
            "current_a_base": 96.0,
            "current_b_base": 93.0,
            "current_c_base": 98.0,
        })
    elif profile == "undercurrent":
        base.update({
            "current_a_base": 10.0,
            "current_b_base": 8.5,
            "current_c_base": 9.2,
            "current_amp": 2.0,
            "active_power_a_base": 4.0,
            "active_power_b_base": 3.6,
            "active_power_c_base": 3.8,
            "active_power_amp": 1.0,
            "reactive_power_a_base": -1.8,
            "reactive_power_b_base": -1.4,
            "reactive_power_c_base": -1.6,
            "reactive_power_amp": 0.6,
        })
    elif profile == "unbalance":
        base.update({
            "voltage_a_base": 223.0,
            "voltage_b_base": 216.5,
            "voltage_c_base": 229.0,
            "current_a_base": 112.0,
            "current_b_base": 74.0,
            "current_c_base": 96.0,
            "active_power_a_base": 25.0,
            "active_power_b_base": 12.5,
            "active_power_c_base": 20.0,
            "reactive_power_a_base": -12.0,
            "reactive_power_b_base": -4.5,
            "reactive_power_c_base": -8.5,
        })


def _phase_override(selection: str | None, defaults: dict[str, bool], keys: tuple[str, str, str]) -> dict[str, bool]:
    if selection is None:
        return defaults
    if selection == "none":
        return {keys[0]: False, keys[1]: False, keys[2]: False}
    if selection == "all":
        return {keys[0]: True, keys[1]: True, keys[2]: True}
    return {
        keys[0]: selection == "a",
        keys[1]: selection == "b",
        keys[2]: selection == "c",
    }


def _build_payload(device: Device, timestamp: datetime, tick: int, options: ScenarioOptions) -> dict[str, Any]:
    t = float(tick)
    base = {
        "voltage_a_base": 220.0,
        "voltage_b_base": 219.4,
        "voltage_c_base": 220.6,
        "voltage_amp": 2.6,
        "current_a_base": 92.0,
        "current_b_base": 88.0,
        "current_c_base": 95.0,
        "current_amp": 16.0,
        "power_factor_a_base": 0.972,
        "power_factor_b_base": 0.968,
        "power_factor_c_base": 0.975,
        "power_factor_amp": 0.02,
        "active_power_a_base": 20.0,
        "active_power_b_base": 19.0,
        "active_power_c_base": 21.0,
        "active_power_amp": 4.0,
        "reactive_power_a_base": -8.0,
        "reactive_power_b_base": -7.0,
        "reactive_power_c_base": -9.0,
        "reactive_power_amp": 2.4,
        "voltage_thd_a_base": 2.8,
        "voltage_thd_b_base": 3.0,
        "voltage_thd_c_base": 2.7,
        "voltage_thd_amp": 0.5,
        "current_harmonic_a_base": 1.4,
        "current_harmonic_b_base": 1.3,
        "current_harmonic_c_base": 1.5,
        "current_harmonic_amp": 0.35,
        "temperature_base": 37.0,
        "temperature_amp": 5.0,
        "frequency_base": 50.0,
        "frequency_amp": 0.03,
    }
    _apply_profile(base, options.profile)

    voltage_a = _wave(base["voltage_a_base"], min(base["voltage_amp"], 3.2), t, 120)
    voltage_b = _wave(base["voltage_b_base"], min(base["voltage_amp"], 3.2), t + 30, 120)
    voltage_c = _wave(base["voltage_c_base"], min(base["voltage_amp"], 3.2), t + 60, 120)

    current_a = max(0.1, _wave(base["current_a_base"], base["current_amp"], t, 90))
    current_b = max(0.1, _wave(base["current_b_base"], base["current_amp"] * 0.94, t + 25, 90))
    current_c = max(0.1, _wave(base["current_c_base"], base["current_amp"] * 0.88, t + 50, 90))

    power_factor_a = min(0.999, max(0.75, _wave(base["power_factor_a_base"], base["power_factor_amp"], t, 90)))
    power_factor_b = min(0.999, max(0.75, _wave(base["power_factor_b_base"], base["power_factor_amp"], t + 15, 90)))
    power_factor_c = min(0.999, max(0.75, _wave(base["power_factor_c_base"], base["power_factor_amp"], t + 30, 90)))

    active_power_a = max(0.5, _wave(base["active_power_a_base"], base["active_power_amp"], t, 90))
    active_power_b = max(0.5, _wave(base["active_power_b_base"], base["active_power_amp"], t + 20, 90))
    active_power_c = max(0.5, _wave(base["active_power_c_base"], base["active_power_amp"], t + 40, 90))

    reactive_power_a = min(-0.2, _wave(base["reactive_power_a_base"], base["reactive_power_amp"], t, 90))
    reactive_power_b = min(-0.2, _wave(base["reactive_power_b_base"], base["reactive_power_amp"] * 0.9, t + 20, 90))
    reactive_power_c = min(-0.2, _wave(base["reactive_power_c_base"], base["reactive_power_amp"], t + 40, 90))

    apparent_power_a = math.sqrt(active_power_a ** 2 + reactive_power_a ** 2)
    apparent_power_b = math.sqrt(active_power_b ** 2 + reactive_power_b ** 2)
    apparent_power_c = math.sqrt(active_power_c ** 2 + reactive_power_c ** 2)

    voltage_thd_a = max(0.1, _wave(base["voltage_thd_a_base"], base["voltage_thd_amp"], t, 180))
    voltage_thd_b = max(0.1, _wave(base["voltage_thd_b_base"], base["voltage_thd_amp"] * 0.8, t + 20, 180))
    voltage_thd_c = max(0.1, _wave(base["voltage_thd_c_base"], base["voltage_thd_amp"], t + 40, 180))
    current_harmonic_a = max(0.1, _wave(base["current_harmonic_a_base"], base["current_harmonic_amp"], t, 180))
    current_harmonic_b = max(0.1, _wave(base["current_harmonic_b_base"], base["current_harmonic_amp"] * 0.86, t + 15, 180))
    current_harmonic_c = max(0.1, _wave(base["current_harmonic_c_base"], base["current_harmonic_amp"], t + 30, 180))
    temperature = _wave(base["temperature_base"], base["temperature_amp"], t, 180)
    frequency = _wave(base["frequency_base"], base["frequency_amp"], t, 300)

    power = active_power_a + active_power_b + active_power_c
    reactive_power = reactive_power_a + reactive_power_b + reactive_power_c
    power_factor = (power_factor_a + power_factor_b + power_factor_c) / 3
    voltage = (voltage_a + voltage_b + voltage_c) / 3
    current = (current_a + current_b + current_c) / 3
    energy = round(max(0.0, power) * max(1, tick + 1) / 3600, 4)

    phase_a_groups = round(min(8, max(0, abs(reactive_power_a) / 1.25)))
    phase_b_groups = round(min(8, max(0, abs(reactive_power_b) / 1.25)))
    phase_c_groups = round(min(8, max(0, abs(reactive_power_c) / 1.25)))
    common_1_groups = round(min(8, max(0, (abs(reactive_power) - 18) / 1.5)))
    common_2_groups = 1 if max(voltage_thd_a, voltage_thd_b, voltage_thd_c) > 3.4 else 0
    common_3_groups = 1 if temperature > 42.0 else 0

    if options.profile == "harmonic":
        common_2_groups = max(common_2_groups, 1)
    if options.profile == "overtemp":
        common_3_groups = max(common_3_groups, 1)
    if options.profile == "unbalance":
        phase_a_groups = max(phase_a_groups, 7)
        phase_b_groups = min(phase_b_groups, 3)
        phase_c_groups = max(phase_c_groups, 5)

    phase_a_groups = _clamp_group(options.phase_a_groups) if options.phase_a_groups is not None else phase_a_groups
    phase_b_groups = _clamp_group(options.phase_b_groups) if options.phase_b_groups is not None else phase_b_groups
    phase_c_groups = _clamp_group(options.phase_c_groups) if options.phase_c_groups is not None else phase_c_groups
    common_1_groups = _clamp_group(options.common_1_groups) if options.common_1_groups is not None else common_1_groups
    common_2_groups = _clamp_group(options.common_2_groups) if options.common_2_groups is not None else common_2_groups
    common_3_groups = _clamp_group(options.common_3_groups) if options.common_3_groups is not None else common_3_groups

    circuit_state_1 = (_build_mask(phase_a_groups) << 8) | _build_mask(phase_b_groups)
    circuit_state_2 = (_build_mask(phase_c_groups) << 8) | _build_mask(common_1_groups)
    circuit_state_3 = (_build_mask(common_2_groups) << 8) | _build_mask(common_3_groups)

    flag_defaults = {
        "leading_a": reactive_power_a < 0,
        "leading_b": reactive_power_b < 0,
        "leading_c": reactive_power_c < 0,
        "undercurrent_a": current_a < 20.0,
        "undercurrent_b": current_b < 20.0,
        "undercurrent_c": current_c < 20.0,
        "overvoltage_alarm_a": voltage_a > 231.0,
        "overvoltage_alarm_b": voltage_b > 231.0,
        "overvoltage_alarm_c": voltage_c > 231.0,
        "voltage_thd_alarm_a": voltage_thd_a > 4.2,
        "voltage_thd_alarm_b": voltage_thd_b > 4.2,
        "voltage_thd_alarm_c": voltage_thd_c > 4.2,
        "current_thd_alarm_a": current_harmonic_a > 2.6,
        "current_thd_alarm_b": current_harmonic_b > 2.6,
        "current_thd_alarm_c": current_harmonic_c > 2.6,
        "temp_alarm": temperature > 52.0,
    }

    flag_defaults.update(_phase_override(options.leading, flag_defaults, ("leading_a", "leading_b", "leading_c")))
    flag_defaults.update(_phase_override(options.undercurrent, flag_defaults, ("undercurrent_a", "undercurrent_b", "undercurrent_c")))
    flag_defaults.update(_phase_override(
        options.voltage_thd_alarm,
        flag_defaults,
        ("voltage_thd_alarm_a", "voltage_thd_alarm_b", "voltage_thd_alarm_c"),
    ))
    flag_defaults.update(_phase_override(
        options.current_thd_alarm,
        flag_defaults,
        ("current_thd_alarm_a", "current_thd_alarm_b", "current_thd_alarm_c"),
    ))
    if options.temp_alarm == "on":
        flag_defaults["temp_alarm"] = True
    elif options.temp_alarm == "off":
        flag_defaults["temp_alarm"] = False

    jkwf_status = 0
    status_bits = {
        "leading_a": 0,
        "leading_b": 1,
        "leading_c": 2,
        "undercurrent_a": 3,
        "undercurrent_b": 4,
        "undercurrent_c": 5,
        "overvoltage_alarm_a": 6,
        "overvoltage_alarm_b": 7,
        "overvoltage_alarm_c": 8,
        "voltage_thd_alarm_a": 9,
        "voltage_thd_alarm_b": 10,
        "voltage_thd_alarm_c": 11,
        "current_thd_alarm_a": 12,
        "current_thd_alarm_b": 13,
        "current_thd_alarm_c": 14,
        "temp_alarm": 15,
    }
    for name, bit in status_bits.items():
        if flag_defaults[name]:
            jkwf_status |= 1 << bit

    payload = {
        "device_code": device.sn,
        "device_name": device.name,
        "device_type": "capacitor_bank_controller",
        "timestamp": timestamp.isoformat(),
        "voltage": round(voltage, 2),
        "current": round(current, 2),
        "power": round(power, 2),
        "energy": energy,
        "reactive_power": round(reactive_power, 2),
        "power_factor": round(power_factor, 4),
        "temperature": round(temperature, 1),
        "voltage_a": round(voltage_a, 2),
        "voltage_b": round(voltage_b, 2),
        "voltage_c": round(voltage_c, 2),
        "current_a": round(current_a, 2),
        "current_b": round(current_b, 2),
        "current_c": round(current_c, 2),
        "power_factor_a": round(power_factor_a, 4),
        "power_factor_b": round(power_factor_b, 4),
        "power_factor_c": round(power_factor_c, 4),
        "active_power_a": round(active_power_a, 2),
        "active_power_b": round(active_power_b, 2),
        "active_power_c": round(active_power_c, 2),
        "reactive_power_a": round(reactive_power_a, 2),
        "reactive_power_b": round(reactive_power_b, 2),
        "reactive_power_c": round(reactive_power_c, 2),
        "apparent_power_a": round(apparent_power_a, 2),
        "apparent_power_b": round(apparent_power_b, 2),
        "apparent_power_c": round(apparent_power_c, 2),
        "voltage_thd_a": round(voltage_thd_a, 2),
        "voltage_thd_b": round(voltage_thd_b, 2),
        "voltage_thd_c": round(voltage_thd_c, 2),
        "current_harmonic_a": round(current_harmonic_a, 2),
        "current_harmonic_b": round(current_harmonic_b, 2),
        "current_harmonic_c": round(current_harmonic_c, 2),
        "frequency": round(frequency, 3),
        "jkwf_status": jkwf_status,
        "circuit_state_1": circuit_state_1,
        "circuit_state_2": circuit_state_2,
        "circuit_state_3": circuit_state_3,
        "switch_on_power_factor": 95,
        "switch_off_power_factor": 105,
        "switch_on_delay_seconds": 10,
        "switch_off_delay_seconds": 8,
        "common_output_circuit_count": 12,
        "split_output_circuit_count": 8,
        "common_capacity_code": "4:1233",
        "split_capacity_code": "7:1124",
        "common_step_capacity_kvar": 30.0,
        "split_step_capacity_kvar": 12.0,
        "ct_primary_current": 300,
        "overvoltage_threshold": 245.0,
        "voltage_harmonic_threshold": 4.5,
        "current_harmonic_threshold": 2.8,
        "temperature_upper_limit": 55.0,
        "alarm_drive_event": "过压切除",
        "baud_rate": 9600,
        "terminal_assignment_scheme": "方案1",
        "current_polarity_identification_enabled": True,
    }
    return payload


def _with_control_state(payload: dict[str, Any], state: ControlSimulationState) -> dict[str, Any]:
    if not state.enabled:
        zero_fields = (
            "voltage",
            "current",
            "power",
            "energy",
            "reactive_power",
            "temperature",
            "voltage_a",
            "voltage_b",
            "voltage_c",
            "current_a",
            "current_b",
            "current_c",
            "active_power_a",
            "active_power_b",
            "active_power_c",
            "reactive_power_a",
            "reactive_power_b",
            "reactive_power_c",
            "apparent_power_a",
            "apparent_power_b",
            "apparent_power_c",
            "current_harmonic_a",
            "current_harmonic_b",
            "current_harmonic_c",
        )
        for key in zero_fields:
            payload[key] = 0
        payload["power_factor"] = 1.0
        payload["power_factor_a"] = 1.0
        payload["power_factor_b"] = 1.0
        payload["power_factor_c"] = 1.0
        payload["frequency"] = 50.0
        payload["jkwf_status"] = 0
        payload["circuit_state_1"] = 0
        payload["circuit_state_2"] = 0
        payload["circuit_state_3"] = 0
        payload["simulated_device_enabled"] = False
    else:
        payload["simulated_device_enabled"] = True

    payload.update(state.parameter_overrides)
    return payload


def _publish_payload(client: mqtt.Client, topic: str, payload: dict[str, Any]) -> bool:
    if _publish_via_docker(topic, payload):
        return True
    try:
        result = client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1)
        result.wait_for_publish(timeout=5)
        ok = result.is_published()
        if not ok:
            print("❌ MQTT 消息未在超时时间内完成发布")
        return ok
    except Exception as exc:
        print(f"❌ MQTT 发送失败: {exc}")
        return False


def _create_client(runtime: RuntimeContext | None = None) -> mqtt.Client:
    client = mqtt.Client()
    if USERNAME and PASSWORD:
        client.username_pw_set(USERNAME, PASSWORD)
    if runtime is not None:
        client.user_data_set(runtime)
        client.on_connect = _on_connect
        client.on_message = _on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    return client


def _find_local_broker_container() -> str | None:
    if BROKER not in {"localhost", "127.0.0.1"}:
        return None
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return None
    for name in BROKER_CONTAINER_CANDIDATES:
        result = subprocess.run(
            [docker_bin, "ps", "--filter", f"name={name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if lines:
            return lines[0]
    return None


def _publish_via_docker(topic: str, payload: dict[str, Any]) -> bool:
    container = _find_local_broker_container()
    if not container:
        return False
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return False
    result = subprocess.run(
        [
            docker_bin,
            "exec",
            container,
            "mosquitto_pub",
            "-h",
            "localhost",
            "-u",
            USERNAME,
            "-P",
            PASSWORD,
            "-t",
            topic,
            "-m",
            json.dumps(payload, ensure_ascii=False),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True
    if result.stderr.strip():
        print(f"⚠️ Docker mosquitto_pub 失败，回退 paho: {result.stderr.strip()}")
    return False


def _is_capacitor_bank_device(device: Device) -> bool:
    return resolve_compensation_subtype(
        getattr(device, "device_type", None),
        getattr(device, "device_subtype", None),
    ) == "capacitor_bank_controller"


def list_capacitor_bank_devices(session: Session) -> None:
    devices = session.exec(select(Device).order_by(Device.id)).all()
    matched = [device for device in devices if _is_capacitor_bank_device(device)]
    if not matched:
        print("⚠️  系统中尚无 capacitor_bank_controller 类型的设备。")
        return
    print(f"\n{'ID':>4}  {'序列号':<16}  {'名称':<20}  {'位置':<20}  {'额定容量'}")
    print("-" * 75)
    for device in matched:
        print(
            f"{device.id:>4}  {device.sn or '--':<16}  {device.name:<20}  "
            f"{(device.location or '--'):<20}  {device.rated_capacity or '--'} kvar"
        )
    print()


def send_one(
    client: mqtt.Client,
    device: Device,
    timestamp: datetime,
    tick: int,
    options: ScenarioOptions,
    *,
    state: ControlSimulationState | None = None,
) -> bool:
    payload = _build_payload(device, timestamp, tick, options)
    payload = _with_control_state(payload, state or ControlSimulationState())
    ok = _publish_payload(client, TOPIC, payload)
    if ok:
        print(
            f"  [{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"profile={options.profile} topic={TOPIC} code={device.sn} "
            f"P={payload['power']}kW Q={payload['reactive_power']}kvar PF={payload['power_factor']} "
            f"status=0x{payload['jkwf_status']:04X} "
            f"reg1=0x{payload['circuit_state_1']:04X} reg2=0x{payload['circuit_state_2']:04X} reg3=0x{payload['circuit_state_3']:04X}"
        )
    return ok


def _apply_control_command(state: ControlSimulationState, command_payload: dict[str, Any]) -> tuple[bool, str]:
    command = str(command_payload.get("command") or "").strip().lower()
    if command == "start":
        state.enabled = True
        return True, "已切换为运行中"
    if command == "stop":
        state.enabled = False
        return True, "已切换为停用状态"
    if command == "write_parameter":
        parameter_key = command_payload.get("parameter_key")
        if not parameter_key:
            return False, "缺少 parameter_key，忽略写入"
        target_value = command_payload.get("target_value")
        state.parameter_overrides[str(parameter_key)] = target_value
        return True, f"已写入参数 {parameter_key}={target_value}"
    return False, f"暂不支持命令 {command or '<empty>'}"


def _publish_control_feedback(client: mqtt.Client, runtime: RuntimeContext, reason: str) -> bool:
    with runtime.lock:
        tick = runtime.tick
        runtime.tick += 1
        payload = _build_payload(runtime.device, datetime.now(), tick, runtime.options)
        payload = _with_control_state(payload, runtime.state)
        payload["control_feedback_reason"] = reason
    return _publish_payload(client, runtime.telemetry_topic, payload)


def _on_connect(client: mqtt.Client, runtime: RuntimeContext | None, flags, rc) -> None:
    if rc == 0 and runtime is not None:
        client.subscribe(runtime.control_topic, qos=1)
        print(f"👂 已监听控制主题: {runtime.control_topic}")
    elif rc != 0:
        print(f"❌ MQTT 连接失败: rc={rc}")


def _on_message(client: mqtt.Client, runtime: RuntimeContext | None, msg) -> None:
    if runtime is None:
        return
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception as exc:
        print(f"⚠️ 控制指令解析失败: {exc}")
        return

    with runtime.lock:
        accepted, message = _apply_control_command(runtime.state, payload)

    print(
        f"🎛️ 控制指令 topic={msg.topic} command={payload.get('command')} "
        f"accepted={accepted} detail={message}"
    )
    if accepted and runtime.publish_on_control:
        if _publish_control_feedback(client, runtime, message):
            print("   ↳ 已补发控制后参数/遥测快照")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="向电容补偿控制器发送场景化 MQTT 遥测数据")
    parser.add_argument("--list", action="store_true", help="列出系统中所有电容补偿控制器")
    parser.add_argument("--id", type=int, dest="device_id", help="目标设备 ID")
    parser.add_argument("--sn", dest="device_sn", help="目标设备序列号（与 --id 二选一）")
    parser.add_argument("--loop", type=int, default=1, help="发送条数（默认 1，0=无限循环）")
    parser.add_argument("--interval", type=float, default=3.0, help="连续发送时的间隔秒数（默认 3）")
    parser.add_argument("--backfill", type=int, default=0, help="补发历史条数（从起始时间向后）")
    parser.add_argument("--backfill-step", type=int, default=60, help="补发历史时每条的时间间隔（秒，默认 60）")
    parser.add_argument("--base-time", help="历史补发或定点发送起始时间，格式如 2026-04-14T09:00:00")
    parser.add_argument("--seed", type=int, help="固定随机扰动种子，便于复现同一组曲线")
    parser.add_argument("--profile", choices=PROFILE_CHOICES, default="normal", help="联调场景，默认 normal")
    parser.add_argument("--leading", choices=PHASE_FLAG_CHOICES, help="强制控制超前标志位")
    parser.add_argument("--undercurrent", choices=PHASE_FLAG_CHOICES, help="强制控制欠流标志位")
    parser.add_argument("--voltage-thd-alarm", choices=PHASE_FLAG_CHOICES, help="强制控制电压 THD 告警位")
    parser.add_argument("--current-thd-alarm", choices=PHASE_FLAG_CHOICES, help="强制控制电流 THD 告警位")
    parser.add_argument("--temp-alarm", choices=("on", "off"), help="强制控制温度告警位")
    parser.add_argument("--phase-a-groups", type=int, choices=range(0, 9), help="A 相投入路数（0-8）")
    parser.add_argument("--phase-b-groups", type=int, choices=range(0, 9), help="B 相投入路数（0-8）")
    parser.add_argument("--phase-c-groups", type=int, choices=range(0, 9), help="C 相投入路数（0-8）")
    parser.add_argument("--common-1-groups", type=int, choices=range(0, 9), help="公补 1-8 投入路数（0-8）")
    parser.add_argument("--common-2-groups", type=int, choices=range(0, 9), help="公补 9-16 投入路数（0-8）")
    parser.add_argument("--common-3-groups", type=int, choices=range(0, 9), help="公补 17-24 投入路数（0-8）")
    parser.add_argument("--no-control-listener", action="store_true", help="仅发送遥测，不监听控制主题")
    parser.add_argument("--no-control-feedback", action="store_true", help="收到控制指令后不立即补发反馈快照")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    options = ScenarioOptions(
        profile=args.profile,
        leading=args.leading,
        undercurrent=args.undercurrent,
        voltage_thd_alarm=args.voltage_thd_alarm,
        current_thd_alarm=args.current_thd_alarm,
        temp_alarm=args.temp_alarm,
        phase_a_groups=args.phase_a_groups,
        phase_b_groups=args.phase_b_groups,
        phase_c_groups=args.phase_c_groups,
        common_1_groups=args.common_1_groups,
        common_2_groups=args.common_2_groups,
        common_3_groups=args.common_3_groups,
    )
    base_time = _parse_datetime(args.base_time)

    with Session(engine) as session:
        if args.list:
            list_capacitor_bank_devices(session)
            return

        if args.device_id:
            device = session.get(Device, args.device_id)
        elif args.device_sn:
            device = session.exec(select(Device).where(Device.sn == args.device_sn)).first()
        else:
            print("❌ 请指定 --id 或 --sn，或使用 --list 查看可用设备")
            parser.print_help()
            return

        if not device:
            print("❌ 设备未找到")
            return
        if not _is_capacitor_bank_device(device):
            print(f"⚠️  设备 {device.name}（{device.device_type}/{device.device_subtype}）不是电容补偿控制器，仍继续发送...")

        print(
            f"\n▶  目标设备: [{device.id}] {device.name}  SN={device.sn}  "
            f"MQTT={BROKER}:{PORT} {TOPIC}  profile={options.profile}"
        )
        control_topic = f"{settings.mqtt_control_topic_prefix}{device.id}"
        state = ControlSimulationState(enabled=bool(device.is_active))
        runtime = RuntimeContext(
            device=device,
            options=options,
            state=state,
            telemetry_topic=TOPIC,
            control_topic=control_topic,
            publish_on_control=not args.no_control_feedback,
            lock=threading.Lock(),
        )

        try:
            client = _create_client(None if args.no_control_listener else runtime)
        except Exception as exc:
            print(f"❌ MQTT 连接失败: {exc}")
            return

        if args.no_control_listener:
            print("🔕 已禁用控制主题监听，仅发送遥测")
        else:
            print(f"🎚️  控制监听已开启: {control_topic}")

        if args.backfill > 0:
            start_time = base_time or (datetime.now() - timedelta(seconds=args.backfill * args.backfill_step))
            print(
                f"\n📅 补发历史数据：{args.backfill} 条，步长 {args.backfill_step}s，"
                f"起点 {start_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            success = 0
            for i in range(args.backfill):
                ts = start_time + timedelta(seconds=i * args.backfill_step)
                success += int(send_one(client, device, ts, tick=i, options=options, state=state))
            print(f"\n✅ 补发完成，成功 {success}/{args.backfill} 条\n")
            client.loop_stop()
            client.disconnect()
            return

        count = 0
        success = 0
        infinite = args.loop == 0
        total = args.loop
        print(f"\n📡 开始发送{'（无限循环，Ctrl+C 停止）' if infinite else f'，共 {total} 条'}\n")
        try:
            while infinite or count < total:
                current_time = (base_time + timedelta(seconds=count * args.interval)) if base_time else datetime.now()
                with runtime.lock:
                    runtime.tick = count
                    success += int(send_one(client, device, current_time, tick=count, options=options, state=state))
                count += 1
                if infinite or count < total:
                    time.sleep(args.interval)
        except KeyboardInterrupt:
            print(f"\n⏹  已停止，成功发送 {success}/{count} 条")
            client.loop_stop()
            client.disconnect()
            return

        print(f"\n✅ 完成，成功发送 {success}/{count} 条\n")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
