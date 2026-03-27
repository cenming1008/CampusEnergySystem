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
    return {
        "device_id": device_id,
        "is_active": snapshot["is_active"],
        "current_power": round((latest.flow_rate or 0) if latest else 0, 2),
        "voltage": round((latest.voltage or 0) if latest else 0, 1),
        "current": round((latest.current or 0) if latest else 0, 2),
        "today_energy": round(snapshot["today_energy"], 2),
        "today_cost": round(snapshot["today_cost"], 2),
    }
