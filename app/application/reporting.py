"""
报表导出用例。
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlmodel import Session

from app.models.tables import User
from app.services.report_service import ReportService


@dataclass
class CsvExportPayload:
    filename: str
    content: str


REPORT_DEFINITIONS = {
    "energy_detail": {
        "headers": ["时间", "设备ID", "设备名称", "能源类型", "电压(V)", "电流(A)", "功率/流量", "累计消耗"],
        "rows_loader": "energy",
    },
    "alarm_history": {
        "headers": ["时间", "设备ID", "设备名称", "严重级别", "是否已恢复", "消息", "恢复人", "恢复时间"],
        "rows_loader": "alarm",
    },
    "carbon_emission": {
        "headers": ["时间", "设备ID", "设备名称", "能源类型", "能耗", "碳排放"],
        "rows_loader": "carbon",
    },
}


def _safe_filename_date(value: Optional[datetime]) -> str:
    return value.strftime("%Y%m%d") if value else datetime.now().strftime("%Y%m%d")


def list_energy_report_rows_use_case(
    session: Session,
    current_user: Optional[User] = None,
    device_id: Optional[int] = None,
    energy_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
):
    """统一报表导出数据读取入口。"""
    return ReportService.list_energy_report_rows(
        session=session,
        current_user=current_user,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


def list_alarm_report_rows_use_case(
    session: Session,
    current_user: Optional[User] = None,
    device_id: Optional[int] = None,
    resolved: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
) -> list[tuple[Alarm, Optional[str]]]:
    return ReportService.list_alarm_report_rows(
        session=session,
        current_user=current_user,
        device_id=device_id,
        resolved=resolved,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


def list_carbon_report_rows_use_case(
    session: Session,
    current_user: Optional[User] = None,
    device_id: Optional[int] = None,
    energy_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
) -> list[tuple[CarbonEmission, Optional[str]]]:
    return ReportService.list_carbon_report_rows(
        session=session,
        current_user=current_user,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


def build_report_csv_export_use_case(
    session: Session,
    current_user: Optional[User],
    report_type: str,
    device_id: Optional[int] = None,
    energy_type: Optional[str] = None,
    resolved: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
) -> CsvExportPayload:
    normalized_report_type = report_type.strip().lower()
    report_definition = REPORT_DEFINITIONS.get(normalized_report_type)
    if report_definition is None:
        raise ValueError(f"不支持的报表类型: {report_type}")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(report_definition["headers"])

    if report_definition["rows_loader"] == "energy":
        rows = list_energy_report_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        for data, device_name in rows:
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
    elif report_definition["rows_loader"] == "alarm":
        rows = list_alarm_report_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            resolved=resolved,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        for alarm, device_name in rows:
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
    else:
        rows = list_carbon_report_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        for data, device_name in rows:
            writer.writerow([
                data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                data.device_id,
                device_name,
                data.energy_type,
                data.energy_consumption,
                data.carbon_emission,
            ])

    return CsvExportPayload(
        filename=f"{normalized_report_type}_{_safe_filename_date(end_time or start_time)}.csv",
        content=output.getvalue(),
    )
