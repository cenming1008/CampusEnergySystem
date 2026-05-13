"""储能设备扩展接口"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.access_control import ensure_device_access
from app.core.database import get_session
from app.models.storage import StorageTelemetry
from app.models.tables import User

router = APIRouter()


def _sample_records(records: list, limit: int) -> list:
    if len(records) <= limit or limit < 3:
        return records
    sampled = [records[0]]
    interior_target = limit - 2
    last_index = len(records) - 1
    for index in range(1, interior_target + 1):
        point_index = round((index * last_index) / (interior_target + 1))
        point = records[min(last_index - 1, max(1, point_index))]
        if sampled[-1] is not point:
            sampled.append(point)
    if sampled[-1] is not records[last_index]:
        sampled.append(records[last_index])
    return sampled


@router.get("/{device_id}/storage/telemetry/latest")
def get_storage_telemetry_latest(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    record = session.exec(
        select(StorageTelemetry)
        .where(StorageTelemetry.device_id == device_id)
        .order_by(StorageTelemetry.timestamp.desc())
        .limit(1)
    ).first()
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
    stmt = select(StorageTelemetry).where(StorageTelemetry.device_id == device_id)
    if start:
        stmt = stmt.where(StorageTelemetry.timestamp >= start)
    if end:
        stmt = stmt.where(StorageTelemetry.timestamp <= end)
    stmt = stmt.order_by(StorageTelemetry.timestamp.desc()).limit(limit * 3)
    records = list(session.exec(stmt).all())
    records.reverse()
    return _sample_records(records, limit)
