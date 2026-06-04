"""
审计事件查询 API。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import ADMIN_ONLY
from app.core.audit import _serialize_audit_value
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import AuditEvent, User
from app.services.audit_service import AuditService

router = APIRouter()


class AuditEventResponse(BaseModel):
    """审计事件响应模型。"""

    id: int
    action: str
    actor: str
    target: str
    outcome: str
    actor_role: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


def _to_response(event: AuditEvent) -> AuditEventResponse:
    details: dict[str, Any] = {}
    if event.details:
        try:
            loaded = json.loads(event.details)
            if isinstance(loaded, dict):
                details = {str(key): _serialize_audit_value(value) for key, value in loaded.items()}
        except json.JSONDecodeError:
            details = {"raw": event.details}

    return AuditEventResponse(
        id=event.id or 0,
        action=event.action,
        actor=event.actor,
        target=event.target,
        outcome=event.outcome,
        actor_role=event.actor_role,
        details=details,
        created_at=event.created_at,
    )


@router.get("/events", response_model=List[AuditEventResponse])
def get_audit_events(
    action: Optional[str] = Query(None, description="按操作标识筛选"),
    actor: Optional[str] = Query(None, description="按执行人筛选"),
    outcome: Optional[str] = Query(None, description="按结果筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    """按条件查询审计事件，仅管理员可访问。"""
    events = AuditService.list_events(
        session,
        action=action,
        actor=actor,
        outcome=outcome,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    return [_to_response(event) for event in events]


@router.get("/events/search")
def search_audit_events(
    action: Optional[str] = Query(None, description="按操作标识筛选"),
    actor: Optional[str] = Query(None, description="按执行人筛选"),
    outcome: Optional[str] = Query(None, description="按结果筛选"),
    failed_only: bool = Query(False, description="仅看失败/拒绝事件"),
    denied_only: bool = Query(False, description="仅看拒绝事件"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    """带总数和快捷筛选的审计查询接口。"""
    return success_response(
        data=AuditService.search_events(
            session,
            action=action,
            actor=actor,
            outcome=outcome,
            failed_only=failed_only,
            denied_only=denied_only,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset,
            serialize_event=_to_response,
        )
    )


@router.get("/summary")
def get_audit_summary(
    hours: int = Query(24, ge=1, le=24 * 30, description="统计时间窗(小时)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    """返回审计事件概览，便于后台快速查看近期风险。"""
    return success_response(data=AuditService.get_summary(session, hours=hours))
