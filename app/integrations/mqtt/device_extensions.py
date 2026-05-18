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
    extract_capacitor_bank_alarm_fields,
    extract_capacitor_bank_control_profile,
    extract_capacitor_bank_telemetry,
    extract_svg_telemetry,
)
from app.models.storage import StorageTelemetry
from app.models.tables import CapacitorBankTelemetry, Device, SVGTelemetry


_STORAGE_NUMERIC_FIELDS = (
    "soc",
    "soh",
    "active_power",
    "reactive_power",
    "dc_voltage",
    "dc_current",
    "ac_voltage_a",
    "ac_voltage_b",
    "ac_voltage_c",
    "ac_current_a",
    "ac_current_b",
    "ac_current_c",
    "frequency",
    "cell_temp_max",
    "cell_temp_min",
    "cell_temp_avg",
    "charge_energy_today",
    "discharge_energy_today",
    "charge_energy_total",
    "discharge_energy_total",
)
_STORAGE_TEXT_FIELDS = ("run_state", "control_mode")
_STORAGE_INT_FIELDS = ("fault_code", "alarm_code", "cycle_count")


def _compensation_subtype(device_id: int, session: Session) -> Optional[str]:
    device = session.get(Device, device_id)
    if device is None:
        return None
    return resolve_compensation_subtype(
        getattr(device, "device_type", None),
        getattr(device, "device_subtype", None),
    )


def _device_category(device_id: int, session: Session) -> Optional[str]:
    device = session.get(Device, device_id)
    return getattr(device, "device_category", None) if device else None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_storage_telemetry(raw_data: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for field in _STORAGE_NUMERIC_FIELDS:
        value = raw_data.get(field)
        if field == "active_power" and value is None:
            value = raw_data.get("power")
        parsed = _to_float(value)
        if parsed is not None:
            fields[field] = parsed
    for field in _STORAGE_TEXT_FIELDS:
        value = raw_data.get(field)
        if value is not None:
            fields[field] = str(value)
    for field in _STORAGE_INT_FIELDS:
        parsed = _to_int(raw_data.get(field))
        if parsed is not None:
            fields[field] = parsed
    return fields


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
    cap_alarm_fields = extract_capacitor_bank_alarm_fields(raw_data)
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
        alarm_fields = {**cap_fields, **cap_alarm_fields}
        AlarmService.check_capacitor_bank_faults(
            session,
            device_id,
            alarm_fields,
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
    elif cap_alarm_fields:
        from app.services.alarm_service import AlarmService

        AlarmService.check_capacitor_bank_faults(
            session,
            device_id,
            cap_alarm_fields,
            timestamp,
            profile_data=cap_profile_fields,
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


def _persist_storage_extension(
    session: Session,
    device_id: int,
    timestamp: datetime,
    raw_data: dict[str, Any],
) -> None:
    storage_fields = _extract_storage_telemetry(raw_data)
    if not storage_fields:
        return

    from app.services.alarm_service import AlarmService

    with session.no_autoflush:
        telemetry = session.exec(
            select(StorageTelemetry)
            .where(StorageTelemetry.device_id == device_id)
            .where(StorageTelemetry.timestamp == timestamp)
        ).first()
        if telemetry is None:
            telemetry = StorageTelemetry(
                device_id=device_id,
                timestamp=timestamp,
                **storage_fields,
            )
            session.add(telemetry)
        else:
            for field, value in storage_fields.items():
                setattr(telemetry, field, value)
    AlarmService.check_storage_faults(session, device_id, storage_fields, timestamp)


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
    elif _device_category(device_id, session) == "storage":
        _persist_storage_extension(session, device_id, timestamp, raw_data)


__all__ = ["persist_device_extensions"]
