"""
设备补偿扩展接口：传统电容补偿控制器子类型
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.api.endpoints.devices.compensation_schemas import CapacitorBankTelemetryResponse
from app.core.access_control import ensure_device_access
from app.core.database import get_session
from app.models.tables import CapacitorBankTelemetry, User

router = APIRouter()


@router.get(
    "/{device_id}/compensation/capacitor-bank/telemetry/latest",
    response_model=CapacitorBankTelemetryResponse,
)
def get_device_capacitor_bank_telemetry_latest(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    record = session.exec(
        select(CapacitorBankTelemetry)
        .where(CapacitorBankTelemetry.device_id == device_id)
        .order_by(CapacitorBankTelemetry.timestamp.desc())
        .limit(1)
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="暂无遥测数据")
    return record


@router.get(
    "/{device_id}/compensation/capacitor-bank/telemetry",
    response_model=List[CapacitorBankTelemetryResponse],
)
def get_device_capacitor_bank_telemetry_history(
    device_id: int,
    start: Optional[datetime] = Query(None, description="开始时间（ISO 8601）"),
    end: Optional[datetime] = Query(None, description="结束时间（ISO 8601）"),
    limit: int = Query(200, ge=1, le=1000, description="最大返回条数"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    stmt = select(CapacitorBankTelemetry).where(CapacitorBankTelemetry.device_id == device_id)
    if start:
        stmt = stmt.where(CapacitorBankTelemetry.timestamp >= start)
    if end:
        stmt = stmt.where(CapacitorBankTelemetry.timestamp <= end)
    stmt = stmt.order_by(CapacitorBankTelemetry.timestamp.desc()).limit(limit)
    return session.exec(stmt).all()
