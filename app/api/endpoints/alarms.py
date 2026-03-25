"""
报警管理API端点
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import Alarm, User
from app.services.alarm_service import AlarmService

router = APIRouter()


@router.get("/", response_model=List[Alarm])
def get_alarms(
    limit: int = 20,
    device_id: Optional[int] = Query(None, description="按设备筛选"),
    resolved: Optional[bool] = Query(False, description="是否已解决，默认仅看未解决"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    session: Session = Depends(get_session)
):
    """
    获取未处理的报警列表
    
    Args:
        limit: 返回的最大记录数，默认20条，最大100条
        
    Returns:
        未解决的报警列表，按时间倒序排列（最新的在前）
    """
    # 限制最大返回数量，防止性能问题
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 1
    
    return AlarmService.list_alarms(
        session,
        device_id=device_id,
        resolved=resolved,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


@router.post("/resolve-all")
def resolve_all_alarms(
    handling_note: Optional[str] = Query(None, description="处理备注"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    批量解决所有未处理的报警
    
    将所有未解决的报警标记为已解决
    
    Returns:
        包含解决数量的响应对象
    """
    count = AlarmService.resolve_all_alarms(
        session,
        resolved_by=current_user.username,
        handling_note=handling_note,
    )
    return success_response(
        data={"count": count},
        message=f"已解决 {count} 条报警"
    )


@router.post("/resolve/{alarm_id}")
def resolve_alarm(
    alarm_id: int,
    handling_note: Optional[str] = Query(None, description="处理备注"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    解决单个报警
    
    Args:
        alarm_id: 报警ID
        
    Returns:
        成功响应
        
    Raises:
        HTTPException: 报警不存在或已解决时返回404
    """
    success = AlarmService.resolve_alarm(
        session,
        alarm_id,
        resolved_by=current_user.username,
        handling_note=handling_note,
    )
    if not success:
        raise HTTPException(status_code=404, detail="报警不存在或已解决")
    
    return success_response(
        data={"alarm_id": alarm_id},
        message="报警已标记为已解决"
    )
