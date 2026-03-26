"""
能源管理用例
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Session

from app.models.tables import CarbonEmission, EnergyData
from app.services.energy_service import EnergyService


def save_energy_data_use_case(
    session: Session,
    device_id: int,
    energy_type: str,
    consumption: float,
    flow_rate: Optional[float] = None,
    timestamp: Optional[datetime] = None,
    **kwargs: Any,
) -> EnergyData:
    """统一能源数据保存入口。"""
    return EnergyService.save_energy_data(
        session=session,
        device_id=device_id,
        energy_type=energy_type,
        consumption=consumption,
        flow_rate=flow_rate,
        timestamp=timestamp,
        **kwargs,
    )


def get_energy_statistics_use_case(
    session: Session,
    energy_type: str,
    start_time: datetime,
    end_time: datetime,
    device_id: Optional[int] = None,
    period_type: str = "day",
    allowed_device_ids: Optional[set[int]] = None,
) -> Dict[str, Any]:
    """统一能源统计入口。"""
    return EnergyService.calculate_statistics(
        session=session,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        period_type=period_type,
        allowed_device_ids=allowed_device_ids,
    )


def get_carbon_summary_use_case(
    session: Session,
    start_time: datetime,
    end_time: datetime,
    device_id: Optional[int] = None,
    allowed_device_ids: Optional[set[int]] = None,
) -> Dict[str, Any]:
    """统一碳排放汇总入口。"""
    return EnergyService.get_carbon_summary(
        session=session,
        start_time=start_time,
        end_time=end_time,
        device_id=device_id,
        allowed_device_ids=allowed_device_ids,
    )


def list_carbon_emissions_use_case(
    session: Session,
    device_id: Optional[int] = None,
    energy_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    allowed_device_ids: Optional[set[int]] = None,
) -> list[CarbonEmission]:
    """统一碳排放查询入口。"""
    return EnergyService.get_carbon_emissions(
        session=session,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        allowed_device_ids=allowed_device_ids,
    )
