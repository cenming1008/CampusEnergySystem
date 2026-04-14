"""
MQTT 消息处理

负责解析 payload、标准化指标、落库与报警检查，并构造 WebSocket 广播消息。
"""

from __future__ import annotations

import json
import math
import hashlib
from time import perf_counter
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlmodel import Session, select

from app.application.telemetry_ingestion import ingest_telemetry_use_case
from app.core.database import engine
from app.core.logger import logger
from app.core.metrics import observe_mqtt_message
from app.core.runtime_state import runtime_state
from app.core.settings import settings
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_device_resolver import resolve_device_id
from app.services.mqtt_models import TelemetryBroadcastData, TelemetryBroadcastMessage
from app.services.mqtt_reliability_service import MqttReliabilityService
from app.domain.device_payloads import resolve_compensation_subtype
from app.models.tables import CapacitorBankTelemetry, Device, MqttIngestionRecord, SVGTelemetry
from app.services.capacitor_bank_service import CapacitorBankService


FIELD_ALIASES = {
    "device_sn": "device_code",
    "sn": "device_code",
    "meter_code": "device_code",
    "ts": "timestamp",
    "time": "timestamp",
    "collect_time": "timestamp",
    "active_power": "power",
    "kw": "power",
    "total_energy": "energy",
    "meter_reading": "consumption",
    "cum_value": "consumption",
    "pf": "power_factor",
    "temp": "temperature",
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
    # 三相电压
    "ua": "voltage_a",
    "ub": "voltage_b",
    "uc": "voltage_c",
    "van": "voltage_a",
    "vbn": "voltage_b",
    "vcn": "voltage_c",
    # 三相电流
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
    "ua": "voltage_a",
    "ub": "voltage_b",
    "uc": "voltage_c",
    "ia": "current_a",
    "ib": "current_b",
    "ic": "current_c",
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

MEANINGFUL_FIELDS = (
    "consumption",
    "energy",
    "flow_rate",
    "power",
    "heat_flow",
    "voltage",
    "current",
    "pressure",
    "temperature",
    "reactive_power",
)

CONTROL_RECEIPT_MESSAGE_TYPE = "control_receipt"


def apply_field_aliases(data: dict[str, Any]) -> dict[str, Any]:
    """兼容常见字段别名，保持原字段优先。"""
    normalized = dict(data)
    for alias, canonical in FIELD_ALIASES.items():
        if canonical not in normalized and alias in normalized:
            normalized[canonical] = normalized[alias]
    return normalized


def _first_numeric(data: dict[str, Any], keys: tuple[str, ...]) -> Optional[float]:
    for key in keys:
        raw = data.get(key)
        if raw is None:
            continue
        try:
            return parse_numeric(raw, key)
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


def parse_numeric(value: Any, field_name: str, default: Optional[float] = None) -> float:
    """解析数值字段，并拒绝 NaN/inf。"""
    if value is None:
        if default is None:
            raise ValueError(f"{field_name} 字段缺失")
        return default

    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{field_name} 字段不是有效数值")
    return parsed


def validate_timestamp(timestamp: datetime) -> datetime:
    """校验设备时间戳是否在可接受范围内。"""
    now = datetime.now()
    max_future_seconds = max(0, int(settings.mqtt_max_future_seconds))
    stale_data_days = max(0, int(settings.mqtt_stale_data_days))

    if timestamp > now and (timestamp - now).total_seconds() > max_future_seconds:
        raise ValueError("设备时间戳超前过多")

    if stale_data_days and timestamp < now - timedelta(days=stale_data_days):
        raise ValueError("设备时间戳过旧")

    return timestamp


def validate_payload_content(data: dict[str, Any]) -> None:
    """确保消息至少包含一项有效测点。"""
    if not any(data.get(field) is not None for field in MEANINGFUL_FIELDS):
        raise ValueError("MQTT payload 缺少有效测点")


def is_control_receipt_payload(data: dict[str, Any]) -> bool:
    return str(data.get("message_type") or "").strip().lower() == CONTROL_RECEIPT_MESSAGE_TYPE


def process_control_receipt(session: Session, data: dict[str, Any], device_id: int) -> None:
    command_id = data.get("command_id")
    result = data.get("result")
    detail = data.get("detail") or data.get("reason") or data.get("message")
    CapacitorBankService.apply_control_receipt(
        session,
        device_id=device_id,
        command_id=command_id,
        result=result,
        detail=detail,
    )


def parse_payload(payload_str: str) -> Optional[dict[str, Any]]:
    """将 MQTT payload 解析为 JSON 对象。"""
    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.warning("MQTT payload JSON decode failed, skipped")
        return None

    if not isinstance(data, dict):
        logger.warning("MQTT payload is not a JSON object, skipped")
        return None

    return data


def hash_payload_string(payload_str: str) -> str:
    """对原始 payload 字符串做哈希，便于失败重放和比对。"""
    return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()


def parse_timestamp(data: dict[str, Any]) -> datetime:
    """解析时间戳，缺失或非法时回退到当前时间。始终返回 naive datetime。"""
    timestamp = data.get("timestamp")
    if timestamp is None:
        return datetime.now()

    try:
        if isinstance(timestamp, str):
            normalized = timestamp.strip()
            if normalized.endswith("Z"):
                normalized = normalized[:-1] + "+00:00"
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is not None:
                dt = dt.astimezone(tz=None).replace(tzinfo=None)
            return dt

        return datetime.fromtimestamp(parse_numeric(timestamp, "timestamp"), tz=timezone.utc).replace(tzinfo=None)
    except Exception:
        logger.warning(f"MQTT timestamp parse failed, fallback to now: {timestamp!r}")
        return datetime.now()


def normalize_metrics(data: dict[str, Any]) -> tuple[float, float, float, float]:
    """标准化电压、电流、功率和能耗字段。"""
    voltage = parse_numeric(data.get("voltage"), "voltage", default=380.0)
    current = parse_numeric(data.get("current"), "current", default=0.0)

    if "power" in data and data["power"] is not None:
        power = parse_numeric(data["power"], "power")
    else:
        power = voltage * current / 1000.0

    energy = parse_numeric(data.get("energy"), "energy", default=0.0)
    return voltage, current, power, energy


def build_data_dict(data: dict[str, Any], voltage: float, current: float, power: float, energy: float) -> dict[str, Any]:
    """构建统一入库数据，保留 0 值并过滤 None。"""
    consumption = energy if energy > 0 else data.get("consumption", data.get("energy", 0.0))

    # reactive_power 允许负值（容性补偿为负），需单独解析以保留 0
    reactive_power_raw = data.get("reactive_power")
    reactive_power: Optional[float] = None
    if reactive_power_raw is not None:
        try:
            reactive_power = parse_numeric(reactive_power_raw, "reactive_power")
        except ValueError:
            reactive_power = None

    payload = {
        "consumption": parse_numeric(consumption, "consumption", default=0.0),
        "power": power,
        "voltage": voltage,
        "current": current,
        "power_factor": data.get("power_factor"),
        "reactive_power": reactive_power,
        "pressure": data.get("pressure"),
        "temperature": data.get("temperature"),
        "flow_rate": data.get("flow_rate"),
        "supply_temp": data.get("supply_temp", data.get("supply_temperature")),
        "return_temp": data.get("return_temp", data.get("return_temperature")),
        "heat_flow": data.get("heat_flow"),
        "heat_power": data.get("heat_power"),
        "cooling_power": data.get("cooling_power"),
    }

    return {key: value for key, value in payload.items() if value is not None}


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
    "frequency", "temperature",
    # 状态标志位（由 decoder 解码后注入）
    "leading_a", "leading_b", "leading_c",
    "undercurrent_a", "undercurrent_b", "undercurrent_c",
    "overvoltage_alarm_a", "overvoltage_alarm_b", "overvoltage_alarm_c",
    "voltage_thd_alarm_a", "voltage_thd_alarm_b", "voltage_thd_alarm_c",
    "current_thd_alarm_a", "current_thd_alarm_b", "current_thd_alarm_c",
    "temp_alarm",
    # 投切状态（由 decoder 解码后注入）
    "circuit_state_phase_a", "circuit_state_phase_b", "circuit_state_phase_c",
    "circuit_state_common_1", "circuit_state_common_2", "circuit_state_common_3",
)

