"""
设备接入健康接口。

职责：
- 提供设备接入健康状态查询
- 提供 MQTT 接入记录查询与人工重放入口

不负责：
- 系统级健康检查
- MQTT 遥测解析与入库逻辑
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.endpoint_utils import bad_request_from_value_error
from app.api.deps import ADMIN_ONLY, get_current_user
from app.core.access_control import ensure_device_access, get_allowed_device_ids
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.core.response import success_response
from app.integrations.mqtt.processor import parse_payload, process_payload_dict
from app.models.tables import MqttIngestionStatus, User
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_reliability_service import MqttReliabilityService

from .health_serializers import serialize_ingestion_record

router = APIRouter()


@router.get("/{device_id}/ingestion-health")
def get_device_ingestion_health(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    try:
        health = IngestionHealthService.get_device_health(session, device_id)
        return success_response(data=health)
    except ValueError as exc:
        raise bad_request_from_value_error(exc) from exc


@router.get("/ingestion-health/overview")
def list_device_ingestion_health(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    items = IngestionHealthService.list_device_health(session)
    allowed_device_ids = get_allowed_device_ids(session, current_user)
    if allowed_device_ids is not None:
        items = [item for item in items if item["device_id"] in allowed_device_ids]
    return success_response(data={"items": items})


@router.get("/ingestion-records")
def list_mqtt_ingestion_records(
    status: Optional[str] = None,
    retry_ready: bool = False,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    records = (
        MqttReliabilityService.list_retry_ready_records(session, limit=limit)
        if retry_ready
        else MqttReliabilityService.list_records(
            session,
            status=status,
            limit=limit,
            offset=offset,
        )
    )
    return success_response(data={"items": [serialize_ingestion_record(record) for record in records]})


@router.get("/{device_id}/ingestion-records")
def list_device_ingestion_records(
    device_id: int,
    status: Optional[str] = None,
    retry_ready: bool = False,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    records = (
        MqttReliabilityService.list_retry_ready_records(session, limit=limit, device_id=device_id)
        if retry_ready
        else MqttReliabilityService.list_records(
            session,
            status=status,
            device_id=device_id,
            limit=limit,
            offset=offset,
        )
    )
    return success_response(data={"items": [serialize_ingestion_record(record) for record in records]})


@router.post("/ingestion-records/{record_id}/replay")
def replay_mqtt_ingestion_record(
    record_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
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
        current_user.username,
        f"mqtt_ingestion_record:{record_id}",
        status_before=record.status,
        device_id=record.device_id,
        replay_count=record.replay_count,
        retry_count=record.retry_count,
    )
    return success_response(
        data={
            "record_id": record_id,
            "replayed": True,
            "status_before": record.status,
            "replay_count": record.replay_count,
            "retry_count": record.retry_count,
            "broadcast": message.to_dict() if message else None,
        }
    )
