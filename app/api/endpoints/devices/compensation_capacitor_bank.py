"""
设备补偿扩展接口：传统电容补偿控制器子类型
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import MAINTAINER_OR_ADMIN, OPERATOR_OR_ADMIN, get_current_user
from app.core.audit import audit_log
from app.api.endpoints.devices.compensation_schemas import (
    CapacitorBankControlProfileResponse,
    CapacitorBankRemoteCommandRequest,
    CapacitorBankRemoteCommandResponse,
    CapacitorBankControlWriteRequest,
    CapacitorBankControlWriteResponse,
    CapacitorBankTelemetryResponse,
)
from app.core.access_control import ensure_device_access
from app.core.database import get_session
from app.models.tables import CapacitorBankTelemetry, User
from app.services.devices.compensation.capacitor_bank.service import (
    CapacitorBankService,
    ControlProfileWritePreconditionError,
)
from app.domain.device_payloads import resolve_compensation_subtype

router = APIRouter()


@router.get(
    "/{device_id}/compensation/capacitor-bank/telemetry/latest",
    response_model=CapacitorBankTelemetryResponse,
)
def get_device_capacitor_bank_telemetry_latest(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    record = CapacitorBankService.get_latest_telemetry(session, device_id)
    if not record:
        raise HTTPException(status_code=404, detail="暂无遥测数据")
    return record


@router.get(
    "/{device_id}/compensation/capacitor-bank/telemetry",
    response_model=List[CapacitorBankTelemetryResponse],
)
def get_device_capacitor_bank_telemetry_history(
    device_id: int,
    start: Optional[datetime] = Query(None, description="开始时间（ISO 8601）"),
    end: Optional[datetime] = Query(None, description="结束时间（ISO 8601）"),
    limit: int = Query(200, ge=1, le=1000, description="最大返回条数"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(session, current_user, device_id)
    return CapacitorBankService.list_telemetry_history(
        session,
        device_id,
        start_time=start,
        end_time=end,
        limit=limit,
    )


@router.get(
    "/{device_id}/compensation/capacitor-bank/control-profile",
    response_model=CapacitorBankControlProfileResponse,
)
def get_device_capacitor_bank_control_profile(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    device = ensure_device_access(session, current_user, device_id)
    if resolve_compensation_subtype(
        getattr(device, "device_type", None),
        getattr(device, "device_subtype", None),
    ) != "capacitor_bank_controller":
        raise HTTPException(status_code=404, detail="当前设备不是电容补偿控制器")

    profile = CapacitorBankService.get_control_profile(session, device_id)
    source_status = CapacitorBankService.get_profile_source_status(profile)
    payload = {
        "device_id": device_id,
        "source_status": source_status,
        "is_stale": source_status == "stale",
        "capabilities": CapacitorBankService.get_control_capabilities(),
    }
    if profile is not None:
        payload.update(profile.model_dump(exclude={"id", "device_id"}))
    payload.update(CapacitorBankService.build_capacity_expansion_payload(profile))
    return payload


@router.post(
    "/{device_id}/compensation/capacitor-bank/control-profile/write",
    response_model=CapacitorBankControlWriteResponse,
)
def write_device_capacitor_bank_control_profile(
    device_id: int,
    body: CapacitorBankControlWriteRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    device = ensure_device_access(session, current_user, device_id)
    if resolve_compensation_subtype(
        getattr(device, "device_type", None),
        getattr(device, "device_subtype", None),
    ) != "capacitor_bank_controller":
        raise HTTPException(status_code=404, detail="当前设备不是电容补偿控制器")

    try:
        result = CapacitorBankService.submit_control_profile_write(
            session,
            device,
            parameter_key=body.parameter_key,
            target_value=body.target_value,
            operator=current_user.username,
            reason=body.reason,
        )
    except ControlProfileWritePreconditionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_log(
        "device.capacitor_bank.write_parameter",
        current_user.username,
        f"device:{device_id}",
        parameter_key=body.parameter_key,
        target_value=body.target_value,
        command_id=result["command_id"],
        role=current_user.role,
    )
    return result


@router.post(
    "/{device_id}/compensation/capacitor-bank/remote-command",
    response_model=CapacitorBankRemoteCommandResponse,
)
def send_device_capacitor_bank_remote_command(
    device_id: int,
    body: CapacitorBankRemoteCommandRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(OPERATOR_OR_ADMIN),
):
    device = ensure_device_access(session, current_user, device_id)
    if resolve_compensation_subtype(
        getattr(device, "device_type", None),
        getattr(device, "device_subtype", None),
    ) != "capacitor_bank_controller":
        raise HTTPException(status_code=404, detail="当前设备不是电容补偿控制器")

    try:
        result = CapacitorBankService.submit_remote_control_command(
            session,
            device,
            action=body.action,
            operator=current_user.username,
            reason=body.reason,
            command_args={
                key: value
                for key, value in {
                    "manual_mode": body.manual_mode,
                    "phase": body.phase,
                    "switch_action": body.switch_action,
                }.items()
                if value is not None
            } or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_log(
        "device.capacitor_bank.remote_command",
        current_user.username,
        f"device:{device_id}",
        remote_command=body.action,
        command_id=result["command_id"],
        role=current_user.role,
    )
    return result
