"""
审计日志工具。
"""

from __future__ import annotations

import json
from contextvars import ContextVar
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlmodel import Session

from app.core.database import engine
from app.core.logger import logger
from app.models.tables import AuditEvent, UserRole


_AUDIT_REQUEST_CONTEXT: ContextVar[dict[str, Any]] = ContextVar(
    "audit_request_context",
    default={},
)


def _serialize_audit_value(value: Any) -> Any:
    """将审计细节转换为可 JSON 序列化的结构。"""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, set):
        return sorted(_serialize_audit_value(item) for item in value)
    if isinstance(value, (list, tuple)):
        return [_serialize_audit_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serialize_audit_value(item) for key, item in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _normalize_role(role: Any) -> Optional[str]:
    """统一角色字段存储格式。"""
    if role is None:
        return None
    if isinstance(role, UserRole):
        return role.value
    return str(role)


def set_audit_request_context(**context: Any) -> object:
    """设置当前请求的审计上下文。"""
    serialized_context = {
        key: _serialize_audit_value(value)
        for key, value in context.items()
        if value is not None
    }
    return _AUDIT_REQUEST_CONTEXT.set(serialized_context)


def reset_audit_request_context(token: object) -> None:
    """重置当前请求的审计上下文。"""
    _AUDIT_REQUEST_CONTEXT.reset(token)


def get_audit_request_context() -> dict[str, Any]:
    """读取当前请求的审计上下文。"""
    return dict(_AUDIT_REQUEST_CONTEXT.get())


def audit_log(action: str, actor: str, target: str, outcome: str = "success", **details: Any) -> None:
    """记录关键安全与运维操作审计日志，并尽力写入数据库。"""
    serialized_details = {key: _serialize_audit_value(value) for key, value in details.items()}
    request_context = get_audit_request_context()
    if request_context:
        serialized_details.update(
            {
                key: value
                for key, value in request_context.items()
                if key not in serialized_details
            }
        )
    actor_role = _normalize_role(serialized_details.get("role"))
    payload = {
        "action": action,
        "actor": actor,
        "target": target,
        "outcome": outcome,
        "actor_role": actor_role,
        "details": serialized_details,
    }
    logger.warning(f"AUDIT {payload}")

    try:
        with Session(engine) as session:
            event = AuditEvent(
                action=action,
                actor=actor,
                target=target,
                outcome=outcome,
                actor_role=actor_role,
                details=json.dumps(serialized_details, ensure_ascii=False, sort_keys=True),
            )
            session.add(event)
            session.commit()
    except Exception as exc:
        logger.warning(f"Audit persistence skipped: {exc}")
