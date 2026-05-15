"""
能耗分析仓储层：分析专用的数据查询。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models.tables import Alarm, DeviceIngestionHealth, EnergyData
from app.repositories.base import BaseRepository


class AnalysisRepository(BaseRepository):
    """分析专用查询。"""

    @staticmethod
    def list_energy_rows(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]],
        energy_type: Optional[str] = None,
    ) -> list[EnergyData]:
        """按时间窗口和可访问设备过滤查询能耗数据。"""
        if allowed_device_ids is not None and not allowed_device_ids:
            return []
        statement = (
            select(EnergyData)
            .where(EnergyData.timestamp >= start_time)
            .where(EnergyData.timestamp <= end_time)
            .order_by(EnergyData.timestamp.asc())
        )
        if allowed_device_ids is not None:
            statement = statement.where(EnergyData.device_id.in_(allowed_device_ids))
        if energy_type:
            statement = statement.where(EnergyData.energy_type == energy_type)
        return list(session.exec(statement).all())

    @staticmethod
    def list_health_rows(
        session: Session,
        allowed_device_ids: Optional[set[int]],
    ) -> list[DeviceIngestionHealth]:
        """查询设备接入健康表。"""
        if allowed_device_ids is not None and not allowed_device_ids:
            return []
        statement = select(DeviceIngestionHealth)
        if allowed_device_ids is not None:
            statement = statement.where(DeviceIngestionHealth.device_id.in_(allowed_device_ids))
        return list(session.exec(statement).all())

    @staticmethod
    def list_unresolved_alarm_rows(
        session: Session,
        allowed_device_ids: Optional[set[int]],
    ) -> list[Alarm]:
        """查询未处理告警。"""
        if allowed_device_ids is not None and not allowed_device_ids:
            return []
        statement = (
            select(Alarm)
            .where(Alarm.is_resolved == False)  # noqa: E712
            .order_by(Alarm.timestamp.desc())
        )
        if allowed_device_ids is not None:
            statement = statement.where(Alarm.device_id.in_(allowed_device_ids))
        return list(session.exec(statement).all())
