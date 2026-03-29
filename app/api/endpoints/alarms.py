"""
报警管理API端点
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import MAINTAINER_OPERATOR_OR_ADMIN, get_current_user
from app.core.access_control import get_allowed_device_ids
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import Alarm, User
from app.services.alarm_service import AlarmService

router = APIRouter()


@router.get("/", response_model=List[Alarm])
def get_alarms(
    limit: int = 20,
    device_id: Optional[int] = Query(None, description="按设备筛选"),
    resolved: Optional[bool] = Query(False, description="是否已处理，默认仅看未处理"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取报警列表（按人工处理状态过滤，受 location_scope 约束）
    """
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 1

    allowed_ids = get_allowed_device_ids(session, current_user)
    
    return AlarmService.list_alarms(
        session,
        device_id=device_id,
        resolved=resolved,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        allowed_device_ids=allowed_ids,
    )


@router.post("/resolve-all")
def resolve_all_alarms(
    handling_note: Optional[str] = Query(None, description="处理备注"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OPERATOR_OR_ADMIN),
):
    """
    批量处理当前用户可访问范围内的未处理报警
    
    Returns:
        包含处理数量的响应对象
    """
    allowed_ids = get_allowed_device_ids(session, current_user)
    count = AlarmService.resolve_all_alarms(
        session,
        resolved_by=current_user.username,
        handling_note=handling_note,
        allowed_device_ids=allowed_ids,
    )
    audit_log(
        "alarm.resolve_all",
        current_user.username,
        "alarm:*",
        count=count,
        role=getattr(current_user, "role", None),
    )
    return success_response(
        data={"count": count},
        message=f"已处理 {count} 条报警"
    )


@router.post("/resolve/{alarm_id}")
def resolve_alarm(
    alarm_id: int,
    handling_note: Optional[str] = Query(None, description="处理备注"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OPERATOR_OR_ADMIN),
):
    """
    处理单个报警
    
    Args:
        alarm_id: 报警ID
        
    Returns:
        成功响应
        
    Raises:
        HTTPException: 报警不存在、不可访问或已处理时返回404
    """
    allowed_ids = get_allowed_device_ids(session, current_user)
    success = AlarmService.resolve_alarm(
        session,
        alarm_id,
        resolved_by=current_user.username,
        handling_note=handling_note,
        allowed_device_ids=allowed_ids,
    )
    if not success:
        raise HTTPException(status_code=404, detail="报警不存在、不可访问或已处理")
    audit_log(
        "alarm.resolve",
        current_user.username,
        f"alarm:{alarm_id}",
        role=getattr(current_user, "role", None),
    )
    
    return success_response(
        data={"alarm_id": alarm_id},
        message="报警已标记为已处理"
    )
