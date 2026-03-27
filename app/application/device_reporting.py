"""
设备数据上报用例
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Session

from app.core.access_control import ensure_device_access
from app.core.audit import audit_log
from app.domain.device_payloads import normalize_device_report_payload
from app.models.tables import EnergyData
from app.services.device_service import DeviceService
from app.services.energy_service import EnergyService


def report_device_data_use_case(
    session: Session,
    current_user,
    device_id: int,
    data: Dict[str, Any],
    timestamp: Optional[datetime] = None,
) -> EnergyData:
    """统一设备数据上报入口。"""
    device = ensure_device_access(session, current_user, device_id)
    payload = normalize_device_report_payload(device.device_type, data)
    result = EnergyService.save_energy_data(
        session=session,
        device_id=device_id,
        energy_type=device.energy_type,
        consumption=payload.consumption,
        flow_rate=payload.flow_rate,
        timestamp=timestamp,
        **payload.optional_fields,
    )
    audit_log(
        "device.report_data",
        current_user.username,
        f"device:{device_id}",
        role=getattr(current_user, "role", None),
    )
    return result


def get_device_data_use_case(
    session: Session,
    current_user,
    device_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
) -> list[EnergyData]:
    """统一设备历史数据读取入口。"""
    ensure_device_access(session, current_user, device_id)
    return DeviceService.get_device_data(
        session=session,
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


def get_device_statistics_use_case(
    session: Session,
    current_user,
    device_id: int,
    start_time: datetime,
    end_time: datetime,
    period_type: str = "day",
) -> Dict:
    """统一设备统计读取入口。"""
    ensure_device_access(session, current_user, device_id)
    return DeviceService.get_device_statistics(
        session=session,
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        period_type=period_type,
    )
