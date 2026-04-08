"""
分析用例。
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session

from app.core.access_control import ensure_device_access, ensure_location_access, get_allowed_device_ids
from app.services.analysis_service import AnalysisService


def analyze_device_use_case(session: Session, current_user, device_id: int):
    """统一设备分析入口。"""
    ensure_device_access(session, current_user, device_id)
    snapshot = AnalysisService.analyze_device(session, device_id)
    latest = snapshot["latest"]
    semantics = snapshot["semantics"]
    device_type_semantics = snapshot.get("device_type_semantics", {})
    energy_data_fields = snapshot.get("energy_data_fields", {})
    current_value = round((latest.flow_rate or 0) if latest else 0, 2)
    today_consumption = round(snapshot["today_consumption"], 2)
    return {
        "device_id": device_id,
        "device_type": snapshot.get("device_type"),
        "device_category": snapshot.get("device_category"),
        "energy_type": snapshot["energy_type"],
        "energy_label": semantics["label"],
        "is_active": snapshot["is_active"],
        "device_object_role": device_type_semantics.get("object_role"),
        "metering_role": device_type_semantics.get("metering_role"),
        "point_kind": device_type_semantics.get("point_kind"),
        "measurement_subject": device_type_semantics.get("measurement_subject"),
        "current_power": current_value,
        "current_value": current_value,
        "current_value_label": semantics["flow_label"],
        "current_value_unit": semantics["flow_unit"],
        "voltage": round((latest.voltage or 0) if latest else 0, 1),
        "current": round((latest.current or 0) if latest else 0, 2),
        "electrical_fields_applicable": bool(semantics["supports_electrical_quality"]),
        "today_energy": today_consumption,
        "today_consumption": today_consumption,
        "today_consumption_label": semantics["consumption_label"],
        "today_consumption_unit": semantics["consumption_unit"],
        "today_consumption_semantics": semantics["consumption_stat_basis"],
        "energy_data_public_fields": energy_data_fields.get("public_fields", []),
        "energy_data_specialized_fields": energy_data_fields.get("specialized_fields", []),
        "today_cost": round(snapshot["today_cost"], 2),
        "analysis_boundary": "multi_energy_first_batch",
    }


def get_energy_analysis_overview_use_case(
    session: Session,
    current_user,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    location_id: int | None = None,
    energy_type: str | None = None,
    top_n: int = 5,
):
    """统一能耗分析主页面聚合入口。"""
    if location_id is not None:
        ensure_location_access(session, current_user, location_id)

    window_end = end_time or datetime.now()
    window_start = start_time or (window_end - timedelta(days=7))
    if window_start > window_end:
        raise ValueError("start_time 不能晚于 end_time")

    return AnalysisService.get_energy_analysis_overview(
        session=session,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
        location_id=location_id,
        energy_type=energy_type,
        top_n=top_n,
    )
