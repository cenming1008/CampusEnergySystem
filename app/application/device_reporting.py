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

