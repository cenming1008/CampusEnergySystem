"""储能实时 EMS 编排服务。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Optional

from sqlmodel import Session, select

from app.core.settings import settings
from app.domain.energy_rules import is_hour_in_ranges, parse_hour_ranges
from app.domain.storage_control_rules import (
    StorageRuleDecision,
    StorageRuleInput,
    decide_storage_power,
)
from app.models.storage import StorageAssetProfile, StorageTelemetry
from app.models.tables import Device, DeviceControlLog, EnergyData
from app.services.devices.storage.control_command_service import StorageControlCommandService
from app.services.devices.storage.dispatch_service import StorageDispatchService
from app.services.devices.storage.specs import CONTROL_COMMAND_SOURCE, PENDING_RESULTS


@dataclass(frozen=True)
class StorageCampusInputs:
    load_kw: float
    pv_kw: float
    tariff: str = "flat"
    demand_limit_kw: Optional[float] = None


CampusInputProvider = Callable[..., StorageCampusInputs]
QueueCommand = Callable[..., dict]


class StorageEmsService:
    """读取统一储能状态，经过纯规则后复用控制命令状态机。"""

    TARGET_DEADBAND_KW = 5.0
    TELEMETRY_MAX_AGE = timedelta(minutes=5)
    PLAN_SAFETY_REASONS = {"soc_protection", "temperature_derate", "device_fault"}

    @staticmethod
    def get_latest_telemetry(session: Session, device_id: int) -> Optional[StorageTelemetry]:
        return session.exec(
            select(StorageTelemetry)
            .where(StorageTelemetry.device_id == device_id)
            .order_by(StorageTelemetry.timestamp.desc())
            .limit(1)
        ).first()

    @staticmethod
    def _has_pending_command(session: Session, device_id: int) -> bool:
        log = session.exec(
            select(DeviceControlLog)
            .where(DeviceControlLog.device_id == device_id)
            .where(DeviceControlLog.command_source == CONTROL_COMMAND_SOURCE)
            .where(DeviceControlLog.result.in_(tuple(PENDING_RESULTS)))
            .limit(1)
        ).first()
        return log is not None

    @staticmethod
    def _tariff_for_time(now: datetime) -> str:
        if is_hour_in_ranges(now.hour, parse_hour_ranges(settings.electricity_peak_hours)):
            return "peak"
        if is_hour_in_ranges(now.hour, parse_hour_ranges(settings.electricity_flat_hours)):
            return "flat"
        return "valley"

    @staticmethod
    def load_campus_inputs(session: Session, now: Optional[datetime] = None) -> StorageCampusInputs:
        totals = {"load": 0.0, "solar": 0.0}
        devices = list(
            session.exec(select(Device).where(Device.device_category.in_(("load", "solar")))).all()
        )
        for device in devices:
            latest = session.exec(
                select(EnergyData)
                .where(EnergyData.device_id == device.id)
                .order_by(EnergyData.timestamp.desc())
                .limit(1)
            ).first()
            if latest is not None and latest.flow_rate is not None:
                totals[str(device.device_category)] += max(float(latest.flow_rate), 0.0)
        current_time = now or datetime.now()
        return StorageCampusInputs(
            load_kw=totals["load"],
            pv_kw=totals["solar"],
            tariff=StorageEmsService._tariff_for_time(current_time),
        )

    @staticmethod
    def _transition_context(
        session: Session,
        device_id: int,
        current_target: float,
        now: datetime,
    ) -> tuple[Optional[float], Optional[float]]:
        records = list(
            session.exec(
                select(StorageTelemetry)
                .where(StorageTelemetry.device_id == device_id)
                .order_by(StorageTelemetry.timestamp.desc())
                .limit(100)
            ).all()
        )
        if len(records) < 2:
            return None, None

        transition_time = records[0].timestamp
        previous_nonzero: Optional[float] = None
        for record in records[1:]:
            target = float(record.target_active_power or 0.0)
            if target == current_target:
                transition_time = record.timestamp
                continue
            if target != 0:
                previous_nonzero = target
            break
        elapsed = max((now - transition_time).total_seconds(), 0.0)
        return previous_nonzero, elapsed

    @staticmethod
    def _build_rule_input(
        telemetry: StorageTelemetry,
        profile: StorageAssetProfile,
        campus: StorageCampusInputs,
        previous_nonzero: Optional[float],
        elapsed: Optional[float],
    ) -> StorageRuleInput:
        current_target = float(telemetry.target_active_power or 0.0)
        return StorageRuleInput(
            load_kw=campus.load_kw,
            pv_kw=campus.pv_kw,
            tariff=campus.tariff,
            demand_limit_kw=campus.demand_limit_kw,
            soc=float(telemetry.soc or 0.0),
            temperature_c=float(telemetry.cell_temp_max or telemetry.cell_temp_avg or 0.0),
            bms_state=str(telemetry.bms_status or "unknown"),
            pcs_state=str(telemetry.pcs_status or "unknown"),
            grid_connected=str(telemetry.grid_status or "").lower() == "connected",
            available_charge_kw=float(
                telemetry.available_charge_power
                if telemetry.available_charge_power is not None
                else (
                    profile.max_charge_power_kw
                    if profile.max_charge_power_kw is not None
                    else profile.rated_power_kw
                )
            ),
            available_discharge_kw=float(
                telemetry.available_discharge_power
                if telemetry.available_discharge_power is not None
                else (
                    profile.max_discharge_power_kw
                    if profile.max_discharge_power_kw is not None
                    else profile.rated_power_kw
                )
            ),
            current_target_power_kw=current_target,
            previous_nonzero_target_power_kw=previous_nonzero,
            seconds_since_last_transition=elapsed,
        )

    @staticmethod
    def _apply_plan_safety(
        telemetry: StorageTelemetry,
        profile: StorageAssetProfile,
        target_power_kw: float,
    ) -> StorageRuleDecision:
        if (
            str(telemetry.bms_status or "").lower() != "normal"
            or str(telemetry.pcs_status or "").lower()
            not in {"available", "ready", "running", "standby"}
            or str(telemetry.grid_status or "").lower() != "connected"
        ):
            return StorageRuleDecision(0.0, "device_fault")
        temperature = float(telemetry.cell_temp_max or telemetry.cell_temp_avg or 0.0)
        if temperature >= 55.0:
            return StorageRuleDecision(0.0, "temperature_derate")
        soc = float(telemetry.soc or 0.0)
        if (target_power_kw > 0 and soc >= profile.soc_soft_max) or (
            target_power_kw < 0 and soc <= profile.soc_soft_min
        ):
            return StorageRuleDecision(0.0, "soc_protection")

        if target_power_kw >= 0:
            limit = float(
                telemetry.available_charge_power
                if telemetry.available_charge_power is not None
                else profile.max_charge_power_kw or profile.rated_power_kw
            )
            bounded_target = min(target_power_kw, max(limit, 0.0))
        else:
            limit = float(
                telemetry.available_discharge_power
                if telemetry.available_discharge_power is not None
                else profile.max_discharge_power_kw or profile.rated_power_kw
            )
            bounded_target = -min(abs(target_power_kw), max(limit, 0.0))
        actual_power = float(telemetry.active_power or 0.0)
        reason = (
            "forecast_deviation"
            if bounded_target != target_power_kw
            or abs(actual_power - bounded_target) > StorageEmsService.TARGET_DEADBAND_KW
            else "day_ahead_plan"
        )
        return StorageRuleDecision(bounded_target, reason)

    @staticmethod
    def evaluate_device(
        session: Session,
        device: Device,
        *,
        campus_input_provider: CampusInputProvider | None = None,
        ems_enabled: Optional[bool] = None,
        queue_command: QueueCommand | None = None,
        now: Optional[datetime] = None,
    ) -> dict:
        enabled = settings.storage_ems_enabled if ems_enabled is None else ems_enabled
        if not enabled:
            return {"status": "skipped", "reason": "global_gate_disabled", "device_id": device.id}

        profile = session.get(StorageAssetProfile, device.id)
        if profile is None or not profile.ems_auto_enabled:
            return {"status": "skipped", "reason": "device_gate_disabled", "device_id": device.id}

        telemetry = StorageEmsService.get_latest_telemetry(session, device.id)
        if telemetry is None:
            return {"status": "skipped", "reason": "missing_telemetry", "device_id": device.id}
        current_time = now or datetime.now()
        if current_time - telemetry.timestamp > StorageEmsService.TELEMETRY_MAX_AGE:
            return {
                "status": "skipped",
                "reason": "stale_telemetry",
                "deviation_reason": "communication_loss",
                "device_id": device.id,
            }
        if str(telemetry.control_mode or "").lower() != "auto":
            return {
                "status": "skipped",
                "reason": "manual_mode",
                "deviation_reason": "manual_takeover",
                "device_id": device.id,
            }
        temperature = (
            telemetry.cell_temp_max
            if telemetry.cell_temp_max is not None
            else telemetry.cell_temp_avg
        )
        if (
            telemetry.soc is None
            or temperature is None
            or not telemetry.bms_status
            or not telemetry.pcs_status
            or not telemetry.grid_status
        ):
            return {"status": "skipped", "reason": "incomplete_telemetry", "device_id": device.id}
        if StorageEmsService._has_pending_command(session, device.id):
            return {"status": "skipped", "reason": "pending_command", "device_id": device.id}

        current_target = float(telemetry.target_active_power or 0.0)
        plan_slot = StorageDispatchService.get_current_slot(
            session,
            device.id,
            now=current_time,
        )
        fallback_reason: Optional[str] = None
        if plan_slot is not None:
            decision = StorageEmsService._apply_plan_safety(
                telemetry,
                profile,
                float(plan_slot.target_active_power),
            )
            command_source = "day_ahead"
        else:
            fallback_reason = "expired_or_missing_plan"
            provider = campus_input_provider or StorageEmsService.load_campus_inputs
            campus = provider(session, current_time)
            previous_nonzero, elapsed = StorageEmsService._transition_context(
                session,
                device.id,
                current_target,
                current_time,
            )
            decision = decide_storage_power(
                StorageEmsService._build_rule_input(
                    telemetry,
                    profile,
                    campus,
                    previous_nonzero,
                    elapsed,
                )
            )
            command_source = "rule"
        if abs(decision.target_power_kw - current_target) <= StorageEmsService.TARGET_DEADBAND_KW:
            return {
                "status": "skipped",
                "reason": "target_deadband",
                "device_id": device.id,
                "decision": decision,
                "plan_slot": plan_slot.slot_index if plan_slot is not None else None,
                "fallback_reason": fallback_reason,
            }

        command = (
            "stop"
            if decision.target_power_kw == 0
            and (
                decision.reason_code.startswith("safety_")
                or decision.reason_code in StorageEmsService.PLAN_SAFETY_REASONS
            )
            else "set_active_power"
        )
        queue = queue_command or StorageControlCommandService.queue_command
        result = queue(
            session,
            device,
            command=command,
            operator="storage-ems",
            source=command_source,
            target_active_power=decision.target_power_kw if command == "set_active_power" else None,
            reason=decision.reason_code,
        )
        return {
            "status": "queued",
            "reason": decision.reason_code,
            "device_id": device.id,
            "decision": decision,
            "command": result,
            "plan_slot": plan_slot.slot_index if plan_slot is not None else None,
            "fallback_reason": fallback_reason,
        }

    @staticmethod
    def evaluate_all(
        session: Session,
        *,
        campus_input_provider: CampusInputProvider | None = None,
        ems_enabled: Optional[bool] = None,
    ) -> list[dict]:
        enabled = settings.storage_ems_enabled if ems_enabled is None else ems_enabled
        if not enabled:
            return []
        profiles = list(
            session.exec(
                select(StorageAssetProfile).where(StorageAssetProfile.ems_auto_enabled.is_(True))
            ).all()
        )
        results: list[dict] = []
        for profile in profiles:
            device = session.get(Device, profile.device_id)
            if device is None:
                continue
            try:
                results.append(
                    StorageEmsService.evaluate_device(
                        session,
                        device,
                        campus_input_provider=campus_input_provider,
                        ems_enabled=True,
                    )
                )
            except Exception as exc:
                session.rollback()
                results.append(
                    {
                        "status": "failed",
                        "reason": "evaluation_error",
                        "device_id": device.id,
                        "detail": str(exc),
                    }
                )
        return results
