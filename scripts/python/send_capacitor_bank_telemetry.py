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
CONTROL_PROTOCOL_VERSION = "campus-control.v1"
CAPACITY_CODE_PATTERNS = {
    0: "1111",
    1: "1222",
    2: "1244",
    3: "1248",
    4: "1233",
    5: "1236",
    6: "1122",
    7: "1124",
    8: "1128",
    9: "1123",
    10: "1126",
    11: "1881",
}


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
    control_mode: str = "auto"
    parameter_overrides: dict[str, Any] | None = None
    tick_interval_seconds: float = 3.0
    auto_pending_action: str | None = None
    auto_pending_elapsed_seconds: float = 0.0
    min_action_interval_seconds: float = 6.0
    last_action_elapsed_seconds: float = 999999.0

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


def _calculate_power_factor(active_power: float, reactive_power: float) -> float:
    apparent_power = math.sqrt(active_power ** 2 + reactive_power ** 2)
    if apparent_power <= 0:
        return 1.0
    return min(0.999, max(0.0, abs(active_power) / apparent_power))


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
            "current_amp": 0.0,
            "active_power_amp": 0.0,
            "reactive_power_amp": 0.0,
        })
    elif profile == "harmonic":
        base.update({
            "voltage_thd_a_base": 4.6,
            "voltage_thd_b_base": 4.8,
            "voltage_thd_c_base": 4.7,
            "current_harmonic_a_base": 2.9,
            "current_harmonic_b_base": 2.8,
            "current_harmonic_c_base": 3.0,
            "current_amp": 0.0,
            "active_power_amp": 0.0,
            "reactive_power_amp": 0.0,
        })
    elif profile == "overtemp":
        base.update({
            "temperature_base": 54.8,
            "temperature_amp": 0.8,
            "current_a_base": 96.0,
            "current_b_base": 93.0,
            "current_c_base": 98.0,
            "current_amp": 0.0,
            "active_power_amp": 0.0,
            "reactive_power_amp": 0.0,
        })
    elif profile == "undercurrent":
        base.update({
            "current_a_base": 10.0,
            "current_b_base": 8.5,
            "current_c_base": 9.2,
            "current_amp": 0.0,
            "active_power_a_base": 4.0,
            "active_power_b_base": 3.6,
            "active_power_c_base": 3.8,
            "active_power_amp": 0.0,
            "reactive_power_a_base": -1.8,
            "reactive_power_b_base": -1.4,
            "reactive_power_c_base": -1.6,
            "reactive_power_amp": 0.0,
        })
    elif profile == "unbalance":
        base.update({
            "voltage_a_base": 223.0,
            "voltage_b_base": 216.5,
            "voltage_c_base": 229.0,
            "voltage_amp": 0.0,
            "current_a_base": 112.0,
            "current_b_base": 74.0,
            "current_c_base": 96.0,
            "current_amp": 0.0,
            "active_power_a_base": 25.0,
            "active_power_b_base": 12.5,
            "active_power_c_base": 20.0,
            "active_power_amp": 0.0,
            "reactive_power_a_base": -8.5,
            "reactive_power_b_base": -12.0,
            "reactive_power_c_base": -4.5,
            "reactive_power_amp": 0.0,
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


def _distribute_balanced(total: int, buckets: int, max_per_bucket: int) -> list[int]:
    total = max(0, min(total, buckets * max_per_bucket))
    if buckets <= 0:
        return []
    base = total // buckets
    remainder = total % buckets
    result = [base + (1 if index < remainder else 0) for index in range(buckets)]
    return [min(max_per_bucket, value) for value in result]


def _distribute_sequential(total: int, bucket_sizes: tuple[int, ...]) -> list[int]:
    remaining = max(0, total)
    result: list[int] = []
    for size in bucket_sizes:
        allocated = min(size, remaining)
        result.append(allocated)
        remaining -= allocated
    return result


def _distribute_by_weight(total: float, weights: tuple[float, float, float]) -> tuple[float, float, float]:
    normalized = [max(0.0, value) for value in weights]
    weight_sum = sum(normalized)
    if weight_sum <= 0:
        even = total / 3 if total else 0.0
        return (even, even, even)
    return tuple(total * value / weight_sum for value in normalized)


def _resolve_capacity_pattern(capacity_code: str | int | None) -> str:
    if capacity_code is None:
        return CAPACITY_CODE_PATTERNS[0]

    if isinstance(capacity_code, int):
        return CAPACITY_CODE_PATTERNS.get(capacity_code, CAPACITY_CODE_PATTERNS[0])

    normalized = str(capacity_code).strip()
    if not normalized:
        return CAPACITY_CODE_PATTERNS[0]

    if ":" in normalized:
        _, suffix = normalized.split(":", 1)
        digits = "".join(char for char in suffix if char.isdigit())
        if digits:
            return digits

    if normalized.isdigit() and len(normalized) == 1:
        return CAPACITY_CODE_PATTERNS.get(int(normalized), CAPACITY_CODE_PATTERNS[0])

    digits = "".join(char for char in normalized if char.isdigit())
    if digits:
        return digits
    return CAPACITY_CODE_PATTERNS[0]


def _expand_capacity_slots(capacity_code: str | int | None, step_kvar: float, count: int) -> list[float]:
    pattern = _resolve_capacity_pattern(capacity_code)
    if count <= 0 or not pattern:
        return []
    digits = [max(1, int(char)) for char in pattern]
    slots: list[float] = []
    while len(slots) < count:
        for digit in digits:
            slots.append(round(step_kvar * digit, 4))
            if len(slots) >= count:
                break
    return slots


def _normalize_capacity_slots(slots: list[float], base_unit: float) -> list[float]:
    non_zero_slots = [slot for slot in slots if slot > 0]
    if not non_zero_slots:
        return [base_unit for _ in slots]
    min_slot = min(non_zero_slots)
    return [round(base_unit * (slot / min_slot), 4) for slot in slots]


def _build_split_phase_slot_kvar(capacity_code: str | int | None, step_kvar: float, count: int) -> dict[str, list[float]]:
    slot_values = _expand_capacity_slots(capacity_code, step_kvar, count)
    phase_keys = ("phase_a_groups", "phase_b_groups", "phase_c_groups")
    phase_capacities = _distribute_balanced(count, buckets=3, max_per_bucket=8)
    phase_slots = {key: [] for key in phase_keys}
    phase_index = 0
    for slot in slot_values:
        attempts = 0
        while attempts < len(phase_keys):
            key = phase_keys[phase_index]
            if len(phase_slots[key]) < phase_capacities[phase_index]:
                phase_slots[key].append(slot)
                phase_index = (phase_index + 1) % len(phase_keys)
                break
            phase_index = (phase_index + 1) % len(phase_keys)
            attempts += 1
    return phase_slots


def _build_common_stage_slot_kvar(capacity_code: str | int | None, step_kvar: float, count: int) -> dict[str, list[float]]:
    slot_values = _expand_capacity_slots(capacity_code, step_kvar, count)
    stage_keys = ("common_1_groups", "common_2_groups", "common_3_groups")
    stage_capacities = _distribute_sequential(count, (8, 8, 8))
    stage_slots: dict[str, list[float]] = {}
    cursor = 0
    for key, stage_count in zip(stage_keys, stage_capacities):
        stage_slots[key] = slot_values[cursor:cursor + stage_count]
        cursor += stage_count
    return stage_slots


def _sum_active_slot_kvar(slot_values: list[float], active_groups: int) -> float:
    return round(sum(slot_values[:max(0, min(active_groups, len(slot_values)))]), 4)


def _resolve_split_phase_slot_kvar(payload: dict[str, Any]) -> dict[str, list[float]]:
    split_phase_slot_kvar = payload.get("_split_phase_slot_kvar")
    if isinstance(split_phase_slot_kvar, dict):
        return {
            "phase_a_groups": [float(value) for value in split_phase_slot_kvar.get("phase_a_groups", [])],
            "phase_b_groups": [float(value) for value in split_phase_slot_kvar.get("phase_b_groups", [])],
            "phase_c_groups": [float(value) for value in split_phase_slot_kvar.get("phase_c_groups", [])],
        }
    split_group_kvar = float(payload.get("_split_group_kvar", 1.25) or 1.25)
    return {
        "phase_a_groups": [split_group_kvar] * 8,
        "phase_b_groups": [split_group_kvar] * 8,
        "phase_c_groups": [split_group_kvar] * 8,
    }


def _resolve_common_stage_slot_kvar(payload: dict[str, Any]) -> dict[str, list[float]]:
    common_stage_slot_kvar = payload.get("_common_stage_slot_kvar")
    if isinstance(common_stage_slot_kvar, dict):
        return {
            "common_1_groups": [float(value) for value in common_stage_slot_kvar.get("common_1_groups", [])],
            "common_2_groups": [float(value) for value in common_stage_slot_kvar.get("common_2_groups", [])],
            "common_3_groups": [float(value) for value in common_stage_slot_kvar.get("common_3_groups", [])],
        }
    return {
        "common_1_groups": [float(payload.get("_common_1_group_kvar", 1.5) or 1.5)] * 8,
        "common_2_groups": [float(payload.get("_common_2_group_kvar", 1.0) or 1.0)] * 8,
        "common_3_groups": [float(payload.get("_common_3_group_kvar", 0.5) or 0.5)] * 8,
    }


def _next_slot_kvar(slot_map: dict[str, list[float]], key: str, current_count: int) -> float | None:
    slot_values = slot_map.get(key, [])
    if current_count < 0 or current_count >= len(slot_values):
        return None
    return float(slot_values[current_count])


def _last_active_slot_kvar(slot_map: dict[str, list[float]], key: str, current_count: int) -> float | None:
    slot_values = slot_map.get(key, [])
    if current_count <= 0 or current_count > len(slot_values):
        return None
    return float(slot_values[current_count - 1])


def _choose_best_common_action(
    slot_map: dict[str, list[float]],
    current_counts: dict[str, int],
    target_kvar: float,
    direction: str,
    max_depth: int = 2,
) -> str | None:
    common_keys = ("common_1_groups", "common_2_groups", "common_3_groups")

    def candidate_actions(counts: dict[str, int]) -> list[tuple[str, float]]:
        actions: list[tuple[str, float]] = []
        for key in common_keys:
            if direction == "on":
                action_kvar = _next_slot_kvar(slot_map, key, counts.get(key, 0))
            else:
                action_kvar = _last_active_slot_kvar(slot_map, key, counts.get(key, 0))
            if action_kvar is not None:
                actions.append((key, action_kvar))
        return actions

    def search(counts: dict[str, int], remaining_kvar: float, depth: int) -> tuple[float, float, float, str | None]:
        best_score = (abs(remaining_kvar), abs(remaining_kvar), 0.0, None)
        if depth <= 0:
            return best_score

        for key, action_kvar in candidate_actions(counts):
            next_counts = dict(counts)
            if direction == "on":
                next_counts[key] = next_counts.get(key, 0) + 1
            else:
                next_counts[key] = next_counts.get(key, 0) - 1
            next_remaining = remaining_kvar - action_kvar
            child_abs, _, _, _ = search(next_counts, next_remaining, depth - 1)
            score = (child_abs, abs(next_remaining), -action_kvar, key)
            if score < best_score:
                best_score = score
        return best_score

    _, _, _, best_key = search(dict(current_counts), target_kvar, max_depth)
    return best_key


def _get_group_override(state: ControlSimulationState, key: str, fallback: int = 0) -> int:
    return int(state.parameter_overrides.get(key, fallback) or 0)


def _set_group_override(state: ControlSimulationState, key: str, value: int) -> None:
    state.parameter_overrides[key] = max(0, value)


def _bit_count(value: int) -> int:
    return bin(max(0, value)).count("1")


def _extract_group_counts_from_payload(payload: dict[str, Any]) -> dict[str, int]:
    circuit_state_1 = int(payload.get("circuit_state_1", 0) or 0)
    circuit_state_2 = int(payload.get("circuit_state_2", 0) or 0)
    circuit_state_3 = int(payload.get("circuit_state_3", 0) or 0)
    return {
        "phase_a_groups": _bit_count((circuit_state_1 >> 8) & 0xFF),
        "phase_b_groups": _bit_count(circuit_state_1 & 0xFF),
        "phase_c_groups": _bit_count((circuit_state_2 >> 8) & 0xFF),
        "common_1_groups": _bit_count(circuit_state_2 & 0xFF),
        "common_2_groups": _bit_count((circuit_state_3 >> 8) & 0xFF),
        "common_3_groups": _bit_count(circuit_state_3 & 0xFF),
    }


def _common_stage_kvar_map(payload: dict[str, Any]) -> dict[str, float]:
    common_stage_slot_kvar = payload.get("_common_stage_slot_kvar")
    if isinstance(common_stage_slot_kvar, dict):
        result: dict[str, float] = {}
        for key in ("common_1_groups", "common_2_groups", "common_3_groups"):
            slot_values = [float(value) for value in common_stage_slot_kvar.get(key, [])]
            result[key] = float(slot_values[0]) if slot_values else 0.0
        return result
    return {
        "common_1_groups": float(payload.get("_common_1_group_kvar", 1.5) or 1.5),
        "common_2_groups": float(payload.get("_common_2_group_kvar", 1.0) or 1.0),
        "common_3_groups": float(payload.get("_common_3_group_kvar", 0.5) or 0.5),
    }


def _apply_auto_control_step(payload: dict[str, Any], state: ControlSimulationState) -> bool:
    state.last_action_elapsed_seconds += state.tick_interval_seconds
    if not state.enabled or state.control_mode != "auto":
        state.auto_pending_action = None
        state.auto_pending_elapsed_seconds = 0.0
        return False

    on_threshold = float(payload.get("switch_on_power_factor", 95) or 95) / 100.0
    off_threshold = min(float(payload.get("switch_off_power_factor", 105) or 105) / 100.0, 0.999)
    current_pf = float(payload.get("power_factor", 1.0) or 1.0)
    current_q = float(payload.get("reactive_power", 0.0) or 0.0)
    leading_count = sum(bool(payload.get(key)) for key in ("leading_a", "leading_b", "leading_c"))
    pf_deadband = 0.005
    q_deadband = 0.5

    desired_action: str | None = None
    if current_q > q_deadband and current_pf < (on_threshold - pf_deadband):
        desired_action = "on"
    elif current_q < -q_deadband and (leading_count >= 2 or current_pf >= min(off_threshold + pf_deadband, 0.999)):
        desired_action = "off"

    if desired_action is None:
        state.auto_pending_action = None
        state.auto_pending_elapsed_seconds = 0.0
        return False

    if state.last_action_elapsed_seconds < state.min_action_interval_seconds:
        state.auto_pending_action = None
        state.auto_pending_elapsed_seconds = 0.0
        return False

    if state.auto_pending_action != desired_action:
        state.auto_pending_action = desired_action
        state.auto_pending_elapsed_seconds = state.tick_interval_seconds
    else:
        state.auto_pending_elapsed_seconds += state.tick_interval_seconds

    delay_seconds = float(
        payload.get("switch_on_delay_seconds", 10) if desired_action == "on"
        else payload.get("switch_off_delay_seconds", 8)
    )
    if state.auto_pending_elapsed_seconds < delay_seconds:
        return False

    phase_keys = ("phase_a_groups", "phase_b_groups", "phase_c_groups")
    common_keys = ("common_1_groups", "common_2_groups", "common_3_groups")
    split_phase_slot_kvar = _resolve_split_phase_slot_kvar(payload)
    common_stage_slot_kvar = _resolve_common_stage_slot_kvar(payload)
    phase_capacity_map = {key: len(split_phase_slot_kvar.get(key, [])) for key in phase_keys}
    common_capacity_map = {key: len(common_stage_slot_kvar.get(key, [])) for key in common_keys}
    phase_reactive_map = {
        "phase_a_groups": float(payload.get("reactive_power_a", 0.0) or 0.0),
        "phase_b_groups": float(payload.get("reactive_power_b", 0.0) or 0.0),
        "phase_c_groups": float(payload.get("reactive_power_c", 0.0) or 0.0),
    }
    if desired_action == "on":
        prioritized_phase_keys = sorted(
            phase_keys,
            key=lambda key: phase_reactive_map[key],
            reverse=True,
        )
        for key in prioritized_phase_keys:
            if _get_group_override(state, key) < phase_capacity_map.get(key, 0):
                _set_group_override(state, key, _get_group_override(state, key) + 1)
                state.auto_pending_action = None
                state.auto_pending_elapsed_seconds = 0.0
                state.last_action_elapsed_seconds = 0.0
                return True
        remaining_gap = max(current_q, 0.0)
        current_common_counts = {key: _get_group_override(state, key) for key in common_keys}
        best_common_key = _choose_best_common_action(
            common_stage_slot_kvar,
            current_common_counts,
            remaining_gap,
            direction="on",
            max_depth=2,
        )
        if best_common_key:
            _set_group_override(state, best_common_key, _get_group_override(state, best_common_key) + 1)
            state.auto_pending_action = None
            state.auto_pending_elapsed_seconds = 0.0
            state.last_action_elapsed_seconds = 0.0
            return True
    else:
        prioritized_phase_keys = sorted(
            [key for key in phase_keys if _get_group_override(state, key) > 0],
            key=lambda key: phase_reactive_map[key],
        )
        most_overcompensated_phase = prioritized_phase_keys[0] if prioritized_phase_keys else None
        mild_overcompensation = (
            most_overcompensated_phase is None
            or phase_reactive_map[most_overcompensated_phase] > -1.5
        )
        if prioritized_phase_keys and not mild_overcompensation and phase_reactive_map[most_overcompensated_phase] < -0.5:
            key = most_overcompensated_phase
            _set_group_override(state, key, _get_group_override(state, key) - 1)
            state.auto_pending_action = None
            state.auto_pending_elapsed_seconds = 0.0
            state.last_action_elapsed_seconds = 0.0
            return True
        remaining_overcomp = abs(min(current_q, 0.0))
        current_common_counts = {key: _get_group_override(state, key) for key in common_keys}
        best_common_key = _choose_best_common_action(
            common_stage_slot_kvar,
            current_common_counts,
            remaining_overcomp,
            direction="off",
            max_depth=2,
        )
        if best_common_key:
            _set_group_override(state, best_common_key, _get_group_override(state, best_common_key) - 1)
            state.auto_pending_action = None
            state.auto_pending_elapsed_seconds = 0.0
            state.last_action_elapsed_seconds = 0.0
            return True
        for key in prioritized_phase_keys:
            if _get_group_override(state, key) > 0:
                _set_group_override(state, key, _get_group_override(state, key) - 1)
                state.auto_pending_action = None
                state.auto_pending_elapsed_seconds = 0.0
                state.last_action_elapsed_seconds = 0.0
                return True

    return False


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

    active_power_a = max(0.5, _wave(base["active_power_a_base"], base["active_power_amp"], t, 90))
    active_power_b = max(0.5, _wave(base["active_power_b_base"], base["active_power_amp"], t + 20, 90))
    active_power_c = max(0.5, _wave(base["active_power_c_base"], base["active_power_amp"], t + 40, 90))

    baseline_target_reactive_power_a = min(-0.2, _wave(base["reactive_power_a_base"], base["reactive_power_amp"], t, 90))
    baseline_target_reactive_power_b = min(-0.2, _wave(base["reactive_power_b_base"], base["reactive_power_amp"] * 0.9, t + 20, 90))
    baseline_target_reactive_power_c = min(-0.2, _wave(base["reactive_power_c_base"], base["reactive_power_amp"], t + 40, 90))

    voltage_thd_a = max(0.1, _wave(base["voltage_thd_a_base"], base["voltage_thd_amp"], t, 180))
    voltage_thd_b = max(0.1, _wave(base["voltage_thd_b_base"], base["voltage_thd_amp"] * 0.8, t + 20, 180))
    voltage_thd_c = max(0.1, _wave(base["voltage_thd_c_base"], base["voltage_thd_amp"], t + 40, 180))
    current_harmonic_a = max(0.1, _wave(base["current_harmonic_a_base"], base["current_harmonic_amp"], t, 180))
    current_harmonic_b = max(0.1, _wave(base["current_harmonic_b_base"], base["current_harmonic_amp"] * 0.86, t + 15, 180))
    current_harmonic_c = max(0.1, _wave(base["current_harmonic_c_base"], base["current_harmonic_amp"], t + 30, 180))
    temperature = _wave(base["temperature_base"], base["temperature_amp"], t, 180)
    frequency = _wave(base["frequency_base"], base["frequency_amp"], t, 300)

    power = active_power_a + active_power_b + active_power_c
    voltage = (voltage_a + voltage_b + voltage_c) / 3
    current = (current_a + current_b + current_c) / 3
    energy = round(max(0.0, power) * max(1, tick + 1) / 3600, 4)

    baseline_reactive_power = (
        baseline_target_reactive_power_a
        + baseline_target_reactive_power_b
        + baseline_target_reactive_power_c
    )
    phase_a_groups = round(min(8, max(0, abs(baseline_target_reactive_power_a) / 1.25)))
    phase_b_groups = round(min(8, max(0, abs(baseline_target_reactive_power_b) / 1.25)))
    phase_c_groups = round(min(8, max(0, abs(baseline_target_reactive_power_c) / 1.25)))
    common_1_groups = round(min(8, max(0, (abs(baseline_reactive_power) - 18) / 1.5)))
    common_2_groups = 1 if max(voltage_thd_a, voltage_thd_b, voltage_thd_c) > 3.4 else 0
    common_3_groups = 1 if temperature > 42.0 else 0

    if options.profile == "harmonic":
        common_2_groups = max(common_2_groups, 1)
    if options.profile == "overtemp":
        common_3_groups = max(common_3_groups, 1)
    if options.profile == "unbalance":
        phase_a_groups = 2
        phase_b_groups = 3
        phase_c_groups = 2

    baseline_phase_a_groups = phase_a_groups
    baseline_phase_b_groups = phase_b_groups
    baseline_phase_c_groups = phase_c_groups
    baseline_common_1_groups = common_1_groups

    phase_a_groups = _clamp_group(options.phase_a_groups) if options.phase_a_groups is not None else baseline_phase_a_groups
    phase_b_groups = _clamp_group(options.phase_b_groups) if options.phase_b_groups is not None else baseline_phase_b_groups
    phase_c_groups = _clamp_group(options.phase_c_groups) if options.phase_c_groups is not None else baseline_phase_c_groups
    common_1_groups = _clamp_group(options.common_1_groups) if options.common_1_groups is not None else baseline_common_1_groups
    common_2_groups = _clamp_group(options.common_2_groups) if options.common_2_groups is not None else common_2_groups
    common_3_groups = _clamp_group(options.common_3_groups) if options.common_3_groups is not None else common_3_groups

    split_configured_count = 8
    common_configured_count = 12
    split_capacities = _distribute_balanced(split_configured_count, buckets=3, max_per_bucket=8)
    common_capacities = _distribute_sequential(common_configured_count, bucket_sizes=(8, 8, 8))

    baseline_phase_a_groups = min(baseline_phase_a_groups, split_capacities[0])
    baseline_phase_b_groups = min(baseline_phase_b_groups, split_capacities[1])
    baseline_phase_c_groups = min(baseline_phase_c_groups, split_capacities[2])
    baseline_common_1_groups = min(baseline_common_1_groups, common_capacities[0])
    phase_a_groups = min(phase_a_groups, split_capacities[0])
    phase_b_groups = min(phase_b_groups, split_capacities[1])
    phase_c_groups = min(phase_c_groups, split_capacities[2])
    common_1_groups = min(common_1_groups, common_capacities[0])
    common_2_groups = min(common_2_groups, common_capacities[1])
    common_3_groups = min(common_3_groups, common_capacities[2])

    common_capacity_code = "4:1233"
    split_capacity_code = "7:1124"
    common_step_capacity_kvar = 30.0
    split_step_capacity_kvar = 12.0

    simulated_split_phase_slots = _build_split_phase_slot_kvar(split_capacity_code, split_step_capacity_kvar, split_configured_count)
    simulated_common_stage_slots = _build_common_stage_slot_kvar(common_capacity_code, common_step_capacity_kvar, common_configured_count)

    split_capacities = [
        len(simulated_split_phase_slots["phase_a_groups"]),
        len(simulated_split_phase_slots["phase_b_groups"]),
        len(simulated_split_phase_slots["phase_c_groups"]),
    ]
    common_capacities = [
        len(simulated_common_stage_slots["common_1_groups"]),
        len(simulated_common_stage_slots["common_2_groups"]),
        len(simulated_common_stage_slots["common_3_groups"]),
    ]

    baseline_common_total_kvar = (
        _sum_active_slot_kvar(simulated_common_stage_slots["common_1_groups"], baseline_common_1_groups)
        + _sum_active_slot_kvar(simulated_common_stage_slots["common_2_groups"], common_2_groups)
        + _sum_active_slot_kvar(simulated_common_stage_slots["common_3_groups"], common_3_groups)
    )
    common_distribution = _distribute_by_weight(
        baseline_common_total_kvar,
        (
            abs(baseline_target_reactive_power_a),
            abs(baseline_target_reactive_power_b),
            abs(baseline_target_reactive_power_c),
        ),
    )
    baseline_compensation_a = _sum_active_slot_kvar(simulated_split_phase_slots["phase_a_groups"], baseline_phase_a_groups) + common_distribution[0]
    baseline_compensation_b = _sum_active_slot_kvar(simulated_split_phase_slots["phase_b_groups"], baseline_phase_b_groups) + common_distribution[1]
    baseline_compensation_c = _sum_active_slot_kvar(simulated_split_phase_slots["phase_c_groups"], baseline_phase_c_groups) + common_distribution[2]

    load_reactive_demand_a = max(0.1, baseline_compensation_a + baseline_target_reactive_power_a)
    load_reactive_demand_b = max(0.1, baseline_compensation_b + baseline_target_reactive_power_b)
    load_reactive_demand_c = max(0.1, baseline_compensation_c + baseline_target_reactive_power_c)

    final_common_distribution = _distribute_by_weight(
        (
            _sum_active_slot_kvar(simulated_common_stage_slots["common_1_groups"], common_1_groups)
            + _sum_active_slot_kvar(simulated_common_stage_slots["common_2_groups"], common_2_groups)
            + _sum_active_slot_kvar(simulated_common_stage_slots["common_3_groups"], common_3_groups)
        ),
        (load_reactive_demand_a, load_reactive_demand_b, load_reactive_demand_c),
    )
    reactive_power_a = round(
        load_reactive_demand_a - (_sum_active_slot_kvar(simulated_split_phase_slots["phase_a_groups"], phase_a_groups) + final_common_distribution[0]),
        4,
    )
    reactive_power_b = round(
        load_reactive_demand_b - (_sum_active_slot_kvar(simulated_split_phase_slots["phase_b_groups"], phase_b_groups) + final_common_distribution[1]),
        4,
    )
    reactive_power_c = round(
        load_reactive_demand_c - (_sum_active_slot_kvar(simulated_split_phase_slots["phase_c_groups"], phase_c_groups) + final_common_distribution[2]),
        4,
    )

    reactive_power_a = round(reactive_power_a, 2)
    reactive_power_b = round(reactive_power_b, 2)
    reactive_power_c = round(reactive_power_c, 2)
    apparent_power_a = math.sqrt(active_power_a ** 2 + reactive_power_a ** 2)
    apparent_power_b = math.sqrt(active_power_b ** 2 + reactive_power_b ** 2)
    apparent_power_c = math.sqrt(active_power_c ** 2 + reactive_power_c ** 2)
    power_factor_a = _calculate_power_factor(active_power_a, reactive_power_a)
    power_factor_b = _calculate_power_factor(active_power_b, reactive_power_b)
    power_factor_c = _calculate_power_factor(active_power_c, reactive_power_c)
    reactive_power = round(reactive_power_a + reactive_power_b + reactive_power_c, 2)
    power_factor = _calculate_power_factor(power, reactive_power)

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
        "reactive_power_a": reactive_power_a,
        "reactive_power_b": reactive_power_b,
        "reactive_power_c": reactive_power_c,
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
        "common_output_circuit_count": common_configured_count,
        "split_output_circuit_count": split_configured_count,
        "common_capacity_code": common_capacity_code,
        "split_capacity_code": split_capacity_code,
        "common_step_capacity_kvar": common_step_capacity_kvar,
        "split_step_capacity_kvar": split_step_capacity_kvar,
        "ct_primary_current": 300,
        "overvoltage_threshold": 245.0,
        "voltage_harmonic_threshold": 4.5,
        "current_harmonic_threshold": 2.8,
        "temperature_upper_limit": 55.0,
        "alarm_drive_event": "过压切除",
        "baud_rate": 9600,
        "terminal_assignment_scheme": "方案1",
        "current_polarity_identification_enabled": True,
        "_load_reactive_demand_a": round(load_reactive_demand_a, 4),
        "_load_reactive_demand_b": round(load_reactive_demand_b, 4),
        "_load_reactive_demand_c": round(load_reactive_demand_c, 4),
        "_split_phase_slot_kvar": simulated_split_phase_slots,
        "_common_stage_slot_kvar": simulated_common_stage_slots,
        "_split_group_kvar": 1.25,
        "_common_1_group_kvar": 1.5,
        "_common_2_group_kvar": 1.0,
        "_common_3_group_kvar": 0.5,
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
        payload.update(state.parameter_overrides)
        return payload
    else:
        payload["simulated_device_enabled"] = True

    group_counts = _extract_group_counts_from_payload(payload)
    for key in group_counts:
        if key in state.parameter_overrides:
            group_counts[key] = max(0, int(state.parameter_overrides[key] or 0))

    split_phase_slot_kvar = payload.get("_split_phase_slot_kvar")
    if not isinstance(split_phase_slot_kvar, dict):
        split_group_kvar = float(payload.get("_split_group_kvar", 1.25) or 1.25)
        split_phase_slot_kvar = {
            "phase_a_groups": [split_group_kvar] * 8,
            "phase_b_groups": [split_group_kvar] * 8,
            "phase_c_groups": [split_group_kvar] * 8,
        }
    common_stage_slot_kvar = payload.get("_common_stage_slot_kvar")
    if not isinstance(common_stage_slot_kvar, dict):
        common_stage_slot_kvar = {
            "common_1_groups": [float(payload.get("_common_1_group_kvar", 1.5) or 1.5)] * 8,
            "common_2_groups": [float(payload.get("_common_2_group_kvar", 1.0) or 1.0)] * 8,
            "common_3_groups": [float(payload.get("_common_3_group_kvar", 0.5) or 0.5)] * 8,
        }
    load_reactive_demand_a = float(payload.get("_load_reactive_demand_a", 0.1) or 0.1)
    load_reactive_demand_b = float(payload.get("_load_reactive_demand_b", 0.1) or 0.1)
    load_reactive_demand_c = float(payload.get("_load_reactive_demand_c", 0.1) or 0.1)

    phase_keys = ("phase_a_groups", "phase_b_groups", "phase_c_groups")
    common_keys = ("common_1_groups", "common_2_groups", "common_3_groups")
    for key in phase_keys:
        group_counts[key] = min(group_counts[key], len(split_phase_slot_kvar.get(key, [])))
    for key in common_keys:
        group_counts[key] = min(group_counts[key], len(common_stage_slot_kvar.get(key, [])))

    common_distribution = _distribute_by_weight(
        sum(_sum_active_slot_kvar(common_stage_slot_kvar.get(key, []), group_counts[key]) for key in common_keys),
        (load_reactive_demand_a, load_reactive_demand_b, load_reactive_demand_c),
    )
    reactive_power_a = round(
        load_reactive_demand_a - (_sum_active_slot_kvar(split_phase_slot_kvar.get("phase_a_groups", []), group_counts["phase_a_groups"]) + common_distribution[0]),
        4,
    )
    reactive_power_b = round(
        load_reactive_demand_b - (_sum_active_slot_kvar(split_phase_slot_kvar.get("phase_b_groups", []), group_counts["phase_b_groups"]) + common_distribution[1]),
        4,
    )
    reactive_power_c = round(
        load_reactive_demand_c - (_sum_active_slot_kvar(split_phase_slot_kvar.get("phase_c_groups", []), group_counts["phase_c_groups"]) + common_distribution[2]),
        4,
    )
    reactive_power = round(reactive_power_a + reactive_power_b + reactive_power_c, 4)

    payload["reactive_power_a"] = round(reactive_power_a, 2)
    payload["reactive_power_b"] = round(reactive_power_b, 2)
    payload["reactive_power_c"] = round(reactive_power_c, 2)
    payload["reactive_power"] = round(reactive_power, 2)
    payload["apparent_power_a"] = round(math.sqrt(payload["active_power_a"] ** 2 + reactive_power_a ** 2), 2)
    payload["apparent_power_b"] = round(math.sqrt(payload["active_power_b"] ** 2 + reactive_power_b ** 2), 2)
    payload["apparent_power_c"] = round(math.sqrt(payload["active_power_c"] ** 2 + reactive_power_c ** 2), 2)
    payload["power_factor_a"] = round(_calculate_power_factor(payload["active_power_a"], reactive_power_a), 4)
    payload["power_factor_b"] = round(_calculate_power_factor(payload["active_power_b"], reactive_power_b), 4)
    payload["power_factor_c"] = round(_calculate_power_factor(payload["active_power_c"], reactive_power_c), 4)
    payload["power_factor"] = round(_calculate_power_factor(payload["power"], reactive_power), 4)
    payload["leading_a"] = reactive_power_a < 0
    payload["leading_b"] = reactive_power_b < 0
    payload["leading_c"] = reactive_power_c < 0
    payload["circuit_state_1"] = (_build_mask(group_counts["phase_a_groups"]) << 8) | _build_mask(group_counts["phase_b_groups"])
    payload["circuit_state_2"] = (_build_mask(group_counts["phase_c_groups"]) << 8) | _build_mask(group_counts["common_1_groups"])
    payload["circuit_state_3"] = (_build_mask(group_counts["common_2_groups"]) << 8) | _build_mask(group_counts["common_3_groups"])
    payload["jkwf_status"] &= ~0x0007
    if payload["leading_a"]:
        payload["jkwf_status"] |= 1 << 0
    if payload["leading_b"]:
        payload["jkwf_status"] |= 1 << 1
    if payload["leading_c"]:
        payload["jkwf_status"] |= 1 << 2

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
    simulation_state = state or ControlSimulationState()
    base_payload = _build_payload(device, timestamp, tick, options)
    payload = _with_control_state(dict(base_payload), simulation_state)
    if _apply_auto_control_step(payload, simulation_state):
        payload = _with_control_state(dict(base_payload), simulation_state)
    publish_payload = {key: value for key, value in payload.items() if not key.startswith("_")}
    ok = _publish_payload(client, TOPIC, publish_payload)
    if ok:
        print(
            f"  [{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"profile={options.profile} topic={TOPIC} code={device.sn} "
            f"P={publish_payload['power']}kW Q={publish_payload['reactive_power']}kvar PF={publish_payload['power_factor']} "
            f"status=0x{publish_payload['jkwf_status']:04X} "
            f"reg1=0x{publish_payload['circuit_state_1']:04X} reg2=0x{publish_payload['circuit_state_2']:04X} reg3=0x{publish_payload['circuit_state_3']:04X}"
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
    if command == "manual_switch_test":
        current = int(state.parameter_overrides.get("circuit_state_common_1", 0) or 0)
        next_value = 0 if current >= 2 else current + 1
        state.parameter_overrides["circuit_state_common_1"] = next_value
        state.parameter_overrides["reactive_power"] = round(-18.0 - next_value * 2.5, 2)
        return True, f"已执行手动投切测试，公补 1 当前投入 {next_value} 组"
    if command == "manual_switch":
        manual_mode = str(command_payload.get("manual_mode") or "").strip().lower()
        phase = str(command_payload.get("phase") or "").strip().upper()
        switch_action = str(command_payload.get("switch_action") or "").strip().lower()
        if manual_mode not in {"manual", "auto"}:
            return False, "缺少合法 manual_mode=manual/auto"
        if phase not in {"A", "B", "C", "COMMON"}:
            return False, "缺少合法 phase=A/B/C/COMMON"
        if switch_action not in {"none", "on", "off"}:
            return False, "缺少合法 switch_action=none/on/off"

        state.control_mode = manual_mode
        state.parameter_overrides["terminal_assignment_scheme"] = "手动模式" if manual_mode == "manual" else "自动模式"
        state.parameter_overrides["auto_mode"] = manual_mode == "auto"
        if manual_mode == "auto":
            return True, "已切回自动模式"

        field_map = {
            "A": "circuit_state_phase_a",
            "B": "circuit_state_phase_b",
            "C": "circuit_state_phase_c",
            "COMMON": "circuit_state_common_1",
        }
        target_field = field_map[phase]
        current = int(state.parameter_overrides.get(target_field, 0) or 0)
        if switch_action == "on":
            next_value = current | 0x01
            action_text = "投入"
        elif switch_action == "off":
            next_value = current & 0xFE
            action_text = "切除"
        else:
            next_value = current
            action_text = "保持"
        state.parameter_overrides[target_field] = next_value
        state.parameter_overrides["reactive_power"] = round(-18.0 - (1 if switch_action == "on" else 0) * 2.5, 2)
        return True, f"已按协议手动投切：{phase} 相 {action_text}"
    if command == "reset_alarm":
        for field in (
            "temp_alarm",
            "overvoltage_alarm_a",
            "overvoltage_alarm_b",
            "overvoltage_alarm_c",
            "voltage_thd_alarm_a",
            "voltage_thd_alarm_b",
            "voltage_thd_alarm_c",
            "current_thd_alarm_a",
            "current_thd_alarm_b",
            "current_thd_alarm_c",
        ):
            state.parameter_overrides[field] = False
        state.parameter_overrides["jkwf_status"] = 0
        return True, "已执行报警复位，当前模拟告警位已清空"
    if command == "switch_control_mode":
        state.control_mode = "manual" if state.control_mode == "auto" else "auto"
        state.parameter_overrides["terminal_assignment_scheme"] = "手动模式" if state.control_mode == "manual" else "自动模式"
        state.parameter_overrides["auto_mode"] = state.control_mode == "auto"
        return True, f"已切换控制模式为 {state.control_mode}"
    return False, f"暂不支持命令 {command or '<empty>'}"


def _publish_control_feedback(client: mqtt.Client, runtime: RuntimeContext, reason: str) -> bool:
    with runtime.lock:
        tick = runtime.tick
        runtime.tick += 1
        payload = _build_payload(runtime.device, datetime.now(), tick, runtime.options)
        payload = _with_control_state(payload, runtime.state)
        payload["control_feedback_reason"] = reason
        payload["simulated_control_mode"] = runtime.state.control_mode
    publish_payload = {key: value for key, value in payload.items() if not key.startswith("_")}
    return _publish_payload(client, runtime.telemetry_topic, publish_payload)


def _publish_control_receipt(
    client: mqtt.Client,
    runtime: RuntimeContext,
    command_payload: dict[str, Any],
    *,
    result: str,
    detail: str,
) -> bool:
    command_id = command_payload.get("command_id")
    if not command_id:
        return False
    receipt_payload = {
        "message_type": "control_receipt",
        "protocol_version": CONTROL_PROTOCOL_VERSION,
        "timestamp": datetime.now().isoformat(),
        "device_id": runtime.device.id,
        "device_code": runtime.device.sn,
        "command_id": command_id,
        "command": command_payload.get("command"),
        "result": result,
        "detail": detail,
    }
    return _publish_payload(client, runtime.telemetry_topic, receipt_payload)


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
    if _publish_control_receipt(
        client,
        runtime,
        payload,
        result="success" if accepted else "failed",
        detail=message,
    ):
        print("   ↳ 已发送控制回执")
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
        control_topic = f"{settings.mqtt_control_topic_prefix}{device.sn}"
        state = ControlSimulationState(enabled=bool(device.is_active), tick_interval_seconds=args.interval)
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
