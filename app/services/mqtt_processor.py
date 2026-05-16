"""
兼容层：MQTT 处理

保留旧导入路径，便于测试和外部调用继续使用 app.services.mqtt_processor。
"""

from __future__ import annotations

from typing import Optional

from app.integrations.mqtt import processor as _canonical_processor
from app.integrations.mqtt.processor import (
    FIELD_ALIASES,
    IngestionHealthService,
    MEANINGFUL_FIELDS,
    TelemetryBroadcastMessage,
    apply_field_aliases,
    build_data_dict,
    hash_payload_string,
    is_control_receipt_payload,
    normalize_metrics,
    parse_numeric,
    parse_payload,
    parse_timestamp,
    persist_device_data,
    process_control_receipt,
    resolve_device_id,
    validate_payload_content,
    validate_timestamp,
)


def process_payload(payload_str: str, topic: Optional[str] = None) -> Optional[dict[str, object]]:
    """兼容旧入口，返回可供 WebSocket 广播的字典。"""
    return _canonical_processor.process_payload(payload_str, topic=topic)


def process_payload_dict(
    data: dict[str, object],
    topic: Optional[str] = None,
) -> Optional[TelemetryBroadcastMessage]:
    """兼容旧入口，委托 integrations.mqtt.processor 的主实现。"""
    return _canonical_processor.process_payload_dict(data, topic=topic)


__all__ = [
    "FIELD_ALIASES",
    "IngestionHealthService",
    "MEANINGFUL_FIELDS",
    "apply_field_aliases",
    "build_data_dict",
    "hash_payload_string",
    "is_control_receipt_payload",
    "normalize_metrics",
    "parse_numeric",
    "parse_payload",
    "parse_timestamp",
    "persist_device_data",
    "process_control_receipt",
    "process_payload",
    "process_payload_dict",
    "resolve_device_id",
    "validate_payload_content",
    "validate_timestamp",
]
