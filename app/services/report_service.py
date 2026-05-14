"""
报表查询服务。

为 application.reporting 提供稳定的报表查询能力，
避免 application 直接承担 ORM 查询细节。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.core.access_control import ensure_device_access
from app.models.tables import Alarm, CarbonEmission, Device, User
from app.models.tables import CapacitorBankTelemetry
from app.repositories.energy_repository import EnergyRepository


class ReportService:
    """报表查询服务。"""

    @staticmethod
    def list_energy_report_rows(
        session: Session,
        current_user: Optional[User] = None,
        device_id: Optional[int] = None,
        energy_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ):
        return EnergyRepository.list_energy_report_rows(
            session=session,
            current_user=current_user,
            device_id=device_id,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    @staticmethod
    def list_alarm_report_rows(
        session: Session,
        current_user: Optional[User] = None,
        device_id: Optional[int] = None,
        resolved: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[tuple[Alarm, Optional[str]]]:
        statement = (
            select(Alarm, Device.name)
            .join(Device, Device.id == Alarm.device_id)
            .order_by(Alarm.timestamp.desc())
            .limit(limit)
        )
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

    @staticmethod
    def list_carbon_report_rows(
        session: Session,
        current_user: Optional[User] = None,
        device_id: Optional[int] = None,
        energy_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[tuple[CarbonEmission, Optional[str], Optional[str], Optional[str]]]:
        statement = (
            select(CarbonEmission, Device.name, Device.device_type, Device.device_category)
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

    @staticmethod
    def list_device_history_report_rows(
        session: Session,
        current_user: Optional[User],
        device_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> dict:
        device = ReportService.get_device_for_history_report(session, current_user, device_id)

        if getattr(device, "device_subtype", None) == "capacitor_bank_controller":
            statement = select(CapacitorBankTelemetry).where(CapacitorBankTelemetry.device_id == device_id)
            if start_time:
                statement = statement.where(CapacitorBankTelemetry.timestamp >= start_time)
            if end_time:
                statement = statement.where(CapacitorBankTelemetry.timestamp <= end_time)
            rows = session.exec(statement.order_by(CapacitorBankTelemetry.timestamp.asc()).limit(limit)).all()
            return {
                "device": device,
                "history_kind": "capacitor_bank",
                "rows": list(rows),
            }

        rows = EnergyRepository.list_energy_data(
            session=session,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        return {
            "device": device,
            "history_kind": "energy",
            "rows": rows,
        }

    @staticmethod
    def get_device_for_history_report(
        session: Session,
        current_user: Optional[User],
        device_id: int,
    ) -> Device:
        if current_user is not None:
            return ensure_device_access(session, current_user, device_id)
        device = session.get(Device, device_id)
        if not device:
            raise ValueError("设备不存在或不可访问")
        return device
