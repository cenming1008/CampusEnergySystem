"""
兼容层：MQTT 处理

保留旧导入路径，便于测试和外部调用继续使用 app.services.mqtt_processor。
"""

from __future__ import annotations

from typing import Optional

from app.integrations.mqtt.processor import (
    IngestionHealthService,
    TelemetryBroadcastMessage,
    apply_field_aliases,
    build_data_dict,
    normalize_metrics,
    parse_numeric,
    parse_payload,
    parse_timestamp,
    persist_device_data,
    resolve_device_id,
    validate_payload_content,
    validate_timestamp,
)


def process_payload(payload_str: str, topic: Optional[str] = None) -> Optional[dict[str, object]]:
    """兼容旧入口，返回可供 WebSocket 广播的字典。"""
    data = parse_payload(payload_str)
    if data is None:
        return None

    message = process_payload_dict(data, topic=topic)
    return message.to_dict() if message else None


def process_payload_dict(
    data: dict[str, object],
    topic: Optional[str] = None,
) -> Optional[TelemetryBroadcastMessage]:
    """兼容旧入口，保留本模块命名空间，支持 patch。"""
    from app.integrations.mqtt.processor import (
        Session,
        TelemetryBroadcastMessage as _TelemetryBroadcastMessage,
        engine,
        logger,
    )

    if data is None:
        return None

    normalized_data = apply_field_aliases(data)
    device_id = resolve_device_id(normalized_data, topic)
    if not device_id:
        logger.warning("MQTT payload missing device_id/device_code, skipped")
        return None

    try:
        validate_payload_content(normalized_data)
        timestamp = validate_timestamp(parse_timestamp(normalized_data))
        voltage, current, power, energy = normalize_metrics(normalized_data)
        data_dict = build_data_dict(normalized_data, voltage, current, power, energy)
        ws_data = persist_device_data(device_id, data_dict, timestamp)
    except ValueError as exc:
        with Session(engine) as session:
            IngestionHealthService.mark_message_received(session, device_id=device_id)
            IngestionHealthService.mark_ingestion_failure(session, device_id=device_id, reason=str(exc))
            session.commit()
        logger.warning(f"MQTT payload validation failed: device_id={device_id}, err={exc}")
        return None
    except Exception as exc:
        with Session(engine) as session:
            IngestionHealthService.mark_message_received(session, device_id=device_id)
            IngestionHealthService.mark_ingestion_failure(session, device_id=device_id, reason=str(exc))
            session.commit()
        logger.warning(f"MQTT payload persist failed: device_id={device_id}, err={exc}")
        return None

    return _TelemetryBroadcastMessage(
        type="telemetry_update",
        data=ws_data,
    )


__all__ = [
    "IngestionHealthService",
    "apply_field_aliases",
    "build_data_dict",
    "normalize_metrics",
    "parse_numeric",
    "parse_payload",
    "parse_timestamp",
    "persist_device_data",
    "process_payload",
    "process_payload_dict",
    "resolve_device_id",
    "validate_payload_content",
    "validate_timestamp",
]
