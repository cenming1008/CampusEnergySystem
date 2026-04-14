"""
设备监控聚合接口
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.access_control import ensure_device_access
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import User
from app.services.alarm_service import AlarmService
from app.services.device_monitor_service import DeviceMonitorService
from .monitoring_serializers import serialize_items_payload


router = APIRouter()


@router.get("/{device_id}/monitor/overview")
def get_device_monitor_overview(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    return success_response(data=DeviceMonitorService.get_monitor_overview(session, device_id))


@router.get("/{device_id}/monitor/realtime")
def get_device_realtime(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    return success_response(data=DeviceMonitorService.get_latest_realtime(session, device_id))


@router.get("/{device_id}/monitor/runtime-status")
def get_device_runtime_status(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    return success_response(data=DeviceMonitorService.get_runtime_status(session, device_id))


@router.get("/{device_id}/monitor/trend")
def get_device_monitor_trend(
    device_id: int,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(500, ge=1, le=5000, description="返回点数限制"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    return success_response(
        data=DeviceMonitorService.get_trend_summary(
            session,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
    )


@router.get("/{device_id}/monitor/alarms")
def get_device_alarm_history(
    device_id: int,
    resolved: Optional[bool] = Query(None, description="是否已解决"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=500, description="返回条数"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    return success_response(
        data=serialize_items_payload(
            AlarmService.list_alarms(
                session,
                device_id=device_id,
                resolved=resolved,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )
        )
    )


@router.get("/{device_id}/monitor/control-logs")
def get_device_control_logs(
    device_id: int,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=500, description="返回条数"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    return success_response(
        data=serialize_items_payload(
            DeviceMonitorService.get_control_logs(
                session,
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )
        )
    )


@router.get("/{device_id}/monitor/status-history")
def get_device_status_history(
    device_id: int,
    hours: int = Query(72, ge=1, le=720, description="回溯小时数"),
    limit: int = Query(100, ge=1, le=500, description="返回条数"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    return success_response(
        data=serialize_items_payload(
            DeviceMonitorService.get_status_history(
                session,
                device_id=device_id,
                hours=hours,
                limit=limit,
            )
        )
    )
