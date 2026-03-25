"""
设备数据上报用例
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Session

from app.models.tables import EnergyData
from app.services.device_service import DeviceService


def report_device_data_use_case(
    session: Session,
    device_id: int,
    data: Dict[str, Any],
    timestamp: Optional[datetime] = None,
) -> EnergyData:
    """统一设备数据上报入口。"""
    return DeviceService.report_device_data(
        session=session,
        device_id=device_id,
        data=data,
        timestamp=timestamp,
    )


def get_device_data_use_case(
    session: Session,
    device_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
) -> list[EnergyData]:
    """统一设备历史数据读取入口。"""
    return DeviceService.get_device_data(
        session=session,
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


def get_device_statistics_use_case(
    session: Session,
    device_id: int,
    start_time: datetime,
    end_time: datetime,
    period_type: str = "day",
) -> Dict:
    """统一设备统计读取入口。"""
    return DeviceService.get_device_statistics(
        session=session,
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        period_type=period_type,
    )
