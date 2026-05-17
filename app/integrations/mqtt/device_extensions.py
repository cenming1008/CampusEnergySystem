"""
MQTT 设备专属遥测扩展落库。

通用 MQTT processor 只负责接入主流程；SVG、电容补偿控制器等专属遥测
在这里按设备身份追加写入，避免主入口继续堆积设备族细节。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlmodel import Session, select

from app.domain.device_payloads import resolve_compensation_subtype
from app.integrations.mqtt.compensation import (
    extract_capacitor_bank_control_profile,
    extract_capacitor_bank_telemetry,
    extract_svg_telemetry,
)
from app.models.tables import CapacitorBankTelemetry, Device, SVGTelemetry


def _compensation_subtype(device_id: int, session: Session) -> Optional[str]:
    device = session.get(Device, device_id)
    if device is None:
        return None
    return resolve_compensation_subtype(
        getattr(device, "device_type", None),
        getattr(device, "device_subtype", None),
    )


def _persist_svg_extension(
    session: Session,
    device_id: int,
    timestamp: datetime,
    raw_data: dict[str, Any],
) -> None:
    svg_fields = extract_svg_telemetry(raw_data)
    if not svg_fields:
        return

    from app.services.alarm_service import AlarmService

    telemetry = SVGTelemetry(
        device_id=device_id,
        timestamp=timestamp,
        **svg_fields,
    )
    session.add(telemetry)
    AlarmService.check_svg_faults(session, device_id, svg_fields, timestamp)


def _persist_capacitor_bank_extension(
    session: Session,
    device_id: int,
    timestamp: datetime,
    raw_data: dict[str, Any],
) -> None:
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
        from app.services.devices.compensation.capacitor_bank.control_command_service import (
            CapacitorBankControlCommandService,
        )

        CapacitorBankControlCommandService.reconcile_failed_manual_switch_with_telemetry(
            session,
            device_id=device_id,
            telemetry=cap_telemetry,
            control_event_notifier=CapacitorBankControlCommandService.publish_control_log_update_event,
        )

    if cap_profile_fields:
        from app.services.devices.compensation.capacitor_bank.control_profile_service import (
            CapacitorBankControlProfileService,
        )

        CapacitorBankControlProfileService.upsert_control_profile(
            session,
            device_id,
            cap_profile_fields,
            snapshot_timestamp=timestamp,
            source="telemetry",
        )


def persist_device_extensions(
    session: Session,
    device_id: int,
    timestamp: datetime,
    raw_data: Optional[dict[str, Any]],
) -> None:
    """按设备身份追加专属遥测、专属告警和参数快照。"""
    if raw_data is None:
        return

    subtype = _compensation_subtype(device_id, session)
    if subtype == "svg":
        _persist_svg_extension(session, device_id, timestamp, raw_data)
    elif subtype == "capacitor_bank_controller":
        _persist_capacitor_bank_extension(session, device_id, timestamp, raw_data)


__all__ = ["persist_device_extensions"]
