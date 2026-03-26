import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.api.deps import get_current_user
from app.application.reporting import (
    list_alarm_report_rows_use_case,
    list_carbon_report_rows_use_case,
    list_energy_report_rows_use_case,
)
from app.core.database import get_session
from app.core.rate_limit import limit_requests
from app.core.settings import settings
from app.models.tables import User

router = APIRouter()


def _safe_filename_date(value: Optional[datetime]) -> str:
    return value.strftime("%Y%m%d") if value else datetime.now().strftime("%Y%m%d")


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
    report_type = report_type.strip().lower()
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "energy_detail":
        writer.writerow([
            "时间", "设备ID", "设备名称", "能源类型",
            "电压(V)", "电流(A)", "功率/流量", "累计消耗"
        ])
        results = list_energy_report_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        for data, device_name in results:
            writer.writerow([
                data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                data.device_id,
                device_name,
                data.energy_type,
                data.voltage,
                data.current,
                data.flow_rate,
                data.consumption,
            ])
    elif report_type == "alarm_history":
        writer.writerow([
            "时间", "设备ID", "设备名称", "严重级别", "是否已恢复", "消息", "恢复人", "恢复时间"
        ])
        results = list_alarm_report_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            resolved=resolved,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        for alarm, device_name in results:
            writer.writerow([
                alarm.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                alarm.device_id,
                device_name,
                alarm.severity,
                "是" if alarm.is_resolved else "否",
                alarm.message,
                alarm.resolved_by or "",
                alarm.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if alarm.resolved_at else "",
            ])
    elif report_type == "carbon_emission":
        writer.writerow([
            "时间", "设备ID", "设备名称", "能源类型", "能耗", "碳排放"
        ])
        results = list_carbon_report_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        for data, device_name in results:
            writer.writerow([
                data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                data.device_id,
                device_name,
                data.energy_type,
                data.energy_consumption,
                data.carbon_emission,
            ])
    else:
        raise HTTPException(status_code=400, detail=f"不支持的报表类型: {report_type}")

    output.seek(0)
    date_label = _safe_filename_date(end_time or start_time)
    response = StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = f"attachment; filename={report_type}_{date_label}.csv"
    return response
