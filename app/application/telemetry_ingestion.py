"""
遥测接入用例
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlmodel import Session

from app.application.device_reporting import report_device_data_ingestion_use_case
from app.services.alarm_service import AlarmService
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_models import TelemetryBroadcastData


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
