"""
报警管理服务层
封装报警相关的业务逻辑
"""
from typing import List
from sqlmodel import Session, select
from datetime import datetime

from app.models.tables import Alarm
from app.core.logger import logger


class AlarmService:
    """
    报警管理服务类
    
    提供报警相关的业务逻辑，包括：
    - 获取未解决的报警列表
    - 批量解决报警
    - 报警统计和查询
    """
    
    @staticmethod
    def get_unresolved_alarms(session: Session, limit: int = 20) -> List[Alarm]:
        """
        获取未解决的报警列表
        
        Args:
            session: 数据库会话
            limit: 返回的最大记录数，默认20条
            
        Returns:
            未解决的报警列表，按时间倒序排列（最新的在前）
        """
        statement = (
            select(Alarm)
            .where(Alarm.is_resolved == False)
            .order_by(Alarm.timestamp.desc())
            .limit(limit)
        )
        alarms = session.exec(statement).all()
        return list(alarms)
    
    @staticmethod
    def resolve_all_alarms(session: Session) -> int:
        """
        批量解决所有未解决的报警
        
        Args:
            session: 数据库会话
            
        Returns:
            解决的报警数量
        """
        # 查询所有未解决的报警
        unresolved = session.exec(
            select(Alarm).where(Alarm.is_resolved == False)
        ).all()
        
        if not unresolved:
            return 0
        
        # 批量更新为已解决
        count = 0
        for alarm in unresolved:
            alarm.is_resolved = True
            session.add(alarm)
            count += 1
        
        # 提交事务
        session.commit()
        
        logger.info(f"批量解决了 {count} 条报警")
        return count
    
    @staticmethod
    def resolve_alarm(session: Session, alarm_id: int) -> bool:
        """
        解决单个报警
        
        Args:
            session: 数据库会话
            alarm_id: 报警ID
            
        Returns:
            是否成功解决，如果报警不存在或已解决则返回False
        """
        alarm = session.get(Alarm, alarm_id)
        if not alarm or alarm.is_resolved:
            return False
        
        alarm.is_resolved = True
        session.add(alarm)
        session.commit()
        
        logger.info(f"报警 {alarm_id} 已标记为已解决")
        return True
    
    @staticmethod
    def get_alarm_count(session: Session, device_id: int = None, resolved: bool = None) -> int:
        """
        获取报警数量统计
        
        Args:
            session: 数据库会话
            device_id: 设备ID，如果指定则只统计该设备的报警
            resolved: 是否已解决，None表示统计所有报警
            
        Returns:
            报警数量
        """
        statement = select(Alarm)
        
        if device_id is not None:
            statement = statement.where(Alarm.device_id == device_id)
        
        if resolved is not None:
            statement = statement.where(Alarm.is_resolved == resolved)
        
        alarms = session.exec(statement).all()
        return len(list(alarms))
    
    @staticmethod
    def create_alarm(
        session: Session,
        device_id: int,
        message: str,
        timestamp: datetime = None
    ) -> Alarm:
        """
        创建新的报警记录
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            message: 报警消息
            timestamp: 报警时间，如果为None则使用当前时间
            
        Returns:
            创建的报警对象
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        alarm = Alarm(
            device_id=device_id,
            message=message,
            timestamp=timestamp,
            is_resolved=False
        )
        
        session.add(alarm)
        session.commit()
        session.refresh(alarm)
        
        logger.info(f"创建报警: 设备 {device_id} - {message}")
        return alarm
