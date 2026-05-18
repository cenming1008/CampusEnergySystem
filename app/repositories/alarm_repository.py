"""
告警仓储层：所有告警相关的数据库查询和持久化操作。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models.tables import Alarm, Device
from app.repositories.base import BaseRepository
from app.domain.alarm_rules import (
    AlarmCreateFields,
    AlarmRecoverFields,
    AlarmRefreshFields,
    ResolveTransition,
)


class AlarmRepository(BaseRepository):
    """告警数据访问层。"""

    @staticmethod
    def get_active_alarm(
        session: Session,
        device_id: int,
        category: str,
        source: str,
    ) -> Optional[Alarm]:
        """获取同设备/类别/来源下仍处于活跃态的实例。"""
        return session.exec(
            select(Alarm)
            .where(Alarm.device_id == device_id)
            .where(Alarm.category == category)
            .where(Alarm.source == source)
            .where(Alarm.recovered_at == None)
            .order_by(Alarm.timestamp.desc())
        ).first()

    @staticmethod
    def get_active_alarms_by_device(
        session: Session,
        device_id: int,
        source: str,
        categories: set[str],
    ) -> list[Alarm]:
        """获取设备在指定来源和类别集合下的所有活跃告警。"""
        if not categories:
            return []
        return list(session.exec(
            select(Alarm)
            .where(Alarm.device_id == device_id)
            .where(Alarm.source == source)
            .where(Alarm.category.in_(categories))
            .where(Alarm.recovered_at == None)
        ).all())

    @staticmethod
    def create_alarm(session: Session, fields: AlarmCreateFields, *, commit: bool = False) -> Alarm:
        """创建新告警记录。"""
        alarm = Alarm(
            device_id=fields.device_id,
            instance_key=fields.instance_key,
            message=fields.message,
            severity=fields.severity,
            category=fields.category,
            source=fields.source,
            timestamp=fields.timestamp,
            last_seen_at=fields.last_seen_at,
            is_resolved=False,
        )
        session.add(alarm)
        if commit:
            session.commit()
            session.refresh(alarm)
        else:
            session.flush()
            session.refresh(alarm)
        return alarm

    @staticmethod
    def refresh_alarm(session: Session, alarm: Alarm, fields: AlarmRefreshFields) -> Alarm:
        """刷新已有告警（更新 last_seen_at、message、severity）。"""
        alarm.instance_key = fields.instance_key
        alarm.message = fields.message
        alarm.severity = fields.severity
        alarm.last_seen_at = fields.last_seen_at
        session.add(alarm)
        return alarm

    @staticmethod
    def recover_alarm(session: Session, alarm: Alarm, fields: AlarmRecoverFields) -> Alarm:
        """标记告警为系统已恢复。"""
        alarm.recovered_at = fields.recovered_at
        session.add(alarm)
        return alarm

    @staticmethod
    def resolve_alarm(session: Session, alarm: Alarm, transition: ResolveTransition) -> Alarm:
        """标记告警为人工已处理。"""
        alarm.is_resolved = transition.is_resolved
        alarm.resolved_at = transition.resolved_at
        alarm.resolved_by = transition.resolved_by
        if transition.handling_note:
            alarm.handling_note = transition.handling_note
        session.add(alarm)
        return alarm

    @staticmethod
    def list_alarms(
        session: Session,
        device_id: Optional[int] = None,
        resolved: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> list[Alarm]:
        """按条件查询告警列表。"""
        statement = select(Alarm)
        if allowed_device_ids is not None:
            statement = statement.where(Alarm.device_id.in_(allowed_device_ids))
        if device_id is not None:
            statement = statement.where(Alarm.device_id == device_id)
        if resolved is not None:
            statement = statement.where(Alarm.is_resolved == resolved)
        if start_time is not None:
            statement = statement.where(Alarm.timestamp >= start_time)
        if end_time is not None:
            statement = statement.where(Alarm.timestamp <= end_time)
        statement = statement.order_by(Alarm.timestamp.desc()).limit(limit)
        return list(session.exec(statement).all())

    @staticmethod
    def get_unresolved_alarms(
        session: Session,
        limit: int = 20,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> list[Alarm]:
        """获取未处理的告警列表。"""
        statement = (
            select(Alarm)
            .where(Alarm.is_resolved == False)
        )
        if allowed_device_ids is not None:
            if not allowed_device_ids:
                return []
            statement = statement.where(Alarm.device_id.in_(allowed_device_ids))
        statement = statement.order_by(Alarm.timestamp.desc()).limit(limit)
        return list(session.exec(statement).all())

    @staticmethod
    def get_alarm_by_id(session: Session, alarm_id: int) -> Optional[Alarm]:
        """按 ID 获取告警。"""
        return session.get(Alarm, alarm_id)

    @staticmethod
    def count_alarms(
        session: Session,
        device_id: Optional[int] = None,
        resolved: Optional[bool] = None,
    ) -> int:
        """统计告警数量。"""
        statement = select(Alarm)
        if device_id is not None:
            statement = statement.where(Alarm.device_id == device_id)
        if resolved is not None:
            statement = statement.where(Alarm.is_resolved == resolved)
        return len(list(session.exec(statement).all()))

    @staticmethod
    def get_device_rated_capacity(session: Session, device_id: int) -> Optional[float]:
        """获取设备额定容量。"""
        return session.exec(
            select(Device.rated_capacity).where(Device.id == device_id)
        ).first()

    @staticmethod
    def get_device_category(session: Session, device_id: int) -> Optional[str]:
        """获取设备类别。"""
        device = session.get(Device, device_id)
        return getattr(device, "device_category", None) if device else None

    @staticmethod
    def get_device_rule_identity(session: Session, device_id: int) -> tuple[Optional[str], Optional[str]]:
        """获取告警规则解析所需的设备分类身份。"""
        device = session.get(Device, device_id)
        if not device:
            return None, None
        return getattr(device, "device_category", None), getattr(device, "device_subtype", None)
