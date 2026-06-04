"""
审计事件查询服务。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

from sqlalchemy import func, or_
from sqlmodel import Session, select

from app.models.tables import AuditEvent


class AuditService:
    """提供审计事件查询、搜索分页和摘要聚合能力。"""

    @staticmethod
    def _build_statement(
        action: Optional[str] = None,
        actor: Optional[str] = None,
        outcome: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        failed_only: bool = False,
        denied_only: bool = False,
    ):
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

    @staticmethod
    def list_events(
        session: Session,
        *,
        action: Optional[str] = None,
        actor: Optional[str] = None,
        outcome: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        statement = AuditService._build_statement(
            action=action,
            actor=actor,
            outcome=outcome,
            start_time=start_time,
            end_time=end_time,
        )
        page_statement = statement.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit)
        return list(session.exec(page_statement).all())

    @staticmethod
    def search_events(
        session: Session,
        *,
        action: Optional[str] = None,
        actor: Optional[str] = None,
        outcome: Optional[str] = None,
        failed_only: bool = False,
        denied_only: bool = False,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        serialize_event: Callable[[AuditEvent], Any],
    ) -> dict[str, Any]:
        base_statement = AuditService._build_statement(
            action=action,
            actor=actor,
            outcome=outcome,
            start_time=start_time,
            end_time=end_time,
            failed_only=failed_only,
            denied_only=denied_only,
        )
        count_statement = base_statement.with_only_columns(func.count()).order_by(None)
        total = int(session.exec(count_statement).one() or 0)
        page_statement = base_statement.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit)
        events = list(session.exec(page_statement).all())

        return {
            "items": [serialize_event(event).model_dump() for event in events],
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_more": offset + len(events) < total,
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

    @staticmethod
    def get_summary(session: Session, *, hours: int = 24) -> dict[str, Any]:
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
        return {
            "window_hours": hours,
            "total": len(events),
            "outcomes": by_outcome,
            "top_actions": [
                {"action": action_name, "count": count}
                for action_name, count in top_actions
            ],
        }
