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
from app.models.tables import Device, MqttIngestionRecord, SVGTelemetry


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


def apply_field_aliases(data: dict[str, Any]) -> dict[str, Any]:
    """兼容常见字段别名，保持原字段优先。"""
    normalized = dict(data)
    for alias, canonical in FIELD_ALIASES.items():
        if canonical not in normalized and alias in normalized:
            normalized[canonical] = normalized[alias]
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


def _is_svg_device(device_id: int, session: Session) -> bool:
    """判断设备是否为 svg 类型。"""
    device = session.get(Device, device_id)
    return device is not None and device.device_type == "svg"


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
