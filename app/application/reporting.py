"""
报表导出用例。
"""

from __future__ import annotations

from sqlmodel import Session

from app.repositories.energy_repository import EnergyRepository


def list_energy_report_rows_use_case(session: Session, limit: int = 1000):
    """统一报表导出数据读取入口。"""
    return EnergyRepository.list_energy_report_rows(session=session, limit=limit)
