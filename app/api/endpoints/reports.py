from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.api.deps import get_current_user
from app.application.reporting import build_report_csv_export_use_case
from app.core.database import get_session
from app.core.rate_limit import limit_requests
from app.core.settings import settings
from app.models.tables import User

router = APIRouter()


@router.get("/export_csv")
def export_csv(
    report_type: str = Query("energy_detail", description="报表类型: energy_detail/alarm_history/carbon_emission"),
    device_id: Optional[int] = Query(None, description="设备ID"),
    energy_type: Optional[str] = Query(None, description="能源类型"),
    resolved: Optional[bool] = Query(None, description="仅报警报表使用"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(1000, ge=1, le=20000, description="最大导出条数"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: None = Depends(
        limit_requests(
            bucket="report-export",
            max_calls=settings.report_export_rate_limit_count,
            window_seconds=settings.report_export_rate_limit_window_seconds,
        )
    ),
):
    """导出设备历史数据为CSV文件"""
    try:
        payload = build_report_csv_export_use_case(
            session=session,
            current_user=current_user,
            report_type=report_type,
            device_id=device_id,
            energy_type=energy_type,
            resolved=resolved,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = StreamingResponse(
        iter([payload.content]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = f"attachment; filename={payload.filename}"
    return response