_CAPACITOR_BANK_CONTROL_PROFILE_FIELDS = (
    "switch_on_power_factor",
    "switch_off_power_factor",
    "switch_on_delay_seconds",
    "switch_off_delay_seconds",
    "common_output_circuit_count",
    "split_output_circuit_count",
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

    # 先将 JKWF-LCD 特有寄存器解码，并合并回 data（不覆盖已有值）
    decoded = decode_jkwf_payload(data)
    merged = {**data, **{k: v for k, v in decoded.items() if k not in data}}

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


def _is_svg_device(device_id: int, session: Session) -> bool:
    """判断设备是否为 SVG 补偿子类型。"""
    device = session.get(Device, device_id)
    return (
        device is not None
        and resolve_compensation_subtype(
            getattr(device, "device_type", None),
            getattr(device, "device_subtype", None),
        ) == "svg"
    )


def _is_capacitor_bank_device(device_id: int, session: Session) -> bool:
    """判断设备是否为传统电容补偿控制器子类型。"""
    device = session.get(Device, device_id)
    return (
        device is not None
        and resolve_compensation_subtype(
            getattr(device, "device_type", None),
            getattr(device, "device_subtype", None),
        ) == "capacitor_bank_controller"
    )


def persist_device_data(
    device_id: int,
    data_dict: dict[str, Any],
    timestamp: datetime,
    raw_data: Optional[dict[str, Any]] = None,
) -> TelemetryBroadcastData:
    """执行遥测接入用例并生成 WebSocket 广播数据。对 svg 设备额外写入 SVGTelemetry。"""
    with Session(engine) as session:
        result = ingest_telemetry_use_case(
            session=session,
            device_id=device_id,
            data=data_dict,
            timestamp=timestamp,
        )

        if raw_data is not None and _is_svg_device(device_id, session):
            svg_fields = extract_svg_telemetry(raw_data)
            if svg_fields:
                from app.services.alarm_service import AlarmService
                telemetry = SVGTelemetry(
                    device_id=device_id,
                    timestamp=timestamp,
                    **svg_fields,
                )
                session.add(telemetry)
                AlarmService.check_svg_faults(session, device_id, svg_fields, timestamp)

        if raw_data is not None and _is_capacitor_bank_device(device_id, session):
            cap_fields = extract_capacitor_bank_telemetry(raw_data)
            if cap_fields:
                cap_telemetry = CapacitorBankTelemetry(
                    device_id=device_id,
                    timestamp=timestamp,
                    **cap_fields,
                )
                session.add(cap_telemetry)
            cap_profile_fields = extract_capacitor_bank_control_profile(raw_data)
            if cap_profile_fields:
                CapacitorBankService.upsert_control_profile(
                    session,
                    device_id,
                    cap_profile_fields,
                    snapshot_timestamp=timestamp,
                    source="telemetry",
                )

        session.commit()
        return result.broadcast_data


def process_payload(payload_str: str, topic: Optional[str] = None) -> Optional[dict[str, Any]]:
    """处理单条 MQTT payload，返回可供 WebSocket 广播的消息。"""
    data = parse_payload(payload_str)
    if data is None:
        return None

    message = process_payload_dict(data, topic=topic, raw_payload=payload_str)
    return message.to_dict() if message else None


def process_payload_dict(
    data: dict[str, Any],
    topic: Optional[str] = None,
    raw_payload: Optional[str] = None,
) -> Optional[TelemetryBroadcastMessage]:
    """处理已解析的 MQTT payload 字典，便于测试。"""
    started_at = perf_counter()
    if data is None:
        observe_mqtt_message("invalid", perf_counter() - started_at)
        return None
    runtime_state.increment("mqtt_messages_total")
    data = apply_field_aliases(data)
    data = normalize_compensation_measurements(data)

    device_id = resolve_device_id(data, topic)
    if not device_id:
        logger.warning("MQTT payload missing device_id/device_code, skipped")
        observe_mqtt_message("invalid", perf_counter() - started_at)
        return None

    timestamp = parse_timestamp(data)
    payload_hash = MqttReliabilityService.build_payload_hash(data)
    fingerprint = MqttReliabilityService.build_fingerprint(device_id, topic, timestamp, payload_hash)

    try:
        with Session(engine) as session:
            record, should_skip = MqttReliabilityService.claim_message(
                session,
                fingerprint=fingerprint,
                payload_hash=payload_hash,
                raw_payload=raw_payload,
                device_id=device_id,
                topic=topic,
                telemetry_timestamp=timestamp,
            )
            session.commit()
        if should_skip:
            runtime_state.increment("mqtt_duplicates_total")
            logger.info(f"MQTT duplicate skipped: device_id={device_id}, fingerprint={fingerprint[:12]}")
            observe_mqtt_message("duplicate", perf_counter() - started_at)
            return None

        if is_control_receipt_payload(data):
            with Session(engine) as session:
                process_control_receipt(session, data, device_id)
                record = session.exec(
                    select(MqttIngestionRecord).where(MqttIngestionRecord.fingerprint == fingerprint)
                ).first()
                if record:
                    MqttReliabilityService.mark_success(session, record)
                session.commit()
            runtime_state.increment("mqtt_ingestion_success_total")
            observe_mqtt_message("success", perf_counter() - started_at)
            return None

        validate_payload_content(data)
        timestamp = validate_timestamp(timestamp)
        voltage, current, power, energy = normalize_metrics(data)
        data_dict = build_data_dict(data, voltage, current, power, energy)
        ws_data = persist_device_data(device_id, data_dict, timestamp, raw_data=data)
        with Session(engine) as session:
            record = session.exec(
                select(MqttIngestionRecord).where(MqttIngestionRecord.fingerprint == fingerprint)
            ).first()
            if record:
                MqttReliabilityService.mark_success(session, record)
                session.commit()
    except ValueError as exc:
        with Session(engine) as session:
            record = session.exec(
                select(MqttIngestionRecord).where(MqttIngestionRecord.fingerprint == fingerprint)
            ).first()
            if record:
                MqttReliabilityService.mark_failure(session, record, str(exc))
            IngestionHealthService.mark_message_received(session, device_id=device_id)
            IngestionHealthService.mark_ingestion_failure(session, device_id=device_id, reason=str(exc))
            session.commit()
        runtime_state.increment("mqtt_ingestion_failure_total")
        logger.warning(f"MQTT payload validation failed: device_id={device_id}, err={exc}")
        observe_mqtt_message("validation_failed", perf_counter() - started_at)
        return None
    except Exception as exc:
        with Session(engine) as session:
            record = session.exec(
                select(MqttIngestionRecord).where(MqttIngestionRecord.fingerprint == fingerprint)
            ).first()
            if record:
                MqttReliabilityService.mark_failure(session, record, str(exc))
            IngestionHealthService.mark_message_received(session, device_id=device_id)
            IngestionHealthService.mark_ingestion_failure(session, device_id=device_id, reason=str(exc))
            session.commit()
        runtime_state.increment("mqtt_ingestion_failure_total")
        logger.warning(f"MQTT payload persist failed: device_id={device_id}, err={exc}")
        observe_mqtt_message("failed", perf_counter() - started_at)
        return None

    runtime_state.increment("mqtt_ingestion_success_total")
    observe_mqtt_message("success", perf_counter() - started_at)
    return TelemetryBroadcastMessage(
        type="telemetry_update",
        data=ws_data,
    )
