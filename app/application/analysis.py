"""
分析用例。
"""

from __future__ import annotations

from sqlmodel import Session

from app.core.access_control import ensure_device_access
from app.services.analysis_service import AnalysisService


def analyze_device_use_case(session: Session, current_user, device_id: int):
    """统一设备分析入口。"""
    ensure_device_access(session, current_user, device_id)
    snapshot = AnalysisService.analyze_device(session, device_id)
    latest = snapshot["latest"]
    semantics = snapshot["semantics"]
    current_value = round((latest.flow_rate or 0) if latest else 0, 2)
    today_consumption = round(snapshot["today_consumption"], 2)
    return {
        "device_id": device_id,
        "energy_type": snapshot["energy_type"],
        "energy_label": semantics["label"],
        "is_active": snapshot["is_active"],
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
        "today_cost": round(snapshot["today_cost"], 2),
        "analysis_boundary": "multi_energy_first_batch",
    }
