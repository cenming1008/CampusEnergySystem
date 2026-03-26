"""
报表导出用例。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models.tables import Alarm, CarbonEmission, Device, User
from app.repositories.energy_repository import EnergyRepository


def list_energy_report_rows_use_case(
    session: Session,
    current_user: Optional[User] = None,
    device_id: Optional[int] = None,
    energy_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
):
    """统一报表导出数据读取入口。"""
    query_kwargs = {"session": session, "limit": limit}
    if current_user is not None:
        query_kwargs["current_user"] = current_user
    if device_id is not None:
        query_kwargs["device_id"] = device_id
    if energy_type is not None:
        query_kwargs["energy_type"] = energy_type
    if start_time is not None:
        query_kwargs["start_time"] = start_time
    if end_time is not None:
        query_kwargs["end_time"] = end_time
    return EnergyRepository.list_energy_report_rows(**query_kwargs)


def list_alarm_report_rows_use_case(
    session: Session,
    current_user: Optional[User] = None,
    device_id: Optional[int] = None,
    resolved: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
) -> list[tuple[Alarm, Optional[str]]]:
    statement = select(Alarm, Device.name).join(Device, Device.id == Alarm.device_id).order_by(Alarm.timestamp.desc()).limit(limit)
    if current_user is not None:
        allowed_location_ids = EnergyRepository.resolve_allowed_location_ids(current_user)
        if allowed_location_ids is not None:
            if not allowed_location_ids:
                return []
            statement = statement.where(Device.location_id.in_(allowed_location_ids))
    if device_id:
        statement = statement.where(Alarm.device_id == device_id)
    if resolved is not None:
        statement = statement.where(Alarm.is_resolved == resolved)
    if start_time:
        statement = statement.where(Alarm.timestamp >= start_time)
    if end_time:
        statement = statement.where(Alarm.timestamp <= end_time)
    return list(session.exec(statement).all())


def list_carbon_report_rows_use_case(
    session: Session,
    current_user: Optional[User] = None,
    device_id: Optional[int] = None,
    energy_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
) -> list[tuple[CarbonEmission, Optional[str]]]:
    statement = (
        select(CarbonEmission, Device.name)
        .join(Device, Device.id == CarbonEmission.device_id)
        .order_by(CarbonEmission.timestamp.desc())
        .limit(limit)
    )
    if current_user is not None:
        allowed_location_ids = EnergyRepository.resolve_allowed_location_ids(current_user)
        if allowed_location_ids is not None:
            if not allowed_location_ids:
                return []
            statement = statement.where(Device.location_id.in_(allowed_location_ids))
    if device_id:
        statement = statement.where(CarbonEmission.device_id == device_id)
    if energy_type:
        statement = statement.where(CarbonEmission.energy_type == energy_type)
    if start_time:
        statement = statement.where(CarbonEmission.timestamp >= start_time)
    if end_time:
        statement = statement.where(CarbonEmission.timestamp <= end_time)
    return list(session.exec(statement).all())
