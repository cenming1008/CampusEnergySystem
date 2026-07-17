"""储能资产档案及设备级自动控制授权服务。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Mapping, Optional

from sqlmodel import Session, select

from app.core.exceptions import PermissionDeniedException
from app.models.storage import StorageAssetProfile, StorageTelemetry

AUTO_GATE_TELEMETRY_MAX_AGE = timedelta(minutes=5)
AUTO_GATE_PCS_AVAILABLE_STATES = {"available", "ready", "running", "standby"}


class StorageAssetProfileService:
    """维护人工资产档案，并保护设备级 EMS 自动控制门禁。"""

    @staticmethod
    def get_profile(session: Session, device_id: int) -> Optional[StorageAssetProfile]:
        return session.get(StorageAssetProfile, device_id)

    @staticmethod
    def _latest_telemetry(session: Session, device_id: int) -> Optional[StorageTelemetry]:
        return session.exec(
            select(StorageTelemetry)
            .where(StorageTelemetry.device_id == device_id)
            .order_by(StorageTelemetry.timestamp.desc())
            .limit(1)
        ).first()

    @staticmethod
    def _validate_values(values: Mapping[str, Any]) -> None:
        rated_energy = float(values["rated_energy_kwh"])
        rated_power = float(values["rated_power_kw"])
        if rated_energy <= 0 or rated_power <= 0:
            raise ValueError("额定能量和额定功率必须大于 0。")
        for field in ("max_charge_power_kw", "max_discharge_power_kw"):
            value = values.get(field)
            if value is not None and float(value) < 0:
                raise ValueError(f"{field} 不能小于 0。")
            if value is not None and float(value) > rated_power:
                raise ValueError(f"{field} 不能超过 PCS 额定功率。")
        for field in ("charge_efficiency", "discharge_efficiency"):
            value = float(values.get(field, 0.95))
            if not 0 < value <= 1:
                raise ValueError(f"{field} 必须在 (0, 1] 范围内。")
        soc_min = float(values.get("soc_min", 10.0))
        soc_max = float(values.get("soc_max", 90.0))
        soft_min = float(values.get("soc_soft_min", 15.0))
        soft_max = float(values.get("soc_soft_max", 85.0))
        if not 0 <= soc_min < soft_min <= soft_max < soc_max <= 100:
            raise ValueError("SOC 硬边界与软边界顺序无效。")

    @staticmethod
    def _validate_auto_enable(session: Session, device_id: int, now: datetime) -> None:
        telemetry = StorageAssetProfileService._latest_telemetry(session, device_id)
        if telemetry is None:
            raise ValueError("缺少储能实时遥测，不能启用自动控制。")
        if now - telemetry.timestamp > AUTO_GATE_TELEMETRY_MAX_AGE:
            raise ValueError("储能遥测已过期，不能启用自动控制。")
        if str(telemetry.bms_status or "").lower() != "normal":
            raise ValueError("BMS 状态不是 normal，不能启用自动控制。")
        if str(telemetry.pcs_status or "").lower() not in AUTO_GATE_PCS_AVAILABLE_STATES:
            raise ValueError("PCS 当前不可用，不能启用自动控制。")
        if str(telemetry.grid_status or "").lower() != "connected":
            raise ValueError("储能设备未并网，不能启用自动控制。")

    @staticmethod
    def upsert_profile(
        session: Session,
        device_id: int,
        values: Mapping[str, Any],
        *,
        allow_auto_gate_update: bool,
        now: Optional[datetime] = None,
    ) -> StorageAssetProfile:
        normalized = dict(values)
        StorageAssetProfileService._validate_values(normalized)
        existing = StorageAssetProfileService.get_profile(session, device_id)
        requested_auto = bool(normalized.get("ems_auto_enabled", False))
        current_auto = bool(existing.ems_auto_enabled) if existing else False

        if existing is None and requested_auto:
            raise ValueError("请先保存储能资产档案，再启用 EMS 自动控制。")
        if requested_auto != current_auto:
            if not allow_auto_gate_update:
                raise PermissionDeniedException("只有管理员可以修改设备级 EMS 自动控制授权")
            if requested_auto:
                StorageAssetProfileService._validate_auto_enable(
                    session,
                    device_id,
                    now or datetime.now(),
                )

        if existing is None:
            profile = StorageAssetProfile(device_id=device_id, **normalized)
        else:
            profile = existing
            for field, value in normalized.items():
                setattr(profile, field, value)
            profile.updated_at = now or datetime.now()

        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile
