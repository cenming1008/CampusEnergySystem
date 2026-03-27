"""
能源数据与统计接口
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import MAINTAINER_OPERATOR_OR_ADMIN, get_current_user
from app.api.endpoint_utils import bad_request_from_value_error, log_endpoint_exception
from app.application.energy_management import (
    get_energy_statistics_use_case,
    save_energy_data_use_case,
)
from app.core.access_control import ensure_device_access, get_allowed_device_ids
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import EnergyData, User
from app.services.energy_service import EnergyService

from .shared import (
    ENERGY_TYPE_OPTIONS,
    EnergyDataCreate,
    EnergyOverviewResponse,
    EnergyStatisticsResponse,
    extract_optional_energy_fields,
)

router = APIRouter()


@router.post("/data", response_model=EnergyData)
def save_energy_data(
    data: EnergyDataCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OPERATOR_OR_ADMIN),
):
    try:
        ensure_device_access(session, current_user, data.device_id)
        result = save_energy_data_use_case(
            session=session,
            device_id=data.device_id,
            energy_type=data.energy_type,
            consumption=data.consumption,
            flow_rate=data.flow_rate,
            timestamp=data.timestamp,
            **extract_optional_energy_fields(data),
        )
        audit_log(
            "energy.save_data",
            current_user.username,
            f"device:{data.device_id}",
            energy_type=data.energy_type,
            role=current_user.role,
        )
        return result
    except ValueError as exc:
        raise bad_request_from_value_error(exc) from exc
    except Exception as exc:
        log_endpoint_exception(f"保存能源数据失败 device_id={data.device_id}, energy_type={data.energy_type}", exc)
        raise HTTPException(status_code=500, detail="保存能源数据失败")


@router.get("/data/{device_id}", response_model=List[EnergyData])
def get_energy_data(
    device_id: int,
    energy_type: Optional[str] = Query(None, description="能源类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(1000, ge=1, le=10000, description="返回条数限制"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    return EnergyService.get_energy_data(
        session=session,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


@router.get("/statistics", response_model=EnergyStatisticsResponse)
def get_energy_statistics(
    energy_type: str = Query(..., description="能源类型"),
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    device_id: Optional[int] = Query(None, description="设备ID，不传则系统级统计"),
    period_type: str = Query("day", description="统计周期: hour/day/month/year"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if device_id is not None:
        ensure_device_access(session, current_user, device_id)
    return get_energy_statistics_use_case(
        session=session,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        period_type=period_type,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
    )


@router.get("/overview", response_model=EnergyOverviewResponse)
def get_energy_overview(
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    device_id: Optional[int] = Query(None, description="设备ID，不传则系统级统计"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if device_id is not None:
        ensure_device_access(session, current_user, device_id)
    allowed_device_ids = get_allowed_device_ids(session, current_user)
    energy_types = [item["value"] for item in ENERGY_TYPE_OPTIONS]
    return {
        "statistics": EnergyService.get_statistics_by_type(
            session=session,
            start_time=start_time,
            end_time=end_time,
            device_id=device_id,
            energy_types=energy_types,
            allowed_device_ids=allowed_device_ids,
        ),
        "overview_boundary": "multi_energy_first_batch",
        "unit_rule": "累计量按时段首末差值统计；瞬时量按样本均值和峰值统计；不同能源不直接混算。",
        "cross_energy_mix_allowed": False,
        "carbon_summary": EnergyService.get_carbon_summary(
            session=session,
            start_time=start_time,
            end_time=end_time,
            device_id=device_id,
            allowed_device_ids=allowed_device_ids,
        ),
    }


@router.get("/types", response_model=dict)
def get_energy_types():
    from app.models.tables import DeviceCategory, EnergyType

    return {
        "energy_types": [
            {
                "value": EnergyType(option["value"]),
                "label": option["label"],
                "unit": option["unit"],
                "flow_unit": option["flow_unit"],
                **EnergyService.get_energy_semantics(option["value"]),
            }
            for option in ENERGY_TYPE_OPTIONS
        ],
        "device_categories": [
            {"value": DeviceCategory.LOAD, "label": "用电设备"},
            {"value": DeviceCategory.SOLAR, "label": "光伏发电"},
            {"value": DeviceCategory.WIND, "label": "风力发电"},
            {"value": DeviceCategory.WATER_METER, "label": "水表"},
            {"value": DeviceCategory.GAS_METER, "label": "燃气表"},
            {"value": DeviceCategory.HEAT_METER, "label": "热量表"},
            {"value": DeviceCategory.COOLING_METER, "label": "冷量表"},
            {"value": DeviceCategory.STORAGE, "label": "储能设备"},
            {"value": DeviceCategory.CHARGER, "label": "充电桩"},
        ],
    }
