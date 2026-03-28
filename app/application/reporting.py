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

from app.core.access_control import get_allowed_device_ids
from app.domain.device_payloads import describe_device_type_semantics
from app.models.tables import User
from app.services.energy_service import EnergyService
from app.services.report_service import ReportService


@dataclass
class CsvExportPayload:
    filename: str
    content: str


REPORT_DEFINITIONS = {
    "energy_detail": {
        "headers": ["时间", "设备ID", "设备名称", "能源类型", "电压(V)", "电流(A)", "功率/流量", "累计消耗", "设备类型", "设备类别", "对象语义", "点位语义"],
        "rows_loader": "energy",
    },
    "alarm_history": {
        "headers": ["时间", "设备ID", "设备名称", "严重级别", "是否已恢复", "消息", "恢复人", "恢复时间"],
        "rows_loader": "alarm",
    },
    "carbon_emission": {
        "headers": ["时间", "设备ID", "设备名称", "能源类型", "能耗", "碳排放", "设备类型", "设备类别", "对象语义", "点位语义"],
        "rows_loader": "carbon",
    },
    "multi_energy_summary": {
        "headers": ["能源类型", "周期消耗", "累计单位", "平均瞬时值", "瞬时单位", "峰值瞬时值", "样本数", "碳排估算(kg CO2)", "碳排边界"],
        "rows_loader": "multi_energy_summary",
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


def build_multi_energy_summary_rows_use_case(
    session: Session,
    current_user: Optional[User] = None,
    device_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    if start_time is None or end_time is None:
        raise ValueError("multi_energy_summary 需要同时提供 start_time 和 end_time")

    energy_types = [item["energy_type"] for item in EnergyService.list_energy_type_catalog()]
    allowed_device_ids = get_allowed_device_ids(session, current_user)
    statistics = EnergyService.get_statistics_by_type(
        session=session,
        start_time=start_time,
        end_time=end_time,
        energy_types=energy_types,
        device_id=device_id,
        allowed_device_ids=allowed_device_ids,
    )
    carbon_summary = EnergyService.get_carbon_summary(
        session=session,
        start_time=start_time,
        end_time=end_time,
        device_id=device_id,
        allowed_device_ids=allowed_device_ids,
    )

    rows = []
    for energy_type in energy_types:
        stats = statistics.get(energy_type, {})
        if not stats or not stats.get("data_count"):
            continue
        semantics = EnergyService.get_energy_semantics(energy_type)
        carbon_payload = carbon_summary["by_energy_type"].get(energy_type, {})
        rows.append(
            {
                "energy_type": energy_type,
                "energy_label": semantics["label"],
                "total_consumption": stats["total_consumption"],
                "consumption_unit": stats["consumption_unit"],
                "avg_flow_rate": round(stats["avg_flow_rate"], 4),
                "flow_unit": stats["flow_unit"],
                "peak_flow_rate": round(stats["peak_flow_rate"], 4),
                "data_count": stats["data_count"],
                "carbon_emission": carbon_payload.get("carbon_emission", 0.0),
                "carbon_boundary": carbon_payload.get("boundary", carbon_summary.get("boundary", "display_estimate")),
            }
        )
    return rows


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
        for data, device_name, device_type, device_category in rows:
            semantics = describe_device_type_semantics(device_type)
            writer.writerow([
                data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                data.device_id,
                device_name,
                data.energy_type,
                data.voltage,
                data.current,
                data.flow_rate,
                data.consumption,
                device_type,
                device_category,
                semantics["object_role"],
                semantics["point_kind"],
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
    elif report_definition["rows_loader"] == "carbon":
        rows = list_carbon_report_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        for data, device_name, device_type, device_category in rows:
            semantics = describe_device_type_semantics(device_type)
            writer.writerow([
                data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                data.device_id,
                device_name,
                data.energy_type,
                data.energy_consumption,
                data.carbon_emission,
                device_type,
                device_category,
                semantics["object_role"],
                semantics["point_kind"],
            ])
    else:
        rows = build_multi_energy_summary_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
        )
        for row in rows:
            writer.writerow([
                row["energy_label"],
                row["total_consumption"],
                row["consumption_unit"],
                row["avg_flow_rate"],
                row["flow_unit"],
                row["peak_flow_rate"],
                row["data_count"],
                row["carbon_emission"],
                row["carbon_boundary"],
            ])

    return CsvExportPayload(
        filename=f"{normalized_report_type}_{_safe_filename_date(end_time or start_time)}.csv",
        content=output.getvalue(),
    )
