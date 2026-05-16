"""
设备补偿扩展接口：SVG 子类型
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query
from sqlmodel import Session

from app.api.deps import get_current_user
from app.api.endpoints.devices.compensation_schemas import (
    SVGOperationsProfileResponse,
    SVGOperationsProfileUpdate,
    SVGTelemetryResponse,
)
from app.api.endpoints.devices.serializers import serialize_svg_operations_profile
from app.core.access_control import ensure_device_access
from app.core.database import get_session
from app.models.tables import SVGTelemetry, User
from app.services.devices.compensation.svg.service import SVGService

router = APIRouter()


@router.get(
    "/{device_id}/compensation/svg/operations-profile",
    response_model=SVGOperationsProfileResponse,
)
def get_device_svg_operations_profile(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    profile = SVGService.get_operations_profile(session, device_id)
    if not profile:
        raise HTTPException(status_code=404, detail="SVG 运维档案不存在，请先填写")
    return serialize_svg_operations_profile(profile)


@router.put(
    "/{device_id}/compensation/svg/operations-profile",
    response_model=SVGOperationsProfileResponse,
)
def upsert_device_svg_operations_profile(
    device_id: int,
    body: SVGOperationsProfileUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    profile = SVGService.upsert_operations_profile(
        session,
        device_id=device_id,
        payload=body.model_dump(exclude_none=True),
    )
    return serialize_svg_operations_profile(profile)


@router.get(
    "/{device_id}/compensation/svg/telemetry/latest",
    response_model=SVGTelemetryResponse,
)
def get_device_svg_telemetry_latest(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    record = SVGService.get_latest_telemetry(session, device_id)
    if not record:
        raise HTTPException(status_code=404, detail="暂无遥测数据")
    return record


@router.get(
    "/{device_id}/compensation/svg/telemetry",
    response_model=List[SVGTelemetryResponse],
)
def get_device_svg_telemetry_history(
    device_id: int,
    start: Optional[datetime] = Query(None, description="开始时间（ISO 8601）"),
    end: Optional[datetime] = Query(None, description="结束时间（ISO 8601）"),
    limit: int = Query(200, ge=1, le=1000, description="最大返回条数"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    return SVGService.list_telemetry_history(
        session,
        device_id,
        start_time=start,
        end_time=end,
        limit=limit,
    )
