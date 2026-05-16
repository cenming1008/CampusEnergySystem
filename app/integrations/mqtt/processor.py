"""
MQTT 消息处理

负责解析 payload、标准化指标、落库与报警检查，并构造 WebSocket 广播消息。
"""

from __future__ import annotations

import json
import hashlib
from time import perf_counter
from datetime import datetime
from typing import Any, Optional

from sqlmodel import Session, select

from app.application.telemetry_ingestion import ingest_telemetry_use_case
from app.core.database import engine
from app.core.logger import logger
from app.core.metrics import observe_mqtt_message
from app.core.runtime_state import runtime_state
from app.integrations.mqtt.compensation import (
    extract_capacitor_bank_control_profile,
    extract_capacitor_bank_telemetry,
    extract_svg_telemetry,
    is_control_receipt_payload,
    normalize_compensation_measurements,
    process_control_receipt,
)
from app.integrations.mqtt.device_extensions import persist_device_extensions
from app.integrations.mqtt.payloads import (
    FIELD_ALIASES,
    MEANINGFUL_FIELDS,
    apply_field_aliases,
    build_data_dict,
    normalize_metrics,
    parse_numeric,
    parse_timestamp,
    validate_payload_content,
    validate_timestamp,
)
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_device_resolver import resolve_device_id
from app.services.mqtt_models import TelemetryBroadcastData, TelemetryBroadcastMessage
from app.services.mqtt_reliability_service import MqttReliabilityService
from app.models.tables import Device, MqttIngestionRecord
# CapacitorBankService imported lazily inside functions to avoid circular import
# (services.__init__ → capacitor_bank_service → integrations.__init__ → mqtt/processor)

PENDING_ARCHIVE_INGESTION_REASON = "设备档案待完善，已跳过业务入库"


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


def persist_device_data(
    device_id: int,
    data_dict: dict[str, Any],
    timestamp: datetime,
    raw_data: Optional[dict[str, Any]] = None,
) -> TelemetryBroadcastData:
    """执行遥测接入用例并生成 WebSocket 广播数据。"""
    with Session(engine) as session:
        result = ingest_telemetry_use_case(
            session=session,
            device_id=device_id,
            data=data_dict,
            timestamp=timestamp,
        )
        persist_device_extensions(session, device_id, timestamp, raw_data)

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
            if should_skip:
                session.commit()
            else:
                device = session.get(Device, device_id)
                if getattr(device, "archive_status", "complete") == "pending":
                    MqttReliabilityService.mark_failure(session, record, PENDING_ARCHIVE_INGESTION_REASON)
                    IngestionHealthService.mark_message_received(session, device_id=device_id)
                    IngestionHealthService.mark_ingestion_failure(
                        session,
                        device_id=device_id,
                        reason=PENDING_ARCHIVE_INGESTION_REASON,
                    )
                    session.commit()
                    runtime_state.increment("mqtt_ingestion_failure_total")
                    observe_mqtt_message("pending_archive", perf_counter() - started_at)
                    logger.warning(
                        "MQTT payload skipped for pending device archive: device_id=%s topic=%s",
                        device_id,
                        topic,
                    )
                    return None
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
