"""
审计事件查询 API。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from sqlalchemy import func, or_

from app.api.deps import ADMIN_ONLY
from app.core.audit import _serialize_audit_value
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import AuditEvent, User

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


def _build_audit_statement(
    action: Optional[str] = None,
    actor: Optional[str] = None,
    outcome: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    failed_only: bool = False,
    denied_only: bool = False,
):
    """构建审计查询条件。"""
    statement = select(AuditEvent)

    if action:
        statement = statement.where(AuditEvent.action == action)
    if actor:
        statement = statement.where(AuditEvent.actor == actor)
    if outcome:
        statement = statement.where(AuditEvent.outcome == outcome)
    if failed_only:
        statement = statement.where(or_(AuditEvent.outcome == "failed", AuditEvent.outcome == "denied"))
    if denied_only:
        statement = statement.where(AuditEvent.outcome == "denied")
    if start_time:
        statement = statement.where(AuditEvent.created_at >= start_time)
    if end_time:
        statement = statement.where(AuditEvent.created_at <= end_time)

    return statement


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
    statement = _build_audit_statement(
        action=action,
        actor=actor,
        outcome=outcome,
        start_time=start_time,
        end_time=end_time,
    )

    statement = (
        statement
        .order_by(AuditEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    events = list(session.exec(statement).all())
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
    base_statement = _build_audit_statement(
        action=action,
        actor=actor,
        outcome=outcome,
        start_time=start_time,
        end_time=end_time,
        failed_only=failed_only,
        denied_only=denied_only,
    )

    count_statement = base_statement.with_only_columns(func.count()).order_by(None)
    total = session.exec(count_statement).one()
    page_statement = base_statement.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit)
    events = list(session.exec(page_statement).all())

    return success_response(
        data={
            "items": [_to_response(event).model_dump() for event in events],
            "total": int(total or 0),
            "offset": offset,
            "limit": limit,
            "has_more": offset + len(events) < int(total or 0),
            "filters": {
                "action": action,
                "actor": actor,
                "outcome": outcome,
                "failed_only": failed_only,
                "denied_only": denied_only,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
            },
        }
    )


@router.get("/summary")
def get_audit_summary(
    hours: int = Query(24, ge=1, le=24 * 30, description="统计时间窗(小时)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    """返回审计事件概览，便于后台快速查看近期风险。"""
    start_time = datetime.now().timestamp() - hours * 3600
    threshold = datetime.fromtimestamp(start_time)
    events = list(
        session.exec(
            select(AuditEvent)
            .where(AuditEvent.created_at >= threshold)
            .order_by(AuditEvent.created_at.desc())
        ).all()
    )

    by_outcome: dict[str, int] = {}
    by_action: dict[str, int] = {}
    for event in events:
        by_outcome[event.outcome] = by_outcome.get(event.outcome, 0) + 1
        by_action[event.action] = by_action.get(event.action, 0) + 1

    top_actions = sorted(by_action.items(), key=lambda item: item[1], reverse=True)[:10]
    return success_response(
        data={
            "window_hours": hours,
            "total": len(events),
            "outcomes": by_outcome,
            "top_actions": [
                {"action": action_name, "count": count}
                for action_name, count in top_actions
            ],
        }
    )
