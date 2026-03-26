"""
MQTT 接入可靠性服务。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlmodel import Session, select

from app.core.settings import settings
from app.models.tables import MqttIngestionRecord, MqttIngestionStatus


class MqttReliabilityService:
    """维护 MQTT 消息幂等台账和失败留痕。"""

    @staticmethod
    def build_payload_hash(data: dict[str, Any]) -> str:
        serialized = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def build_fingerprint(
        device_id: int,
        topic: Optional[str],
        telemetry_timestamp: datetime,
        payload_hash: str,
    ) -> str:
        raw = f"{device_id}|{topic or ''}|{telemetry_timestamp.isoformat()}|{payload_hash}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def claim_message(
        session: Session,
        *,
        fingerprint: str,
        payload_hash: str,
        raw_payload: Optional[str],
        device_id: int,
        topic: Optional[str],
        telemetry_timestamp: datetime,
    ) -> tuple[MqttIngestionRecord, bool]:
        """声明一条消息。

        返回 `(record, should_skip)`。
        """
        statement = select(MqttIngestionRecord).where(MqttIngestionRecord.fingerprint == fingerprint)
        record = session.exec(statement).first()
        now = datetime.now()

        if record is None:
            record = MqttIngestionRecord(
                fingerprint=fingerprint,
                payload_hash=payload_hash,
                raw_payload=raw_payload,
                device_id=device_id,
                topic=topic,
                telemetry_timestamp=telemetry_timestamp,
                received_at=now,
                last_seen_at=now,
                status=MqttIngestionStatus.PROCESSING,
            )
            session.add(record)
            session.flush()
            return record, False

        record.last_seen_at = now
        record.duplicate_count += 1
        if raw_payload and not record.raw_payload:
            record.raw_payload = raw_payload

        if record.status in (MqttIngestionStatus.SUCCESS, MqttIngestionStatus.DUPLICATE, MqttIngestionStatus.PROCESSING):
            session.add(record)
            session.flush()
            return record, True

        record.status = MqttIngestionStatus.PROCESSING
        record.error_reason = None
        session.add(record)
        session.flush()
        return record, False

    @staticmethod
    def mark_success(session: Session, record: MqttIngestionRecord) -> MqttIngestionRecord:
        record.status = MqttIngestionStatus.SUCCESS
        record.error_reason = None
        record.last_seen_at = datetime.now()
        session.add(record)
        session.flush()
        return record

    @staticmethod
    def mark_failure(session: Session, record: MqttIngestionRecord, reason: str) -> MqttIngestionRecord:
        record.retry_count += 1
        max_attempts = max(1, int(settings.mqtt_retry_max_attempts))
        if record.retry_count >= max_attempts:
            record.status = MqttIngestionStatus.DEAD_LETTER
            record.next_retry_at = None
        else:
            record.status = MqttIngestionStatus.FAILED
            backoff_seconds = max(1, int(settings.mqtt_retry_backoff_seconds))
            record.next_retry_at = datetime.now() + timedelta(seconds=backoff_seconds * record.retry_count)
        record.error_reason = reason
        record.last_seen_at = datetime.now()
        session.add(record)
        session.flush()
        return record

    @staticmethod
    def list_records(
        session: Session,
        *,
        status: Optional[str] = None,
        device_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MqttIngestionRecord]:
        statement = select(MqttIngestionRecord)
        if status:
            statement = statement.where(MqttIngestionRecord.status == status)
        if device_id is not None:
            statement = statement.where(MqttIngestionRecord.device_id == device_id)
        statement = (
            statement
            .order_by(MqttIngestionRecord.received_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.exec(statement).all())

    @staticmethod
    def list_retry_ready_records(
        session: Session,
        *,
        limit: int = 100,
        device_id: Optional[int] = None,
    ) -> list[MqttIngestionRecord]:
        now = datetime.now()
        statement = select(MqttIngestionRecord).where(
            MqttIngestionRecord.status.in_((MqttIngestionStatus.FAILED, MqttIngestionStatus.DEAD_LETTER))
        )
        statement = statement.where(
            (MqttIngestionRecord.next_retry_at == None) | (MqttIngestionRecord.next_retry_at <= now)  # noqa: E711
        )
        if device_id is not None:
            statement = statement.where(MqttIngestionRecord.device_id == device_id)
        statement = statement.order_by(MqttIngestionRecord.last_seen_at.asc()).limit(limit)
        return list(session.exec(statement).all())

    @staticmethod
    def get_record_by_id(session: Session, record_id: int) -> Optional[MqttIngestionRecord]:
        return session.get(MqttIngestionRecord, record_id)

    @staticmethod
    def mark_replayed(session: Session, record: MqttIngestionRecord) -> MqttIngestionRecord:
        record.replay_count += 1
        record.retry_count += 1
        record.last_replayed_at = datetime.now()
        record.next_retry_at = None
        session.add(record)
        session.flush()
        return record
