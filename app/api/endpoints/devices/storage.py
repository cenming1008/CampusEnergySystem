"""储能设备扩展接口"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import MAINTAINER_OPERATOR_OR_ADMIN, MAINTAINER_OR_ADMIN, get_current_user
from app.api.endpoints.devices.storage_schemas import (
    StorageAssetProfileUpdate,
    StorageControlRequest,
    StorageControlResponse,
    StorageSimulationControlRequest,
)
from app.core.access_control import ensure_device_access
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.settings import settings
from app.models.storage import StorageAssetProfile, StorageTelemetry
from app.models.tables import User, UserRole
from app.services.devices.storage.asset_profile_service import StorageAssetProfileService
from app.services.devices.storage.control_command_service import StorageControlCommandService
from app.services.devices.storage.monitor_service import StorageMonitorService
from app.services.devices.storage.specs import (
    SUPPORTED_COMMAND_SOURCES,
    SUPPORTED_CONTROL_MODES,
    SUPPORTED_STORAGE_COMMANDS,
)
from app.services.mqtt_publisher import publish_topic_payload_async

router = APIRouter()


def _ensure_storage_device(device: Any) -> None:
    if str(getattr(device, "device_category", "")) != "storage":
        raise HTTPException(status_code=404, detail="当前设备不是储能设备")


def _ensure_simulation_enabled() -> None:
    if not settings.storage_simulation_enabled:
        raise HTTPException(status_code=404, detail="储能模拟控制未启用")


@router.get("/{device_id}/storage/profile", response_model=StorageAssetProfile)
def get_storage_profile(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    device = ensure_device_access(session, current_user, device_id)
    _ensure_storage_device(device)
    profile = StorageAssetProfileService.get_profile(session, device_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="暂无储能资产档案")
    return profile


@router.put("/{device_id}/storage/profile", response_model=StorageAssetProfile)
def put_storage_profile(
    device_id: int,
    body: StorageAssetProfileUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    device = ensure_device_access(session, current_user, device_id)
    _ensure_storage_device(device)
    try:
        profile = StorageAssetProfileService.upsert_profile(
            session,
            device_id,
            body.model_dump(),
            allow_auto_gate_update=current_user.role == UserRole.ADMIN,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    audit_log(
        "device.storage.update_profile",
        current_user.username,
        f"device:{device_id}",
        ems_auto_enabled=profile.ems_auto_enabled,
        role=current_user.role,
    )
    return profile


@router.get("/{device_id}/storage/control/capabilities")
def get_storage_control_capabilities(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    device = ensure_device_access(session, current_user, device_id)
    _ensure_storage_device(device)
    profile = StorageAssetProfileService.get_profile(session, device_id)
    return {
        "commands": sorted(SUPPORTED_STORAGE_COMMANDS),
        "sources": sorted(SUPPORTED_COMMAND_SOURCES),
        "control_modes": sorted(SUPPORTED_CONTROL_MODES),
        "power_sign": {"charge": "positive", "discharge": "negative"},
        "ems_auto_enabled": bool(profile.ems_auto_enabled) if profile else False,
        "ems_global_enabled": settings.storage_ems_enabled,
    }


@router.post("/{device_id}/storage/control", response_model=StorageControlResponse)
def send_storage_control(
    device_id: int,
    body: StorageControlRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OPERATOR_OR_ADMIN),
):
    device = ensure_device_access(session, current_user, device_id)
    _ensure_storage_device(device)
    try:
        result = StorageControlCommandService.queue_command(
            session,
            device,
            command=body.command,
            operator=current_user.username,
            source=body.source,
            target_active_power=body.target_active_power,
            control_mode=body.control_mode,
            reason=body.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    audit_log(
        "device.storage.control",
        current_user.username,
        f"device:{device_id}",
        command=body.command,
        command_id=result["command_id"],
        role=current_user.role,
    )
    return result


@router.get("/{device_id}/storage/simulation/capabilities")
def get_storage_simulation_capabilities(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _ensure_simulation_enabled()
    device = ensure_device_access(session, current_user, device_id)
    _ensure_storage_device(device)
    return {
        "enabled": True,
        "actions": ["set_scenario", "set_speed", "inject_fault", "clear_fault"],
        "scenarios": [
            "sunny_workday",
            "cloudy_workday",
            "weekend_low_load",
            "pv_surplus",
            "evening_peak",
        ],
        "speeds": [1, 10, 60, 288],
        "faults": ["low_soc", "overtemperature", "pcs_fault", "communication_loss", "pv_drop"],
    }


@router.post("/{device_id}/storage/simulation/control")
def send_storage_simulation_control(
    device_id: int,
    body: StorageSimulationControlRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OPERATOR_OR_ADMIN),
):
    _ensure_simulation_enabled()
    device = ensure_device_access(session, current_user, device_id)
    _ensure_storage_device(device)
    if body.action == "set_scenario" and body.scenario is None:
        raise HTTPException(status_code=400, detail="set_scenario 必须提供 scenario")
    if body.action == "set_speed" and body.speed is None:
        raise HTTPException(status_code=400, detail="set_speed 必须提供 speed")
    if body.action == "inject_fault" and body.fault is None:
        raise HTTPException(status_code=400, detail="inject_fault 必须提供 fault")

    simulation_prefix = settings.storage_simulation_topic_prefix.rstrip("/") + "/"
    production_prefix = settings.mqtt_control_topic_prefix.rstrip("/") + "/"
    if simulation_prefix.startswith(production_prefix) or production_prefix.startswith(simulation_prefix):
        raise HTTPException(status_code=503, detail="储能模拟控制主题与生产控制主题配置冲突")

    payload = body.model_dump(exclude_none=True)
    payload.update(
        {
            "message_type": "simulation_control",
            "device_id": device_id,
            "device_code": device.sn,
            "timestamp": datetime.now().isoformat(),
        }
    )
    topic = f"{simulation_prefix}{device.sn}/control"
    publish_topic_payload_async(topic, payload, worker_name=f"mqtt-storage-simulation-{body.action}-{device_id}")
    audit_log(
        "device.storage.simulation_control",
        current_user.username,
        f"device:{device_id}",
        simulation_action=body.action,
        role=current_user.role,
    )
    return {"accepted": True, "status": "accepted", "message": "储能模拟控制命令已发送"}


@router.get("/{device_id}/storage/telemetry/latest")
def get_storage_telemetry_latest(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    record = StorageMonitorService.get_latest_telemetry(session, device_id)
    if not record:
        raise HTTPException(status_code=404, detail="暂无遥测数据")
    return record


@router.get("/{device_id}/storage/telemetry", response_model=List[StorageTelemetry])
def get_storage_telemetry_history(
    device_id: int,
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    return StorageMonitorService.list_telemetry_history(
        session,
        device_id,
        start_time=start,
        end_time=end,
        limit=limit,
    )
