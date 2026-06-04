"""
设备监控聚合主流程 use case。
"""

from __future__ import annotations

from typing import Any, Optional

from sqlmodel import Session

from app.core.access_control import ensure_device_access
from app.models.tables import User


def get_device_monitor_overview_use_case(
    session: Session,
    device_id: int,
    current_user: Optional[User] = None,
) -> dict[str, Any]:
    """构建设备监控 overview，保持现有接口返回契约。"""
    if current_user is not None:
        ensure_device_access(session, current_user, device_id)

    from app.services.device_monitor_service import DeviceMonitorService

    return DeviceMonitorService.get_monitor_overview(session, device_id)


__all__ = ["get_device_monitor_overview_use_case"]
