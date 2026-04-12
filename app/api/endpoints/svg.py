"""
SVG（静止无功发生器）专属接口

提供 SVG 设备的静态配置、资产档案和实时遥测数据的读写接口。
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.access_control import ensure_device_access
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import SVGAssetProfile, SVGConfig, SVGTelemetry, User
from app.services.svg_service import SVGService

router = APIRouter()


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic 请求/响应模型
# ──────────────────────────────────────────────────────────────────────────────


class SVGOperationsProfileUpdate(BaseModel):
    model_number: Optional[str] = None
    rated_voltage: Optional[float] = None
    rated_frequency: Optional[float] = None
    comm_address: Optional[str] = None
    software_version: Optional[str] = None
    hardware_version: Optional[str] = None
    protocol_version: Optional[str] = None
    module_count: Optional[int] = None
    single_module_capacity: Optional[float] = None
    device_label_zh: Optional[str] = None
    asset_number: Optional[str] = None
    fixed_asset_code: Optional[str] = None
    qr_code_number: Optional[str] = None
    asset_group: Optional[str] = None
    # 现场安装类
    distribution_room: Optional[str] = None
    distribution_cabinet: Optional[str] = None
    circuit: Optional[str] = None
    area: Optional[str] = None
    building: Optional[str] = None
    install_date: Optional[str] = None       # ISO date string YYYY-MM-DD
    commission_date: Optional[str] = None    # ISO date string YYYY-MM-DD
    field_number: Optional[str] = None
    # 管理责任类
    om_responsible: Optional[str] = None
    inspection_responsible: Optional[str] = None
    department: Optional[str] = None
    management_unit: Optional[str] = None
    contact_phone: Optional[str] = None
    warranty_expiry: Optional[str] = None    # ISO date string YYYY-MM-DD
    maintenance_cycle_days: Optional[int] = None
    # 平台建模类
    device_group: Optional[str] = None
    device_tree_level: Optional[str] = None
    monitor_screen_position: Optional[str] = None
    alarm_policy: Optional[str] = None
    device_alias: Optional[str] = None
    display_name: Optional[str] = None


class SVGOperationsProfileResponse(BaseModel):
    id: Optional[int]
    device_id: int
    model_number: Optional[str]
    rated_voltage: Optional[float]
    rated_frequency: Optional[float]
    comm_address: Optional[str]
    software_version: Optional[str]
    hardware_version: Optional[str]
    protocol_version: Optional[str]
    module_count: Optional[int]
    single_module_capacity: Optional[float]
    device_label_zh: Optional[str]
    asset_number: Optional[str]
    fixed_asset_code: Optional[str]
    qr_code_number: Optional[str]
    asset_group: Optional[str]
    distribution_room: Optional[str]
    distribution_cabinet: Optional[str]
    circuit: Optional[str]
    area: Optional[str]
    building: Optional[str]
    install_date: Optional[str]
    commission_date: Optional[str]
    field_number: Optional[str]
    om_responsible: Optional[str]
    inspection_responsible: Optional[str]
    department: Optional[str]
    management_unit: Optional[str]
    contact_phone: Optional[str]
    warranty_expiry: Optional[str]
    maintenance_cycle_days: Optional[int]
    device_group: Optional[str]
    device_tree_level: Optional[str]
    monitor_screen_position: Optional[str]
    alarm_policy: Optional[str]
    device_alias: Optional[str]
    display_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SVGTelemetryResponse(BaseModel):
    device_id: int
    timestamp: datetime
    voltage_a: Optional[float]
    voltage_b: Optional[float]
    voltage_c: Optional[float]
    current_a: Optional[float]
    current_b: Optional[float]
    current_c: Optional[float]
    frequency: Optional[float]
    svg_reactive_output: Optional[float]
    capacity_utilization: Optional[float]
    output_direction: Optional[str]
    run_status: Optional[bool]
    stop_status: Optional[bool]
    auto_mode: Optional[bool]
    local_mode: Optional[bool]
    breaker_status: Optional[bool]
    module_status: Optional[bool]
    fan_status: Optional[bool]
    comm_status: Optional[bool]
    overvoltage_fault: Optional[bool]
    undervoltage_fault: Optional[bool]
    overcurrent_fault: Optional[bool]
    overtemp_fault: Optional[bool]
    module_fault: Optional[bool]
    fan_fault: Optional[bool]
    comm_fault: Optional[bool]
    current_fault_code: Optional[str]
    current_alarm_code: Optional[str]
    cabinet_temp: Optional[float]
    module_temp: Optional[float]
    igbt_temp: Optional[float]
    dc_bus_voltage: Optional[float]
    heatsink_temp: Optional[float]

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────────────────────────
# SVGConfig 端点
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/{device_id}/operations-profile", response_model=SVGOperationsProfileResponse)
def get_svg_operations_profile(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取 SVG 统一运维档案。"""
    ensure_device_access(session, current_user, device_id)
    profile = SVGService.get_operations_profile(session, device_id)
    if not profile:
        raise HTTPException(status_code=404, detail="SVG 运维档案不存在，请先填写")
    return _serialize_profile(profile)


