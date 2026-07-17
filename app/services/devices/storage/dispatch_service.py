"""Storage day-ahead plan generation, persistence, and lookup."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Callable, Optional, Tuple

from sqlalchemy import delete
from sqlmodel import Session, select

from app.core.settings import settings
from app.domain.energy_rules import is_hour_in_ranges, parse_hour_ranges
from app.domain.storage_dispatch_optimizer import (
    DispatchOptimizationError,
    StorageDispatchInput,
    StorageDispatchResult,
    optimize_storage_dispatch,
)
from app.models.storage import StorageAssetProfile, StorageDispatchPlan, StorageTelemetry

OptimizeDispatch = Callable[[StorageDispatchInput], StorageDispatchResult]
SCENARIO_KEYS = {
    "sunny_workday",
    "cloudy_workday",
    "weekend_low_load",
    "pv_surplus",
    "evening_peak",
}


@dataclass(frozen=True)
class DispatchPlanGenerationResult:
    status: str
    solver_status: str
    dispatch_date: date
    plans: Tuple[StorageDispatchPlan, ...] = ()
    failure_reason: Optional[str] = None


class StorageDispatchService:
    """Generate complete plans before atomically replacing one device-day version."""

    STRATEGY_VERSION = "v1.0.0"

    @staticmethod
    def generate_plan(
        session: Session,
        *,
        device_id: int,
        dispatch_date: date,
        optimizer_input: StorageDispatchInput,
        data_source: str = "calculated",
        simulation_run_id: Optional[str] = None,
        optimizer: OptimizeDispatch = optimize_storage_dispatch,
        generated_at: Optional[datetime] = None,
    ) -> DispatchPlanGenerationResult:
        if data_source not in {"calculated", "simulated", "real"}:
            raise ValueError("data_source 仅支持 calculated/simulated/real。")
        if data_source == "simulated" and not simulation_run_id:
            raise ValueError("simulated 计划必须携带 simulation_run_id。")
        if data_source != "simulated" and simulation_run_id is not None:
            raise ValueError("只有 simulated 计划可以携带 simulation_run_id。")

        try:
            optimized = optimizer(optimizer_input)
        except DispatchOptimizationError as exc:
            return DispatchPlanGenerationResult(
                status="failed",
                solver_status=exc.solver_status,
                dispatch_date=dispatch_date,
                failure_reason=str(exc),
            )
        if len(optimized.slots) != 96:
            raise ValueError("优化器必须返回完整 96 时段结果。")

        timestamp = generated_at or datetime.now()
        new_plans = tuple(
            StorageDispatchPlan(
                device_id=device_id,
                dispatch_date=dispatch_date,
                slot_index=slot.slot_index,
                target_active_power=slot.target_active_power_kw,
                forecast_load_power=optimizer_input.load_kw[slot.slot_index],
                forecast_pv_power=optimizer_input.pv_kw[slot.slot_index],
                tariff_price=optimizer_input.tariff_per_kwh[slot.slot_index],
                expected_soc=slot.soc,
                strategy="day_ahead",
                strategy_version=StorageDispatchService.STRATEGY_VERSION,
                solver_status=optimized.solver_status,
                is_valid=True,
                generated_at=timestamp,
                data_source=data_source,
                simulation_run_id=simulation_run_id,
            )
            for slot in optimized.slots
        )

        try:
            session.exec(
                delete(StorageDispatchPlan)
                .where(StorageDispatchPlan.device_id == device_id)
                .where(StorageDispatchPlan.dispatch_date == dispatch_date)
            )
            session.add_all(new_plans)
            session.commit()
        except Exception:
            session.rollback()
            raise
        return DispatchPlanGenerationResult(
            status="optimal",
            solver_status=optimized.solver_status,
            dispatch_date=dispatch_date,
            plans=new_plans,
        )

    @staticmethod
    def get_current_plan(
        session: Session,
        device_id: int,
        dispatch_date: date,
    ) -> list[StorageDispatchPlan]:
        return list(
            session.exec(
                select(StorageDispatchPlan)
                .where(StorageDispatchPlan.device_id == device_id)
                .where(StorageDispatchPlan.dispatch_date == dispatch_date)
                .where(StorageDispatchPlan.is_valid.is_(True))
                .order_by(StorageDispatchPlan.slot_index)
            ).all()
        )

    @staticmethod
    def get_current_slot(
        session: Session,
        device_id: int,
        *,
        now: Optional[datetime] = None,
    ) -> Optional[StorageDispatchPlan]:
        current = now or datetime.now()
        slot_index = current.hour * 4 + current.minute // 15
        return session.exec(
            select(StorageDispatchPlan)
            .where(StorageDispatchPlan.device_id == device_id)
            .where(StorageDispatchPlan.dispatch_date == current.date())
            .where(StorageDispatchPlan.slot_index == slot_index)
            .where(StorageDispatchPlan.is_valid.is_(True))
            .limit(1)
        ).first()

    @staticmethod
    def get_solver_status(session: Session, device_id: int, dispatch_date: date) -> dict:
        plan = session.exec(
            select(StorageDispatchPlan)
            .where(StorageDispatchPlan.device_id == device_id)
            .where(StorageDispatchPlan.dispatch_date == dispatch_date)
            .order_by(StorageDispatchPlan.generated_at.desc())
            .limit(1)
        ).first()
        if plan is None:
            return {
                "status": "missing",
                "solver_status": None,
                "dispatch_date": dispatch_date,
                "failure_reason": None,
            }
        return {
            "status": "optimal" if plan.is_valid and plan.solver_status == "Optimal" else "failed",
            "solver_status": plan.solver_status,
            "dispatch_date": dispatch_date,
            "failure_reason": plan.failure_reason,
            "generated_at": plan.generated_at,
        }

    @staticmethod
    def _tariff_series() -> Tuple[float, ...]:
        peak_ranges = parse_hour_ranges(settings.electricity_peak_hours)
        flat_ranges = parse_hour_ranges(settings.electricity_flat_hours)
        prices = []
        for slot in range(96):
            hour = slot // 4
            if is_hour_in_ranges(hour, peak_ranges):
                prices.append(float(settings.peak_price))
            elif is_hour_in_ranges(hour, flat_ranges):
                prices.append(float(settings.flat_price))
            else:
                prices.append(float(settings.valley_price))
        return tuple(prices)

    @staticmethod
    def build_scenario_input(
        profile: StorageAssetProfile,
        *,
        scenario_key: str,
        seed: int,
        initial_soc: float,
        terminal_soc_target: Optional[float] = None,
    ) -> StorageDispatchInput:
        if scenario_key not in SCENARIO_KEYS:
            raise ValueError(f"未知储能场景 `{scenario_key}`。")
        rng = random.Random(seed)
        rated_power = float(profile.rated_power_kw)
        load_values = []
        pv_values = []
        for slot in range(96):
            hour = slot / 4
            workday = scenario_key != "weekend_low_load"
            base_load = rated_power * (1.15 if workday else 0.65)
            evening_factor = 0.65 if 17 <= hour < 21 else 0.0
            if scenario_key == "evening_peak":
                evening_factor = 1.0 if 17 <= hour < 21 else 0.0
            load = base_load + rated_power * evening_factor + rng.uniform(-2.0, 2.0)

            daylight = max(math.sin(math.pi * (hour - 6) / 12), 0.0)
            pv_factor = {
                "sunny_workday": 1.8,
                "cloudy_workday": 0.8,
                "weekend_low_load": 1.2,
                "pv_surplus": 2.4,
                "evening_peak": 1.1,
            }[scenario_key]
            pv = rated_power * pv_factor * daylight
            load_values.append(max(round(load, 6), 0.0))
            pv_values.append(round(pv, 6))

        max_charge = profile.max_charge_power_kw or profile.rated_power_kw
        max_discharge = profile.max_discharge_power_kw or profile.rated_power_kw
        return StorageDispatchInput(
            load_kw=tuple(load_values),
            pv_kw=tuple(pv_values),
            tariff_per_kwh=StorageDispatchService._tariff_series(),
            energy_capacity_kwh=profile.rated_energy_kwh,
            max_charge_kw=max_charge,
            max_discharge_kw=max_discharge,
            initial_soc=initial_soc,
            terminal_soc_target=(
                initial_soc if terminal_soc_target is None else terminal_soc_target
            ),
            charge_efficiency=profile.charge_efficiency,
            discharge_efficiency=profile.discharge_efficiency,
            soc_min=profile.soc_soft_min,
            soc_max=profile.soc_soft_max,
            demand_charge_per_kw=10.0,
            degradation_cost_per_kwh=0.01,
            curtailment_penalty_per_kwh=0.2,
        )

    @staticmethod
    def generate_scenario_plan(
        session: Session,
        *,
        device_id: int,
        dispatch_date: date,
        scenario_key: str,
        seed: int,
        initial_soc: float,
        terminal_soc_target: Optional[float] = None,
    ) -> DispatchPlanGenerationResult:
        profile = session.get(StorageAssetProfile, device_id)
        if profile is None:
            raise ValueError("储能设备缺少资产档案，无法生成日前计划。")
        telemetry = session.exec(
            select(StorageTelemetry)
            .where(StorageTelemetry.device_id == device_id)
            .order_by(StorageTelemetry.timestamp.desc())
            .limit(1)
        ).first()
        optimizer_input = StorageDispatchService.build_scenario_input(
            profile,
            scenario_key=scenario_key,
            seed=seed,
            initial_soc=initial_soc,
            terminal_soc_target=terminal_soc_target,
        )
        return StorageDispatchService.generate_plan(
            session,
            device_id=device_id,
            dispatch_date=dispatch_date,
            optimizer_input=optimizer_input,
            data_source="simulated",
            simulation_run_id=getattr(telemetry, "simulation_run_id", None),
        )

    @staticmethod
    def generate_daily_plans(
        session: Session,
        *,
        now: Optional[datetime] = None,
    ) -> list[dict]:
        current = now or datetime.now()
        dispatch_date = current.date() + timedelta(days=1)
        profiles = list(
            session.exec(
                select(StorageAssetProfile).where(
                    StorageAssetProfile.ems_auto_enabled.is_(True)
                )
            ).all()
        )
        results = []
        for profile in profiles:
            telemetry = session.exec(
                select(StorageTelemetry)
                .where(StorageTelemetry.device_id == profile.device_id)
                .order_by(StorageTelemetry.timestamp.desc())
                .limit(1)
            ).first()
            if telemetry is None or telemetry.soc is None:
                results.append(
                    {"device_id": profile.device_id, "status": "failed", "reason": "missing_telemetry"}
                )
                continue
            optimizer_input = StorageDispatchService.build_scenario_input(
                profile,
                scenario_key="sunny_workday",
                seed=int(dispatch_date.strftime("%Y%m%d")),
                initial_soc=float(telemetry.soc),
            )
            generated = StorageDispatchService.generate_plan(
                session,
                device_id=profile.device_id,
                dispatch_date=dispatch_date,
                optimizer_input=optimizer_input,
                data_source="calculated",
            )
            results.append(
                {
                    "device_id": profile.device_id,
                    "status": generated.status,
                    "solver_status": generated.solver_status,
                }
            )
        return results
