"""
报警管理服务层
封装报警相关的业务逻辑
"""
from typing import List
from sqlmodel import Session, select

from app.models.tables import Alarm


class AlarmService:
    """报警服务类"""
    
    @staticmethod
    def get_unresolved_alarms(session: Session, limit: int = 20) -> List[Alarm]:
        """获取未处理的报警列表"""
        statement = (
            select(Alarm)
            .where(Alarm.is_resolved == False)
            .order_by(Alarm.timestamp.desc())
            .limit(limit)
        )
        return list(session.exec(statement).all())
    
    @staticmethod
    def resolve_all_alarms(session: Session) -> int:
        """批量解决所有报警"""
        statement = select(Alarm).where(Alarm.is_resolved == False)
        alarms = session.exec(statement).all()
        
        count = 0
        for alarm in alarms:
            alarm.is_resolved = True
            session.add(alarm)
            count += 1
        
        session.commit()
        return count

