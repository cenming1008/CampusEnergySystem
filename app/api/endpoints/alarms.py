from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.tables import Alarm

router = APIRouter()

@router.get("/", response_model=List[Alarm])
def read_alarms(limit: int = 20, session: Session = Depends(get_session)):
    """
    获取最新的【未处理】报警记录
    """
    return session.exec(
        select(Alarm)
        .where(Alarm.is_resolved == False)  # 👈 关键点：只查未解决的
        .order_by(Alarm.timestamp.desc())
        .limit(limit)
    ).all()

@router.post("/resolve-all")
def resolve_all_alarms(session: Session = Depends(get_session)):
    """
    一键清除所有报警（标记为已解决）
    """
    # 查出所有未解决的报警
    statement = select(Alarm).where(Alarm.is_resolved == False)
    alarms = session.exec(statement).all()
    
    # 批量标记为 True
    for alarm in alarms:
        alarm.is_resolved = True
        session.add(alarm)
    
    session.commit()
    return {"ok": True, "count": len(alarms)}