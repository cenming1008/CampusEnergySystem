"""
能源碳排放接口
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_current_user
from app.application.energy_management import (
    get_carbon_summary_use_case,
    list_carbon_emissions_use_case,
)
from app.core.access_control import ensure_device_access, get_allowed_device_ids
from app.core.database import get_session
from app.core.response import success_response
from app.domain.energy_rules import CARBON_FACTORS, ENERGY_UNITS, calculate_manual_carbon
from app.models.tables import CarbonEmission, User

from .shared import CarbonSummaryResponse

router = APIRouter()


@router.get("/carbon/emissions", response_model=List[CarbonEmission])
def get_carbon_emissions(
    device_id: Optional[int] = Query(None, description="设备ID，不传则查询所有"),
    energy_type: Optional[str] = Query(None, description="能源类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回条数限制"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if device_id is not None:
        ensure_device_access(session, current_user, device_id)
    return list_carbon_emissions_use_case(
        session=session,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
    )


@router.get("/carbon/summary", response_model=CarbonSummaryResponse)
def get_carbon_summary(
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    device_id: Optional[int] = Query(None, description="设备ID，不传则查询所有"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if device_id is not None:
        ensure_device_access(session, current_user, device_id)
    return get_carbon_summary_use_case(
        session=session,
        start_time=start_time,
        end_time=end_time,
        device_id=device_id,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
    )


@router.get("/carbon/factors", response_model=dict)
def get_carbon_factors():
    return {
        "carbon_factors": {
            energy_type: {
                "factor": factor,
                "unit": f"kg CO2/{ENERGY_UNITS.get(energy_type, '')}",
            }
            for energy_type, factor in CARBON_FACTORS.items()
        },
        "description": "碳排放因子参考国家标准，实际使用时可根据地区调整",
    }


@router.post("/carbon/calculate")
def calculate_carbon_manual(
    energy_type: str = Query(..., description="能源类型"),
    consumption: float = Query(..., description="消耗量"),
    session: Session = Depends(get_session),
):
    return success_response(data=calculate_manual_carbon(energy_type, consumption))
