"""
MQTT 补偿设备族适配。

这里集中承载补偿类设备的字段别名、公共测点归一、专属遥测提取和控制回执入口，
避免通用 MQTT processor 随新增补偿子型继续膨胀。
"""

from __future__ import annotations

import math
from typing import Any, Optional

from sqlmodel import Session

COMPENSATION_FIELD_ALIASES = {
    # 无功功率别名（兼容多种厂商字段名）
    "kvar": "reactive_power",
    "q_power": "reactive_power",
    "react_pwr": "reactive_power",
    "var": "reactive_power",
    "reactive_q": "reactive_power",
    # SVG 专属字段别名
    "svg_output": "svg_reactive_output",
    "svg_kvar": "svg_reactive_output",
    "reactive_output": "svg_reactive_output",
    "cap_util": "capacity_utilization",
    "capacity_util": "capacity_utilization",
    "dir": "output_direction",
    "output_dir": "output_direction",
    # 三相电压 / 电流
    "ua": "voltage_a",
    "ub": "voltage_b",
    "uc": "voltage_c",
    "van": "voltage_a",
    "vbn": "voltage_b",
    "vcn": "voltage_c",
    "ia": "current_a",
    "ib": "current_b",
    "ic": "current_c",
    # 故障位别名
    "fault_ov": "overvoltage_fault",
    "fault_uv": "undervoltage_fault",
    "fault_oc": "overcurrent_fault",
    "fault_ot": "overtemp_fault",
    "fault_mod": "module_fault",
    "fault_fan": "fan_fault",
    "fault_com": "comm_fault",
    "fault_code": "current_fault_code",
    "alarm_code": "current_alarm_code",
    # 传统电容补偿控制器三相字段
    "pf_a": "power_factor_a",
    "pf_b": "power_factor_b",
    "pf_c": "power_factor_c",
    "cos_a": "power_factor_a",
    "cos_b": "power_factor_b",
    "cos_c": "power_factor_c",
    "p_a": "active_power_a",
    "p_b": "active_power_b",
    "p_c": "active_power_c",
    "q_a": "reactive_power_a",
    "q_b": "reactive_power_b",
    "q_c": "reactive_power_c",
    "step_state": "step_status",
    "circuit_state": "circuit_status",
    "common_step_state": "common_compensation_status",
    # 温度别名
    "temp_cab": "cabinet_temp",
    "temp_module": "module_temp",
    "temp_igbt": "igbt_temp",
    "temp_sink": "heatsink_temp",
    "vdc": "dc_bus_voltage",
    "dc_voltage": "dc_bus_voltage",
    # 状态位别名
    "run": "run_status",
    "stop": "stop_status",
    "auto": "auto_mode",
    "local": "local_mode",
    "breaker": "breaker_status",
    "freq": "frequency",
    # JKWF-LCD 视在功率
    "s_a": "apparent_power_a",
    "s_b": "apparent_power_b",
    "s_c": "apparent_power_c",
    # JKWF-LCD 电压谐波 THD（多种网关命名兼容）
    "thd_ua": "voltage_thd_a",
    "thd_ub": "voltage_thd_b",
    "thd_uc": "voltage_thd_c",
    "thd_va": "voltage_thd_a",
    "thd_vb": "voltage_thd_b",
    "thd_vc": "voltage_thd_c",
    # JKWF-LCD 谐波电流幅值
    "thd_ia": "current_harmonic_a",
    "thd_ib": "current_harmonic_b",
    "thd_ic": "current_harmonic_c",
    # JKWF-LCD 状态标志位寄存器原始值
    "jkwf_status": "jkwf_status_flags",
    # JKWF-LCD 电容回路投切状态寄存器（0x01~0x03）
    "circuit_state_1": "circuit_state_reg_1",
    "circuit_state_2": "circuit_state_reg_2",
    "circuit_state_3": "circuit_state_reg_3",
    # JKWF 参数快照字段
    "switch_on_pf": "switch_on_power_factor",
    "switch_off_pf": "switch_off_power_factor",
    "switch_on_delay": "switch_on_delay_seconds",
    "switch_off_delay": "switch_off_delay_seconds",
    "common_output_circuits": "common_output_circuit_count",
    "split_output_circuits": "split_output_circuit_count",
    "phase_a_capacity_steps_kvar": "phase_a_capacity_steps_kvar_json",
    "phase_b_capacity_steps_kvar": "phase_b_capacity_steps_kvar_json",
    "phase_c_capacity_steps_kvar": "phase_c_capacity_steps_kvar_json",
    "common_1_capacity_steps_kvar": "common_1_capacity_steps_kvar_json",
    "common_2_capacity_steps_kvar": "common_2_capacity_steps_kvar_json",
    "common_3_capacity_steps_kvar": "common_3_capacity_steps_kvar_json",
    "common_group_1_total_count": "common_1_circuit_total_count",
    "common_group_2_total_count": "common_2_circuit_total_count",
    "common_group_3_total_count": "common_3_circuit_total_count",
    "common_capacity_step": "common_step_capacity_kvar",
    "split_capacity_step": "split_step_capacity_kvar",
    "ct_ratio_primary": "ct_primary_current",
    "overvoltage_threshold_v": "overvoltage_threshold",
    "voltage_thd_threshold": "voltage_harmonic_threshold",
    "current_thd_threshold": "current_harmonic_threshold",
    "temperature_limit": "temperature_upper_limit",
    "alarm_event": "alarm_drive_event",
    "baudrate": "baud_rate",
    "terminal_scheme": "terminal_assignment_scheme",
    "current_polarity_identify": "current_polarity_identification_enabled",
}

