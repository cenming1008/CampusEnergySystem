"""
设备管理主流程 use case。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlmodel import Session

from app.core.access_control import ensure_device_access
from app.core.audit import audit_log
from app.domain.device_payloads import resolve_compensation_subtype
from app.models.tables import Device, User
from app.services.device_service import DeviceService
from app.services.mqtt_publisher import publish_control_command_async
from app.services.svg_service import SVGService


@dataclass(frozen=True)
class DeviceManagementActionResult:
    message: str


def _normalize_toggle_reason(active: bool, reason: Optional[str]) -> str:
    normalized = reason.strip() if reason else ""
    if normalized:
        return normalized
    return "API启用设备" if active else "API停用设备"


def create_device_smart_use_case(
    session: Session,
    current_user: User,
    name: str,
    sn: str,
    device_type: str,
    device_subtype: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    rated_capacity: Optional[float] = None,
    svg_operations: Optional[dict] = None,
) -> Device:
    device = DeviceService.create_device_smart(
        session=session,
        name=name,
        sn=sn,
        device_type=device_type,
        device_subtype=device_subtype,
        location=location,
        description=description,
        rated_capacity=rated_capacity,
    )
    if resolve_compensation_subtype(
        getattr(device, "device_type", None),
        getattr(device, "device_subtype", None),
    ) == "svg" and svg_operations:
        SVGService.upsert_operations_profile(session, device.id, svg_operations)
    audit_log("device.create", current_user.username, f"device:{device.id}", role=current_user.role)
    return device


def create_device_legacy_use_case(
    session: Session,
    current_user: User,
    device: Device,
) -> Device:
    created = DeviceService.create_device(session, device)
    audit_log("device.create_legacy", current_user.username, f"device:{created.id}", role=current_user.role)
    return created


def update_device_profile_use_case(
    session: Session,
    current_user: User,
    device_id: int,
    device_type: Optional[str] = None,
    device_subtype: Optional[str] = None,
    name: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    rated_capacity: Optional[float] = None,
    svg_operations: Optional[dict] = None,
) -> Device:
    ensure_device_access(session, current_user, device_id)
    updated = DeviceService.update_device(
        session,
        device_id,
        device_type=device_type,
        device_subtype=device_subtype,
        name=name,
        location=location,
        description=description,
        rated_capacity=rated_capacity,
    )
    if resolve_compensation_subtype(
        getattr(updated, "device_type", None),
        getattr(updated, "device_subtype", None),
    ) == "svg" and svg_operations:
        SVGService.upsert_operations_profile(session, updated.id, svg_operations)
    audit_log("device.update", current_user.username, f"device:{device_id}", role=current_user.role)
    return updated


def delete_device_use_case(
    session: Session,
    current_user: User,
    device_id: int,
) -> DeviceManagementActionResult:
    device = ensure_device_access(session, current_user, device_id)
    DeviceService.delete_device(session, device_id)
    audit_log("device.delete", current_user.username, f"device:{device_id}", role=current_user.role)
    return DeviceManagementActionResult(message=f"设备 {device.name} 已删除")


def toggle_device_status_use_case(
    session: Session,
    current_user: User,
    device_id: int,
    active: bool,
    reason: Optional[str] = None,
) -> Device:
    ensure_device_access(session, current_user, device_id)
    normalized_reason = _normalize_toggle_reason(active, reason)
    command_action = "start" if active else "stop"
    device = DeviceService.toggle_device_status(
        session,
        device_id,
        active,
        operator=current_user.username,
        reason=normalized_reason,
        command_source="api",
    )
    publish_control_command_async(device.id, command_action)
    audit_log(
        "device.toggle",
        current_user.username,
        f"device:{device.id}",
        active=active,
        reason=normalized_reason,
        command_action=command_action,
        role=current_user.role,
    )
    return device
