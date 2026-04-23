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
from app.integrations.mqtt.compensation import (
    apply_compensation_field_aliases,
    extract_capacitor_bank_control_profile,
    extract_capacitor_bank_telemetry,
    extract_svg_telemetry,
    is_control_receipt_payload,
    normalize_compensation_measurements,
    process_control_receipt,
)
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_device_resolver import resolve_device_id
from app.services.mqtt_models import TelemetryBroadcastData, TelemetryBroadcastMessage
from app.services.mqtt_reliability_service import MqttReliabilityService
from app.domain.device_payloads import resolve_compensation_subtype
from app.models.tables import CapacitorBankTelemetry, Device, MqttIngestionRecord, SVGTelemetry
# CapacitorBankService imported lazily inside functions to avoid circular import
# (services.__init__ → capacitor_bank_service → integrations.__init__ → mqtt/processor)


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
    return apply_compensation_field_aliases(normalized)


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
            cap_profile_fields = extract_capacitor_bank_control_profile(raw_data)
            if cap_fields:
                from app.services.alarm_service import AlarmService
                with session.no_autoflush:
                    cap_telemetry = session.exec(
                        select(CapacitorBankTelemetry)
                        .where(CapacitorBankTelemetry.device_id == device_id)
                        .where(CapacitorBankTelemetry.timestamp == timestamp)
                    ).first()
                    if cap_telemetry is None:
                        cap_telemetry = CapacitorBankTelemetry(
                            device_id=device_id,
                            timestamp=timestamp,
                            **cap_fields,
                        )
                        session.add(cap_telemetry)
                    else:
                        for field, value in cap_fields.items():
                            setattr(cap_telemetry, field, value)
                AlarmService.check_capacitor_bank_faults(
                    session,
                    device_id,
                    cap_fields,
                    timestamp,
                    profile_data=cap_profile_fields,
                )
            if cap_profile_fields:
                from app.services.devices.compensation.capacitor_bank.control_profile_service import CapacitorBankControlProfileService  # lazy import
                CapacitorBankControlProfileService.upsert_control_profile(
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
