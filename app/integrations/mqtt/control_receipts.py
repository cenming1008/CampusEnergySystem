"""按设备类别分发 MQTT 控制回执。"""

from __future__ import annotations

from typing import Any

from sqlmodel import Session

from app.models.tables import Device, DeviceControlLog


def process_device_control_receipt(
    session: Session,
    data: dict[str, Any],
    device_id: int,
) -> DeviceControlLog:
    device = session.get(Device, device_id)
    if device is None:
        raise ValueError(f"控制回执找不到设备：device_id={device_id}")

    command_id = data.get("command_id")
    detail = data.get("detail") or data.get("reason") or data.get("message")
    if str(device.device_category) == "storage":
        from app.services.devices.storage.control_command_service import (
            StorageControlCommandService,
        )

        return StorageControlCommandService.apply_control_receipt(
            session,
            device_id=device_id,
            command_id=command_id,
            result=StorageControlCommandService.normalize_control_result(data.get("result")),
            detail=detail,
            control_event_notifier=StorageControlCommandService.publish_control_log_update_event,
        )

    from app.services.devices.compensation.capacitor_bank.control_command_service import (
        CapacitorBankControlCommandService,
    )

    return CapacitorBankControlCommandService.apply_control_receipt(
        session,
        device_id=device_id,
        command_id=command_id,
        result=CapacitorBankControlCommandService.normalize_control_result(data.get("result")),
        detail=detail,
        control_event_notifier=CapacitorBankControlCommandService.publish_control_log_update_event,
    )
