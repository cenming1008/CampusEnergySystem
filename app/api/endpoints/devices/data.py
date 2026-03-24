"""
设备数据接口
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.endpoint_utils import bad_request_from_value_error, log_endpoint_exception
from app.application.device_reporting import report_device_data_use_case
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import EnergyData
from app.services.device_service import DeviceService

from .shared import DeviceDataReportRequest

router = APIRouter()


@router.post("/{device_id}/data", response_model=EnergyData)
def report_device_data(
    device_id: int,
    req: DeviceDataReportRequest,
    session: Session = Depends(get_session),
):
    try:
        return report_device_data_use_case(
            session=session,
            device_id=device_id,
            data=req.model_dump(exclude_none=True),
            timestamp=req.timestamp,
        )
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
):
    return DeviceService.get_device_data(
        session=session,
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
):
    stats = DeviceService.get_device_statistics(
        session=session,
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        period_type=period_type,
    )
    return success_response(data=stats)
