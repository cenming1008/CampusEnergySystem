"""
设备数据访问
"""

from __future__ import annotations

from typing import Optional

from sqlmodel import Session, select

from app.models.tables import Device


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
    def delete(session: Session, device: Device) -> None:
        session.delete(device)
        session.commit()
