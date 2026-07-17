"""园区级光储 EMS 只读聚合接口。"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_current_user
from app.api.endpoint_utils import bad_request_from_value_error
from app.core.access_control import ensure_device_access, get_allowed_device_ids
from app.core.database import get_session
from app.models.tables import User
from app.services.devices.storage.dispatch_service import SCENARIO_KEYS
from app.services.storage_energy_service import StorageEnergyService

from .schemas import StorageEnergyOverviewResponse, StorageStrategyComparisonResponse

router = APIRouter()


@router.get("/storage/overview", response_model=StorageEnergyOverviewResponse)
def get_storage_overview(
    device_id: Optional[int] = Query(None, description="储能设备 ID，不传则聚合权限范围内设备"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if device_id is not None:
        ensure_device_access(session, current_user, device_id)
    try:
        return StorageEnergyService.get_overview(
            session,
            allowed_device_ids=get_allowed_device_ids(session, current_user),
            device_id=device_id,
        )
    except ValueError as exc:
        raise bad_request_from_value_error(exc) from exc


@router.get("/storage/comparison", response_model=StorageStrategyComparisonResponse)
def get_storage_comparison(
    scenario_key: str = Query(
        "sunny_workday",
        description=f"固定重放场景：{', '.join(sorted(SCENARIO_KEYS))}",
    ),
    seed: int = Query(20260716, description="固定随机种子"),
    initial_soc: float = Query(50.0, ge=0.0, le=100.0, description="重放初始 SOC (%)"),
    device_id: Optional[int] = Query(None, description="用于读取储能资产参数的设备 ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if device_id is not None:
        ensure_device_access(session, current_user, device_id)
    try:
        return StorageEnergyService.compare_strategies(
            session,
            scenario_key=scenario_key,
            seed=seed,
            initial_soc=initial_soc,
            allowed_device_ids=get_allowed_device_ids(session, current_user),
            device_id=device_id,
        )
    except ValueError as exc:
        raise bad_request_from_value_error(exc) from exc
