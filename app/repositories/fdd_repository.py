"""
故障诊断仓储层：故障诊断相关的数据查询。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, func, select

from app.models.tables import Alarm, Device, EnergyData
from app.repositories.base import BaseRepository


class FDDRepository(BaseRepository):
    """故障诊断数据访问层。"""

    @staticmethod
    def list_device_alarms_since(
        session: Session,
        device_id: int,
        start_time: datetime,
    ) -> list[Alarm]:
        """获取设备在指定时间点之后的所有报警。"""
        statement = (
            select(Alarm)
            .where(Alarm.device_id == device_id)
            .where(Alarm.timestamp >= start_time)
        )
        return list(session.exec(statement).all())

    @staticmethod
    def list_device_running_data_since(
        session: Session,
        device_id: int,
        start_time: datetime,
    ) -> list[tuple[Optional[float], Optional[float], Optional[float]]]:
        """获取设备在指定时间点之后的运行数据（电压/电流/功率）。"""
        statement = (
            select(EnergyData.voltage, EnergyData.current, EnergyData.flow_rate)
            .where(EnergyData.device_id == device_id)
            .where(EnergyData.timestamp >= start_time)
            .order_by(EnergyData.timestamp.asc())
        )
        return list(session.exec(statement).all())

    @staticmethod
    def count_unresolved_alarms_by_device(
        session: Session,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> dict[int, int]:
        """按设备聚合未解决报警数量，返回 {device_id: count}。"""
        statement = (
            select(Alarm.device_id, func.count(Alarm.id).label("cnt"))
            .where(Alarm.is_resolved == False)
            .group_by(Alarm.device_id)
        )
        if allowed_device_ids is not None:
            if not allowed_device_ids:
                return {}
            statement = statement.where(Alarm.device_id.in_(allowed_device_ids))
        rows = session.exec(statement).all()
        return {row[0]: row[1] for row in rows}

    @staticmethod
    def list_devices(
        session: Session,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> list[Device]:
        """获取设备列表（可按可访问范围过滤）。"""
        statement = select(Device)
        if allowed_device_ids is not None:
            if not allowed_device_ids:
                return []
            statement = statement.where(Device.id.in_(allowed_device_ids))
        return list(session.exec(statement).all())

    @staticmethod
    def get_device_by_id(session: Session, device_id: int) -> Optional[Device]:
        """按 ID 获取设备。"""
        return session.get(Device, device_id)
