"""
设备接入健康度服务
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlmodel import Session, select

from app.core.settings import settings
from app.models.tables import Device, DeviceIngestionHealth


class IngestionHealthService:
    """维护设备接入健康状态。"""

    @staticmethod
    def _get_or_create(session: Session, device_id: int) -> DeviceIngestionHealth:
        status = session.get(DeviceIngestionHealth, device_id)
        if status:
            return status

        device = session.get(Device, device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")

        status = DeviceIngestionHealth(device_id=device_id)
        session.add(status)
        session.flush()
        return status

    @staticmethod
    def mark_message_received(
        session: Session,
        device_id: int,
        timestamp: Optional[datetime] = None,
    ) -> DeviceIngestionHealth:
        status = IngestionHealthService._get_or_create(session, device_id)
        status.last_message_at = timestamp or datetime.now()
        status.total_messages += 1
        status.updated_at = datetime.now()
        session.add(status)
        return status

    @staticmethod
    def mark_ingestion_success(
        session: Session,
        device_id: int,
        timestamp: Optional[datetime] = None,
    ) -> DeviceIngestionHealth:
        status = IngestionHealthService._get_or_create(session, device_id)
        status.last_message_at = timestamp or datetime.now()
        status.last_success_at = timestamp or datetime.now()
        status.consecutive_failures = 0
        status.last_failure_reason = None
        status.updated_at = datetime.now()
        session.add(status)
        return status

    @staticmethod
    def mark_ingestion_failure(
        session: Session,
        device_id: int,
        reason: str,
        timestamp: Optional[datetime] = None,
    ) -> DeviceIngestionHealth:
        status = IngestionHealthService._get_or_create(session, device_id)
        status.last_message_at = timestamp or datetime.now()
        status.last_failure_at = timestamp or datetime.now()
        status.last_failure_reason = reason
        status.consecutive_failures += 1
        status.total_failures += 1
        status.updated_at = datetime.now()
        session.add(status)
        return status

    @staticmethod
    def get_device_health(session: Session, device_id: int) -> Dict[str, Any]:
        device = session.get(Device, device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")

        status = session.get(DeviceIngestionHealth, device_id)
        if not status:
            return {
                "device_id": device_id,
                "is_online": False,
                "status": "unknown",
                "last_message_at": None,
                "last_success_at": None,
                "last_failure_at": None,
                "last_failure_reason": None,
                "consecutive_failures": 0,
                "total_messages": 0,
                "total_failures": 0,
            }

        return IngestionHealthService.serialize_status(status)

    @staticmethod
    def list_device_health(session: Session) -> list[Dict[str, Any]]:
        statuses = list(session.exec(select(DeviceIngestionHealth).order_by(DeviceIngestionHealth.device_id)).all())
        return [IngestionHealthService.serialize_status(status) for status in statuses]

    @staticmethod
    def serialize_status(status: DeviceIngestionHealth) -> Dict[str, Any]:
        online_window_seconds = max(30, int(getattr(settings, "mqtt_online_timeout_seconds", 300)))
        now = datetime.now()
        is_online = bool(
            status.last_success_at and status.last_success_at >= now - timedelta(seconds=online_window_seconds)
        )

        if status.last_success_at is None and status.total_messages == 0:
            state = "unknown"
        elif is_online and status.consecutive_failures == 0:
            state = "online"
        elif is_online:
            state = "degraded"
        else:
            state = "offline"

        success_rate = None
        if status.total_messages > 0:
            success_rate = round(
                ((status.total_messages - status.total_failures) / status.total_messages) * 100,
                2,
            )

        return {
            "device_id": status.device_id,
            "is_online": is_online,
            "status": state,
            "last_message_at": status.last_message_at,
            "last_success_at": status.last_success_at,
            "last_failure_at": status.last_failure_at,
            "last_failure_reason": status.last_failure_reason,
            "consecutive_failures": status.consecutive_failures,
            "total_messages": status.total_messages,
            "total_failures": status.total_failures,
            "success_rate": success_rate,
            "updated_at": status.updated_at,
        }