@router.put("/{device_id}/operations-profile", response_model=SVGOperationsProfileResponse)
def upsert_svg_operations_profile(
    device_id: int,
    body: SVGOperationsProfileUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """创建或更新 SVG 统一运维档案。"""
    ensure_device_access(session, current_user, device_id)
    profile = SVGService.upsert_operations_profile(
        session,
        device_id=device_id,
        payload=body.model_dump(exclude_none=True),
    )
    return _serialize_profile(profile)


# ──────────────────────────────────────────────────────────────────────────────
# SVGAssetProfile 端点
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/{device_id}/config", response_model=SVGOperationsProfileResponse)
def get_svg_config(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """兼容旧接口：返回统一运维档案。"""
    return get_svg_operations_profile(device_id, session, current_user)


@router.put("/{device_id}/config", response_model=SVGOperationsProfileResponse)
def upsert_svg_config(
    device_id: int,
    body: SVGOperationsProfileUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """兼容旧接口：写入统一运维档案。"""
    return upsert_svg_operations_profile(device_id, body, session, current_user)


@router.get("/{device_id}/asset-profile", response_model=SVGOperationsProfileResponse)
def get_svg_asset_profile(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取 SVG 资产档案。"""
    ensure_device_access(session, current_user, device_id)
    profile = SVGService.get_operations_profile(session, device_id)
    if not profile:
        raise HTTPException(status_code=404, detail="SVG 资产档案不存在，请先通过 PUT 创建")
    return _serialize_profile(profile)


@router.put("/{device_id}/asset-profile", response_model=SVGOperationsProfileResponse)
def upsert_svg_asset_profile(
    device_id: int,
    body: SVGOperationsProfileUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """创建或更新 SVG 资产档案。"""
    ensure_device_access(session, current_user, device_id)
    profile = SVGService.upsert_operations_profile(
        session,
        device_id=device_id,
        payload=body.model_dump(exclude_none=True),
    )
    return _serialize_profile(profile)


def _serialize_profile(profile: SVGAssetProfile) -> dict:
    """将 date 字段序列化为 ISO 字符串。"""
    data = {}
    date_fields = {"install_date", "commission_date", "warranty_expiry"}
    for field in SVGOperationsProfileResponse.model_fields:
        value = getattr(profile, field, None)
        if field in date_fields and value is not None:
            value = value.isoformat()
        data[field] = value
    return data


# ──────────────────────────────────────────────────────────────────────────────
# SVGTelemetry 端点
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/{device_id}/telemetry/latest", response_model=SVGTelemetryResponse)
def get_svg_telemetry_latest(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取最新一条 SVG 遥测扩展数据。"""
    ensure_device_access(session, current_user, device_id)
    record = session.exec(
        select(SVGTelemetry)
        .where(SVGTelemetry.device_id == device_id)
        .order_by(SVGTelemetry.timestamp.desc())
        .limit(1)
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="暂无遥测数据")
    return record


@router.get("/{device_id}/telemetry", response_model=List[SVGTelemetryResponse])
def get_svg_telemetry_history(
    device_id: int,
    start: Optional[datetime] = Query(None, description="开始时间（ISO 8601）"),
    end: Optional[datetime] = Query(None, description="结束时间（ISO 8601）"),
    limit: int = Query(200, ge=1, le=1000, description="最大返回条数"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """查询 SVG 遥测历史数据。"""
    ensure_device_access(session, current_user, device_id)

    stmt = select(SVGTelemetry).where(SVGTelemetry.device_id == device_id)
    if start:
        stmt = stmt.where(SVGTelemetry.timestamp >= start)
    if end:
        stmt = stmt.where(SVGTelemetry.timestamp <= end)
    stmt = stmt.order_by(SVGTelemetry.timestamp.desc()).limit(limit)

    return list(session.exec(stmt).all())