CONTROL_RECEIPT_MESSAGE_TYPE = "control_receipt"
COMMAND_RESULT_MESSAGE_TYPE = "command_result"


def apply_compensation_field_aliases(data: dict[str, Any]) -> dict[str, Any]:
    """应用补偿设备族字段别名，保持规范字段优先。"""
    normalized = dict(data)
    for alias, canonical in COMPENSATION_FIELD_ALIASES.items():
        if canonical not in normalized and alias in normalized:
            normalized[canonical] = normalized[alias]
    return normalized


def _parse_numeric(value: Any, field_name: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{field_name} 字段不是有效数值")
    return parsed


def _first_numeric(data: dict[str, Any], keys: tuple[str, ...]) -> Optional[float]:
    for key in keys:
        raw = data.get(key)
        if raw is None:
            continue
        try:
            return _parse_numeric(raw, key)
        except ValueError:
            continue
    return None


def _average_numeric(data: dict[str, Any], keys: tuple[str, ...]) -> Optional[float]:
    values = [_first_numeric(data, (key,)) for key in keys]
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return sum(valid) / len(valid)


def _sum_numeric(data: dict[str, Any], keys: tuple[str, ...]) -> Optional[float]:
    values = [_first_numeric(data, (key,)) for key in keys]
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return sum(valid)


def _sanitize_harmonic_spectrum(value: Any) -> Optional[list[dict[str, float | int]]]:
    """保留 2~31 次、有限数值的逐次谐波谱线。"""
    if not isinstance(value, list):
        return None

    by_order: dict[int, float] = {}
    for item in value:
        if not isinstance(item, dict):
            continue
        try:
            order = int(item.get("order"))
            magnitude = _parse_numeric(item.get("value"), "harmonic.value")
        except (TypeError, ValueError):
            continue
        if 2 <= order <= 31:
            by_order[order] = magnitude

    if not by_order:
        return None
    return [{"order": order, "value": by_order[order]} for order in sorted(by_order)]


def normalize_compensation_measurements(data: dict[str, Any]) -> dict[str, Any]:
    """将补偿控制器常见三相字段归一到公共字段层。"""
    normalized = dict(data)

    if normalized.get("voltage") is None:
        voltage = _average_numeric(normalized, ("voltage_a", "voltage_b", "voltage_c"))
        if voltage is not None:
            normalized["voltage"] = voltage

    if normalized.get("current") is None:
        current = _average_numeric(normalized, ("current_a", "current_b", "current_c"))
        if current is not None:
            normalized["current"] = current

    if normalized.get("power_factor") is None:
        power_factor = _average_numeric(normalized, ("power_factor_a", "power_factor_b", "power_factor_c"))
        if power_factor is not None:
            normalized["power_factor"] = power_factor

    if normalized.get("reactive_power") is None:
        reactive_power = _sum_numeric(normalized, ("reactive_power_a", "reactive_power_b", "reactive_power_c"))
        if reactive_power is not None:
            normalized["reactive_power"] = reactive_power

    if normalized.get("power") is None:
        active_power = _sum_numeric(normalized, ("active_power_a", "active_power_b", "active_power_c"))
        if active_power is not None:
            normalized["power"] = active_power

    if normalized.get("flow_rate") is None and normalized.get("power") is not None:
        normalized["flow_rate"] = normalized["power"]

    if normalized.get("temperature") is None:
        temperature = _first_numeric(normalized, ("cabinet_temp", "temp_cab", "temperature"))
        if temperature is not None:
            normalized["temperature"] = temperature

    return normalized


_SVG_TELEMETRY_FIELDS = (
    "voltage_a", "voltage_b", "voltage_c",
    "current_a", "current_b", "current_c",
    "frequency", "svg_reactive_output", "capacity_utilization", "output_direction",
    "run_status", "stop_status", "auto_mode", "local_mode",
    "breaker_status", "module_status", "fan_status", "comm_status",
    "overvoltage_fault", "undervoltage_fault", "overcurrent_fault", "overtemp_fault",
    "module_fault", "fan_fault", "comm_fault",
    "current_fault_code", "current_alarm_code",
    "cabinet_temp", "module_temp", "igbt_temp", "dc_bus_voltage", "heatsink_temp",
)


def extract_svg_telemetry(data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """从 payload 提取 SVGTelemetry 字段，无任何 SVG 专属字段时返回 None。"""
    extracted = {field: data[field] for field in _SVG_TELEMETRY_FIELDS if field in data and data[field] is not None}
    return extracted if extracted else None


_CAPACITOR_BANK_TELEMETRY_FIELDS = (
    "voltage_a", "voltage_b", "voltage_c",
    "current_a", "current_b", "current_c",
    "power_factor_a", "power_factor_b", "power_factor_c",
    "active_power_a", "active_power_b", "active_power_c",
    "reactive_power_a", "reactive_power_b", "reactive_power_c",
    "apparent_power_a", "apparent_power_b", "apparent_power_c",
    "voltage_thd_a", "voltage_thd_b", "voltage_thd_c",
    "current_harmonic_a", "current_harmonic_b", "current_harmonic_c",
    "voltage_harmonics_a", "voltage_harmonics_b", "voltage_harmonics_c",
    "current_harmonics_a", "current_harmonics_b", "current_harmonics_c",
    "frequency", "temperature",
    "leading_a", "leading_b", "leading_c",
    "undercurrent_a", "undercurrent_b", "undercurrent_c",
    "overvoltage_alarm_a", "overvoltage_alarm_b", "overvoltage_alarm_c",
    "voltage_thd_alarm_a", "voltage_thd_alarm_b", "voltage_thd_alarm_c",
    "current_thd_alarm_a", "current_thd_alarm_b", "current_thd_alarm_c",
    "temp_alarm",
    "circuit_state_phase_a", "circuit_state_phase_b", "circuit_state_phase_c",
    "circuit_state_common_1", "circuit_state_common_2", "circuit_state_common_3",
    "phase_a_circuit_running_count", "phase_b_circuit_running_count", "phase_c_circuit_running_count",
    "common_group_1_running_count", "common_group_2_running_count", "common_group_3_running_count",
    "split_circuit_running_count", "common_circuit_running_count", "running_circuit_count",
    "control_mode", "auto_on_elapsed_seconds", "auto_off_elapsed_seconds", "last_auto_action",
)

_CAPACITOR_BANK_CONTROL_PROFILE_FIELDS = (
    "switch_on_power_factor",
    "switch_off_power_factor",
    "switch_on_delay_seconds",
    "switch_off_delay_seconds",
    "common_output_circuit_count",
    "split_output_circuit_count",
    "phase_a_circuit_total_count",
    "phase_b_circuit_total_count",
    "phase_c_circuit_total_count",
    "common_1_circuit_total_count",
    "common_2_circuit_total_count",
    "common_3_circuit_total_count",
    "phase_a_capacity_steps_kvar_json",
    "phase_b_capacity_steps_kvar_json",
    "phase_c_capacity_steps_kvar_json",
    "common_1_capacity_steps_kvar_json",
    "common_2_capacity_steps_kvar_json",
    "common_3_capacity_steps_kvar_json",
    "phase_a_circuit_running_count",
    "phase_b_circuit_running_count",
    "phase_c_circuit_running_count",
    "common_group_1_running_count",
    "common_group_2_running_count",
    "common_group_3_running_count",
    "split_circuit_running_count",
    "common_circuit_running_count",
    "running_circuit_count",
    "control_mode",
    "auto_on_elapsed_seconds",
    "auto_off_elapsed_seconds",
    "last_auto_action",
    "common_capacity_code",
    "split_capacity_code",
    "common_step_capacity_kvar",
    "split_step_capacity_kvar",
    "ct_primary_current",
    "overvoltage_threshold",
    "voltage_harmonic_threshold",
    "current_harmonic_threshold",
    "temperature_upper_limit",
    "alarm_drive_event",
    "baud_rate",
    "terminal_assignment_scheme",
    "current_polarity_identification_enabled",
)


def extract_capacitor_bank_telemetry(data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """从 payload 提取 CapacitorBankTelemetry 字段，并应用 JKWF-LCD 协议解码。"""
    from app.integrations.jkwf_lcd.decoder import decode_jkwf_payload

    decoded = decode_jkwf_payload(data)
    merged = {**data, **{key: value for key, value in decoded.items() if key not in data}}
    for field in (
        "voltage_harmonics_a", "voltage_harmonics_b", "voltage_harmonics_c",
        "current_harmonics_a", "current_harmonics_b", "current_harmonics_c",
    ):
        sanitized = _sanitize_harmonic_spectrum(merged.get(field))
        if sanitized is not None:
            merged[field] = sanitized
        else:
            merged.pop(field, None)

    extracted = {
        field: merged[field]
        for field in _CAPACITOR_BANK_TELEMETRY_FIELDS
        if field in merged and merged[field] is not None
    }
    return extracted if extracted else None


def extract_capacitor_bank_control_profile(data: dict[str, Any]) -> Optional[dict[str, Any]]:
    extracted = {
        field: data[field]
        for field in _CAPACITOR_BANK_CONTROL_PROFILE_FIELDS
        if field in data and data[field] is not None
    }
    return extracted if extracted else None


def is_control_receipt_payload(data: dict[str, Any]) -> bool:
    return str(data.get("message_type") or "").strip().lower() in {
        CONTROL_RECEIPT_MESSAGE_TYPE,
        COMMAND_RESULT_MESSAGE_TYPE,
    }


def process_control_receipt(session: Session, data: dict[str, Any], device_id: int) -> None:
    from app.services.devices.compensation.capacitor_bank.control_command_service import CapacitorBankControlCommandService

    command_id = data.get("command_id")
    result = CapacitorBankControlCommandService.normalize_control_result(data.get("result"))
    detail = data.get("detail") or data.get("reason") or data.get("message")
    CapacitorBankControlCommandService.apply_control_receipt(
        session,
        device_id=device_id,
        command_id=command_id,
        result=result,
        detail=detail,
        control_event_notifier=CapacitorBankControlCommandService.publish_control_log_update_event,
    )
