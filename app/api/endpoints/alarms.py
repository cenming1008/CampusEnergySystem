"""
报警管理API端点
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import Alarm
from app.services.alarm_service import AlarmService

router = APIRouter()


@router.get("/", response_model=List[Alarm])
def get_alarms(
    limit: int = 20,
    session: Session = Depends(get_session)
):
    """获取未处理的报警列表"""
    return AlarmService.get_unresolved_alarms(session, limit)


@router.post("/resolve-all")
def resolve_all_alarms(session: Session = Depends(get_session)):
    """批量解决所有报警"""
    count = AlarmService.resolve_all_alarms(session)
    return success_response(
        data={"count": count},
        message=f"已解决 {count} 条报警"
    )