"""
设备数据访问
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlmodel import Session, select

from app.models.tables import Device, DeviceControlLog


class DeviceRepository:
    """设备表访问仓储。"""

    @staticmethod
    def get_by_id(session: Session, device_id: int) -> Optional[Device]:
        return session.get(Device, device_id)

    @staticmethod
    def get_by_sn(session: Session, sn: str) -> Optional[Device]:
        return session.exec(select(Device).where(Device.sn == sn)).first()

    @staticmethod
    def list_devices(
        session: Session,
        energy_type: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Device]:
        statement = select(Device)
        if energy_type:
            statement = statement.where(Device.energy_type == energy_type)
        if category:
            statement = statement.where(Device.device_category == category)
        if is_active is not None:
            statement = statement.where(Device.is_active == is_active)
        statement = statement.order_by(Device.id)
        return list(session.exec(statement).all())

    @staticmethod
    def save(session: Session, device: Device) -> Device:
        session.add(device)
        session.commit()
        session.refresh(device)
        return device

    @staticmethod
    def save_control_log(
        session: Session,
        control_log: DeviceControlLog,
        commit: bool = True,
    ) -> DeviceControlLog:
        session.add(control_log)
        if commit:
            session.commit()
            session.refresh(control_log)
        else:
            session.flush()
        return control_log

    @staticmethod
    def list_control_logs(
        session: Session,
        device_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[DeviceControlLog]:
        statement = select(DeviceControlLog).where(DeviceControlLog.device_id == device_id)
        if start_time:
            statement = statement.where(DeviceControlLog.created_at >= start_time)
        if end_time:
            statement = statement.where(DeviceControlLog.created_at <= end_time)
        statement = statement.order_by(DeviceControlLog.created_at.desc()).limit(limit)
        return list(session.exec(statement).all())

    @staticmethod
    def delete(session: Session, device: Device) -> None:
        session.delete(device)
        session.commit()
