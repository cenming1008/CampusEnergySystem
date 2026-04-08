"""
维护主流程 use case。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlmodel import Session

from app.core.access_control import ensure_device_access, get_allowed_device_ids
from app.core.audit import audit_log
from app.models.tables import DeviceMaintenance, MaintenanceStatus, MaintenanceType, User
from app.services.maintenance_service import MaintenanceService


@dataclass(frozen=True)
class MaintenanceActionResult:
    message: str


def _get_accessible_maintenance(session: Session, current_user: User, maintenance_id: int) -> DeviceMaintenance:
    maintenance = MaintenanceService.get_maintenance_by_id(session, maintenance_id)
    ensure_device_access(session, current_user, maintenance.device_id)
    return maintenance


def list_maintenance_records_use_case(
    session: Session,
    current_user: User,
    device_id: Optional[int] = None,
    maintenance_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
):
    return MaintenanceService.get_maintenance_list(
        session=session,
        device_id=device_id,
        maintenance_type=maintenance_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
        limit=limit,
        offset=offset,
    )


def list_maintenance_type_options_use_case():
    type_meta = {
        MaintenanceType.ROUTINE: ("日常维护", "定期的日常保养和检查"),
        MaintenanceType.REPAIR: ("故障维修", "设备故障后的修理"),
        MaintenanceType.INSPECTION: ("定期巡检", "按计划进行的设备巡检"),
        MaintenanceType.UPGRADE: ("设备升级", "设备软硬件升级改造"),
        MaintenanceType.CALIBRATION: ("校准调试", "设备精度校准和参数调试"),
    }
    return [
        {"value": item.value, "label": type_meta[item][0], "description": type_meta[item][1]}
        for item in MaintenanceType
    ]


def list_maintenance_status_options_use_case():
    status_meta = {
        MaintenanceStatus.SCHEDULED: ("已计划", "维护已安排，等待执行"),
        MaintenanceStatus.IN_PROGRESS: ("进行中", "维护正在进行"),
        MaintenanceStatus.COMPLETED: ("已完成", "维护已完成"),
        MaintenanceStatus.CANCELLED: ("已取消", "维护已取消"),
    }
    return [
        {"value": item.value, "label": status_meta[item][0], "description": status_meta[item][1]}
        for item in MaintenanceStatus
    ]


def get_maintenance_detail_use_case(
    session: Session,
    current_user: User,
    maintenance_id: int,
):
    return _get_accessible_maintenance(session, current_user, maintenance_id)


def create_maintenance_record_use_case(
    session: Session,
    current_user: User,
    device_id: int,
    maintenance_type: str,
    scheduled_time: datetime,
    title: str,
    description: Optional[str] = None,
    operator: Optional[str] = None,
    created_by: Optional[str] = None,
):
    ensure_device_access(session, current_user, device_id)
    maintenance = MaintenanceService.create_maintenance(
        session=session,
        device_id=device_id,
        maintenance_type=maintenance_type,
        scheduled_time=scheduled_time,
        title=title,
        description=description,
        operator=operator,
        created_by=created_by or current_user.username,
    )
    audit_log(
        "maintenance.create",
        current_user.username,
        f"device:{device_id}",
        maintenance_type=maintenance_type,
        role=current_user.role,
    )
    return maintenance


def update_maintenance_record_use_case(
    session: Session,
    current_user: User,
    maintenance_id: int,
    update_data: dict,
):
    _get_accessible_maintenance(session, current_user, maintenance_id)
    result = MaintenanceService.update_maintenance(session, maintenance_id, **update_data)
    audit_log("maintenance.update", current_user.username, f"maintenance:{maintenance_id}", role=current_user.role)
    return result


def start_maintenance_use_case(
    session: Session,
    current_user: User,
    maintenance_id: int,
    operator: Optional[str] = None,
):
    _get_accessible_maintenance(session, current_user, maintenance_id)
    result = MaintenanceService.start_maintenance(
        session,
        maintenance_id,
        operator or current_user.username,
    )
    audit_log("maintenance.start", current_user.username, f"maintenance:{maintenance_id}", role=current_user.role)
    return result


def complete_maintenance_use_case(
    session: Session,
    current_user: User,
    maintenance_id: int,
    result: Optional[str] = None,
    cost: Optional[float] = None,
    parts_replaced: Optional[str] = None,
    next_maintenance_date: Optional[datetime] = None,
):
    _get_accessible_maintenance(session, current_user, maintenance_id)
    maintenance = MaintenanceService.complete_maintenance(
        session=session,
        maintenance_id=maintenance_id,
        result=result,
        cost=cost,
        parts_replaced=parts_replaced,
        next_maintenance_date=next_maintenance_date,
    )
    audit_log("maintenance.complete", current_user.username, f"maintenance:{maintenance_id}", role=current_user.role)
    return maintenance


def cancel_maintenance_use_case(
    session: Session,
    current_user: User,
    maintenance_id: int,
    reason: Optional[str] = None,
):
    _get_accessible_maintenance(session, current_user, maintenance_id)
    result = MaintenanceService.cancel_maintenance(session, maintenance_id, reason)
    audit_log("maintenance.cancel", current_user.username, f"maintenance:{maintenance_id}", reason=reason, role=current_user.role)
    return result


def delete_maintenance_record_use_case(
    session: Session,
    current_user: User,
    maintenance_id: int,
) -> MaintenanceActionResult:
    _get_accessible_maintenance(session, current_user, maintenance_id)
    MaintenanceService.delete_maintenance(session, maintenance_id)
    audit_log("maintenance.delete", current_user.username, f"maintenance:{maintenance_id}", role=current_user.role)
    return MaintenanceActionResult(message=f"维护记录 {maintenance_id} 已删除")


def list_device_maintenance_history_use_case(
    session: Session,
    current_user: User,
    device_id: int,
    limit: int = 10,
):
    ensure_device_access(session, current_user, device_id)
    return MaintenanceService.get_device_maintenance_history(
        session,
        device_id,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
        limit=limit,
    )


def list_upcoming_maintenance_use_case(
    session: Session,
    current_user: User,
    days: int = 7,
):
    return MaintenanceService.get_upcoming_maintenance(
        session,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
        days=days,
    )


def list_overdue_maintenance_use_case(
    session: Session,
    current_user: User,
):
    return MaintenanceService.get_overdue_maintenance(
        session,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
    )


def summarize_maintenance_statistics_use_case(
    session: Session,
    current_user: User,
    device_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    if device_id is not None:
        ensure_device_access(session, current_user, device_id)
    return MaintenanceService.get_maintenance_statistics(
        session,
        device_id,
        start_date,
        end_date,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
    )
