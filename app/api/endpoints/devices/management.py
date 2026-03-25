"""
设备管理接口
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.endpoint_utils import bad_request_from_value_error, log_endpoint_exception
from app.api.deps import get_current_user
from app.core.database import get_session
from app.core.rate_limit import limit_requests
from app.core.response import success_response
from app.core.settings import settings
from app.models.tables import Device, User
from app.services.device_service import DeviceService
from app.services.mqtt_publisher import publish_control_command

from .shared import DeviceCreateRequest, DeviceUpdateRequest

router = APIRouter()


@router.get("/", response_model=List[Device])
def get_devices(
    energy_type: Optional[str] = Query(None, description="按能源类型筛选"),
    category: Optional[str] = Query(None, description="按设备类别筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    session: Session = Depends(get_session),
):
    return DeviceService.get_all_devices(
        session,
        energy_type=energy_type,
        category=category,
        is_active=is_active,
    )


@router.get("/types")
def get_device_types():
    return success_response(data=DeviceService.get_device_types())


@router.get("/types/{device_type}")
def get_device_type_info(device_type: str):
    info = DeviceService.get_device_type_info(device_type)
    if not info:
        raise HTTPException(status_code=404, detail="设备类型不存在")
    return success_response(data=info)


@router.post("/", response_model=Device)
def create_device_smart(
    req: DeviceCreateRequest,
    session: Session = Depends(get_session),
):
    try:
        return DeviceService.create_device_smart(
            session=session,
            name=req.name,
            sn=req.sn,
            device_type=req.device_type,
            location=req.location,
            description=req.description,
            rated_capacity=req.rated_capacity,
        )
    except ValueError as exc:
        raise bad_request_from_value_error(exc) from exc
    except Exception as exc:
        log_endpoint_exception(f"智能创建设备失败 sn={req.sn}, device_type={req.device_type}", exc)
        raise HTTPException(status_code=500, detail="创建设备失败")


@router.post("/legacy", response_model=Device)
def create_device_legacy(
    device: Device,
    session: Session = Depends(get_session),
):
    return DeviceService.create_device(session, device)


@router.get("/{device_id}", response_model=Device)
def get_device(
    device_id: int,
    session: Session = Depends(get_session),
):
    return DeviceService.get_device_by_id(session, device_id)


@router.put("/{device_id}", response_model=Device)
def update_device(
    device_id: int,
    req: DeviceUpdateRequest,
    session: Session = Depends(get_session),
):
    return DeviceService.update_device(
        session,
        device_id,
        name=req.name,
        location=req.location,
        description=req.description,
        rated_capacity=req.rated_capacity,
    )


@router.delete("/{device_id}")
def delete_device(
    device_id: int,
    session: Session = Depends(get_session),
):
    device = DeviceService.get_device_by_id(session, device_id)
    DeviceService.delete_device(session, device_id)
    return success_response(message=f"设备 {device.name} 已删除")


@router.post("/{device_id}/toggle")
def toggle_device_status(
    device_id: int,
    active: bool,
    reason: Optional[str] = Query(None, description="启停原因/备注"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: None = Depends(
        limit_requests(
            bucket="device-control",
            max_calls=settings.device_control_rate_limit_count,
            window_seconds=settings.device_control_rate_limit_window_seconds,
        )
    ),
):
    device = DeviceService.toggle_device_status(
        session,
        device_id,
        active,
        operator=current_user.username,
        reason=reason,
        command_source="api",
    )
    publish_control_command(device.id, "start" if active else "stop")
    return device
