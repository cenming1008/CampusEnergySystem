"""
设备数据接口
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import MAINTAINER_OPERATOR_OR_ADMIN, get_current_user
from app.api.endpoint_utils import bad_request_from_value_error, log_endpoint_exception
from app.application.device_reporting import (
    get_device_data_use_case,
    get_device_statistics_use_case,
    report_device_data_use_case,
)
from app.core.database import get_session
from app.core.rate_limit import limit_requests
from app.core.response import success_response
from app.core.settings import settings
from app.models.tables import EnergyData, User

from .schemas import DeviceDataReportRequest

router = APIRouter()


@router.post("/{device_id}/data", response_model=EnergyData)
def report_device_data(
    device_id: int,
    req: DeviceDataReportRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OPERATOR_OR_ADMIN),
    _: None = Depends(
        limit_requests(
            bucket="device-report",
            max_calls=settings.device_report_rate_limit_count,
            window_seconds=settings.device_report_rate_limit_window_seconds,
        )
    ),
):
    try:
        result = report_device_data_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            data=req.model_dump(exclude_none=True),
            timestamp=req.timestamp,
        )
        return result
    except ValueError as exc:
        raise bad_request_from_value_error(exc) from exc
    except Exception as exc:
        log_endpoint_exception(f"设备数据上报失败 device_id={device_id}", exc)
        raise HTTPException(status_code=500, detail="设备数据上报失败")


@router.get("/{device_id}/data", response_model=List[EnergyData])
def get_device_data(
    device_id: int,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(1000, ge=1, le=10000, description="返回条数限制"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return get_device_data_use_case(
        session=session,
        current_user=current_user,
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


@router.get("/{device_id}/statistics")
def get_device_statistics(
    device_id: int,
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    period_type: str = Query("day", description="统计周期: hour/day/month/year"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    stats = get_device_statistics_use_case(
        session=session,
        current_user=current_user,
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        period_type=period_type,
    )
    return success_response(data=stats)
