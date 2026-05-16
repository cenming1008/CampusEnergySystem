"""储能设备扩展接口"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.access_control import ensure_device_access
from app.core.database import get_session
from app.models.storage import StorageTelemetry
from app.models.tables import User
from app.services.devices.storage.monitor_service import StorageMonitorService

router = APIRouter()


@router.get("/{device_id}/storage/telemetry/latest")
def get_storage_telemetry_latest(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    record = StorageMonitorService.get_latest_telemetry(session, device_id)
    if not record:
        raise HTTPException(status_code=404, detail="暂无遥测数据")
    return record


@router.get("/{device_id}/storage/telemetry", response_model=List[StorageTelemetry])
def get_storage_telemetry_history(
    device_id: int,
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    return StorageMonitorService.list_telemetry_history(
        session,
        device_id,
        start_time=start,
        end_time=end,
        limit=limit,
    )
