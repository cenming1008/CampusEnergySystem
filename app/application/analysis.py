"""
分析用例。
"""

from __future__ import annotations

from sqlmodel import Session

from app.services.analysis_service import AnalysisService


def analyze_device_use_case(session: Session, device_id: int):
    """统一设备分析入口。"""
    return AnalysisService.analyze_device(session, device_id)
