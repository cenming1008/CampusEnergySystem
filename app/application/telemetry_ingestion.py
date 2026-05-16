"""
遥测接入用例
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlmodel import Session

from app.application.device_reporting import report_device_data_ingestion_use_case
from app.core.audit import audit_log
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.models.tables import MqttIngestionStatus
from app.services.alarm_service import AlarmService
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_models import TelemetryBroadcastData
from app.services.mqtt_reliability_service import MqttReliabilityService


@dataclass(frozen=True)
class TelemetryIngestionResult:
    """遥测接入结果。"""

    broadcast_data: TelemetryBroadcastData


def ingest_telemetry_use_case(
    session: Session,
    device_id: int,
    data: dict[str, Any],
    timestamp: datetime,
) -> TelemetryIngestionResult:
    """处理单条设备遥测的落库、告警和健康状态更新。"""
    # 在线健康应表达服务端最近接收/成功处理时间；设备 timestamp 仍用于遥测时序落库。
    IngestionHealthService.mark_message_received(session, device_id=device_id)

    record = report_device_data_ingestion_use_case(
        session=session,
        device_id=device_id,
        data=data,
        timestamp=timestamp,
    )

    AlarmService.check_and_create_alarm(
        session=session,
        device_id=device_id,
        data=data,
        timestamp=timestamp,
    )
    IngestionHealthService.mark_ingestion_success(session, device_id=device_id)

    return TelemetryIngestionResult(
        broadcast_data=TelemetryBroadcastData(
            device_id=device_id,
            voltage=record.voltage,
            current=record.current,
            power=record.flow_rate,
            energy=record.consumption,
            timestamp=record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        )
    )


def replay_mqtt_ingestion_record_use_case(
    session: Session,
    record_id: int,
    operator_username: str,
) -> dict[str, Any]:
    """人工重放一条失败/死信状态的 MQTT 接入记录。"""
    from app.integrations.mqtt.processor import parse_payload, process_payload_dict

    record = MqttReliabilityService.get_record_by_id(session, record_id)
    if not record:
        raise ResourceNotFoundException("MQTT接入记录", record_id)
    if record.status not in (MqttIngestionStatus.FAILED, MqttIngestionStatus.DEAD_LETTER):
        raise ValidationException("仅失败或死信状态的消息允许人工重放")
    if not record.raw_payload:
        raise ValidationException("该消息未保存原始 payload，无法重放")

    payload = parse_payload(record.raw_payload)
    if payload is None:
        raise ValidationException("原始 payload 已损坏，无法重放")

    message = process_payload_dict(payload, topic=record.topic, raw_payload=record.raw_payload)
    MqttReliabilityService.mark_replayed(session, record)
    session.commit()
    audit_log(
        "mqtt.replay_record",
        operator_username,
        f"mqtt_ingestion_record:{record_id}",
        status_before=record.status,
        device_id=record.device_id,
        replay_count=record.replay_count,
        retry_count=record.retry_count,
    )
    return {
        "record_id": record_id,
        "replayed": True,
        "status_before": record.status,
        "replay_count": record.replay_count,
        "retry_count": record.retry_count,
        "broadcast": message.to_dict() if message else None,
    }
