"""
设备接入健康 serializer。

仅负责将 MQTT 接入记录转换为 API 响应字典。
"""

from __future__ import annotations


from typing import Any


def serialize_ingestion_record(record: Any) -> dict:
    """序列化单条 MQTT 接入记录。"""

    return {
        "id": record.id,
        "device_id": record.device_id,
        "topic": record.topic,
        "status": record.status,
        "error_reason": record.error_reason,
        "duplicate_count": record.duplicate_count,
        "retry_count": record.retry_count,
        "next_retry_at": record.next_retry_at.isoformat() if record.next_retry_at else None,
        "replay_count": record.replay_count,
        "received_at": record.received_at.isoformat(),
        "last_seen_at": record.last_seen_at.isoformat(),
        "last_replayed_at": record.last_replayed_at.isoformat() if record.last_replayed_at else None,
        "telemetry_timestamp": record.telemetry_timestamp.isoformat() if record.telemetry_timestamp else None,
    }


__all__ = ["serialize_ingestion_record"]
