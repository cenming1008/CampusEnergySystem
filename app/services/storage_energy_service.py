"""园区级光储实时总览与可复现策略对比。"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlmodel import Session, select

from app.core.settings import settings
from app.domain.storage_control_rules import StorageRuleInput, decide_storage_power
from app.domain.storage_dispatch_optimizer import (
    SLOT_COUNT,
    SLOT_HOURS,
    StorageDispatchInput,
    optimize_storage_dispatch,
)
from app.models.storage import StorageAssetProfile, StorageTelemetry
from app.models.tables import Device, EnergyData
from app.services.devices.storage.dispatch_service import StorageDispatchService


class StorageEnergyService:
    """Keep current aggregation and deterministic strategy replay in one domain service."""

    INPUT_MAX_AGE = timedelta(minutes=5)

    @staticmethod
    def _accessible_devices(
        session: Session,
        *,
        category: str,
        allowed_device_ids: Optional[set[int]],
    ) -> list[Device]:
        statement = select(Device).where(Device.device_category == category)
        if allowed_device_ids is not None:
            if not allowed_device_ids:
                return []
            statement = statement.where(Device.id.in_(allowed_device_ids))
        return list(session.exec(statement.order_by(Device.id)).all())

    @staticmethod
    def _latest_energy_data(session: Session, device_id: int) -> Optional[EnergyData]:
        return session.exec(
            select(EnergyData)
            .where(EnergyData.device_id == device_id)
            .order_by(EnergyData.timestamp.desc())
            .limit(1)
        ).first()

    @staticmethod
    def _latest_telemetry(session: Session, device_id: int) -> Optional[StorageTelemetry]:
        return session.exec(
            select(StorageTelemetry)
            .where(StorageTelemetry.device_id == device_id)
            .order_by(StorageTelemetry.timestamp.desc())
            .limit(1)
        ).first()

    @staticmethod
    def get_overview(
        session: Session,
        *,
        allowed_device_ids: Optional[set[int]],
        device_id: Optional[int] = None,
        now: Optional[datetime] = None,
    ) -> dict:
        storage_devices = StorageEnergyService._accessible_devices(
            session,
            category="storage",
            allowed_device_ids=allowed_device_ids,
        )
        if device_id is not None:
            storage_devices = [device for device in storage_devices if device.id == device_id]
            if not storage_devices:
                raise ValueError("储能设备不存在或不可访问。")

        load_devices = StorageEnergyService._accessible_devices(
            session,
            category="load",
            allowed_device_ids=allowed_device_ids,
        )
        pv_devices = StorageEnergyService._accessible_devices(
            session,
            category="solar",
            allowed_device_ids=allowed_device_ids,
        )
        load_rows = [StorageEnergyService._latest_energy_data(session, device.id) for device in load_devices]
        pv_rows = [StorageEnergyService._latest_energy_data(session, device.id) for device in pv_devices]
        load_kw = sum(max(float(row.flow_rate or 0.0), 0.0) for row in load_rows if row is not None)
        pv_kw = sum(max(float(row.flow_rate or 0.0), 0.0) for row in pv_rows if row is not None)

        storage_kw = 0.0
        weighted_soc = 0.0
        soc_weight = 0.0
        sources: set[str] = set()
        run_ids: set[str] = set()
        execution_total = 0
        execution_matched = 0
        target_storage_kw = 0.0
        strategies: set[str] = set()
        solver_statuses: set[str] = set()
        fallback_reasons: set[str] = set()
        plan_statuses: set[str] = set()
        slot_indexes: set[int] = set()
        plan_timestamps: list[datetime] = []
        storage_timestamps: list[datetime] = []
        current_time = now or datetime.now()
        for device in storage_devices:
            telemetry = StorageEnergyService._latest_telemetry(session, device.id)
            if telemetry is None:
                continue
            storage_kw += float(telemetry.active_power or 0.0)
            storage_timestamps.append(telemetry.timestamp)
            profile = session.get(StorageAssetProfile, device.id)
            weight = float(profile.rated_energy_kwh) if profile is not None else 1.0
            if telemetry.soc is not None:
                weighted_soc += float(telemetry.soc) * weight
                soc_weight += weight
            sources.add(str(telemetry.data_source or "unknown"))
            if telemetry.simulation_run_id:
                run_ids.add(telemetry.simulation_run_id)

            plan = StorageDispatchService.get_current_slot(session, device.id, now=current_time)
            if plan is None:
                target_storage_kw += float(telemetry.target_active_power or 0.0)
                plan_statuses.add("missing")
            else:
                plan_statuses.add("active")
                target_storage_kw += float(plan.target_active_power)
                strategies.add(str(plan.strategy))
                solver_statuses.add(str(plan.solver_status))
                slot_indexes.add(plan.slot_index)
                plan_timestamps.append(plan.generated_at)
                if plan.failure_reason:
                    fallback_reasons.add(plan.failure_reason)
            if plan is not None and telemetry.active_power is not None:
                execution_total += 1
                if abs(float(telemetry.active_power) - float(plan.target_active_power)) <= 5.0:
                    execution_matched += 1

        data_source = next(iter(sources)) if len(sources) == 1 else ("mixed" if sources else "unknown")
        simulation_run_id = next(iter(run_ids)) if len(run_ids) == 1 else None
        soc = round(weighted_soc / soc_weight, 6) if soc_weight else None
        plan_execution_rate = (
            round(execution_matched / execution_total * 100.0, 6) if execution_total else 0.0
        )
        load_timestamps = [row.timestamp for row in load_rows if row is not None]
        pv_timestamps = [row.timestamp for row in pv_rows if row is not None]
        observed_timestamps = load_timestamps + pv_timestamps + storage_timestamps
        missing_input = (
            len(load_rows) != len(load_timestamps)
            or len(pv_rows) != len(pv_timestamps)
            or len(storage_devices) != len(storage_timestamps)
            or not load_devices
            or not pv_devices
            or not storage_devices
        )
        is_stale = missing_input or any(
            current_time - timestamp > StorageEnergyService.INPUT_MAX_AGE
            for timestamp in observed_timestamps
        )
        time_skew_seconds = (
            round((max(observed_timestamps) - min(observed_timestamps)).total_seconds(), 6)
            if observed_timestamps
            else None
        )

        def one_or_mixed(values: set[str]) -> Optional[str]:
            if not values:
                return None
            return next(iter(values)) if len(values) == 1 else "mixed"

        return {
            "current": {
                "load_kw": round(load_kw, 6),
                "pv_kw": round(pv_kw, 6),
                "grid_kw": round(max(load_kw - pv_kw + storage_kw, 0.0), 6),
                "storage_kw": round(storage_kw, 6),
                "soc": soc,
            },
            "storage_device_ids": [device.id for device in storage_devices],
            "data_source": data_source,
            "simulation_run_id": simulation_run_id,
            "plan_execution_rate": plan_execution_rate,
            "dispatch": {
                "actual_power_kw": round(storage_kw, 6),
                "target_power_kw": round(target_storage_kw, 6),
                "deviation_kw": round(storage_kw - target_storage_kw, 6),
                "strategy": one_or_mixed(strategies),
                "plan_status": one_or_mixed(plan_statuses) or "missing",
                "solver_status": one_or_mixed(solver_statuses),
                "fallback_reason": one_or_mixed(fallback_reasons),
                "slot_index": next(iter(slot_indexes)) if len(slot_indexes) == 1 else None,
                "plan_generated_at": max(plan_timestamps) if plan_timestamps else None,
            },
            "provenance": {
                "load_timestamp": min(load_timestamps) if load_timestamps else None,
                "pv_timestamp": min(pv_timestamps) if pv_timestamps else None,
                "storage_timestamp": min(storage_timestamps) if storage_timestamps else None,
                "time_skew_seconds": time_skew_seconds,
                "is_stale": is_stale,
            },
            "timestamp": current_time,
        }

    @staticmethod
    def _bounded_target(
        inputs: StorageDispatchInput,
        requested_kw: float,
        soc: float,
    ) -> tuple[float, float]:
        requested_kw = max(-inputs.max_discharge_kw, min(requested_kw, inputs.max_charge_kw))
        if requested_kw >= 0:
            room_kwh = max(inputs.soc_max - soc, 0.0) / 100.0 * inputs.energy_capacity_kwh
            physical_limit_kw = room_kwh / (inputs.charge_efficiency * SLOT_HOURS)
            applied_kw = min(requested_kw, physical_limit_kw)
            delta_kwh = applied_kw * inputs.charge_efficiency * SLOT_HOURS
        else:
            available_kwh = max(soc - inputs.soc_min, 0.0) / 100.0 * inputs.energy_capacity_kwh
            physical_limit_kw = available_kwh * inputs.discharge_efficiency / SLOT_HOURS
            applied_kw = -min(abs(requested_kw), physical_limit_kw)
            delta_kwh = applied_kw / inputs.discharge_efficiency * SLOT_HOURS
        next_soc = soc + delta_kwh / inputs.energy_capacity_kwh * 100.0
        return round(applied_kw, 9), round(next_soc, 9)

    @staticmethod
    def calculate_metrics(
        inputs: StorageDispatchInput,
        target_power_kw: Sequence[float],
    ) -> dict:
        if len(target_power_kw) != SLOT_COUNT:
            raise ValueError(f"target_power_kw 必须包含 {SLOT_COUNT} 个时段。")
        requested = tuple(float(value) for value in target_power_kw)
        if not all(math.isfinite(value) for value in requested):
            raise ValueError("target_power_kw 必须全部为有限数值。")

        soc = float(inputs.initial_soc)
        grid_import_kwh = 0.0
        grid_export_kwh = 0.0
        energy_cost = 0.0
        curtailment_kwh = 0.0
        throughput_kwh = 0.0
        peak_grid_kw = 0.0
        executed_slots = 0
        for slot_index, requested_kw in enumerate(requested):
            applied_kw, soc = StorageEnergyService._bounded_target(inputs, requested_kw, soc)
            if abs(applied_kw - requested_kw) <= 1e-6:
                executed_slots += 1
            net_grid_kw = inputs.load_kw[slot_index] - inputs.pv_kw[slot_index] + applied_kw
            grid_kw = max(net_grid_kw, 0.0)
            surplus_kw = max(-net_grid_kw, 0.0)
            pv_surplus_kw = max(
                inputs.pv_kw[slot_index] - inputs.load_kw[slot_index] - max(applied_kw, 0.0),
                0.0,
            )
            curtailed_kw = min(surplus_kw, pv_surplus_kw)
            exported_kw = max(surplus_kw - curtailed_kw, 0.0)
            grid_import_kwh += grid_kw * SLOT_HOURS
            grid_export_kwh += exported_kw * SLOT_HOURS
            energy_cost += grid_kw * inputs.tariff_per_kwh[slot_index] * SLOT_HOURS
            curtailment_kwh += curtailed_kw * SLOT_HOURS
            throughput_kwh += abs(applied_kw) * SLOT_HOURS
            peak_grid_kw = max(peak_grid_kw, grid_kw)

        pv_energy_kwh = sum(inputs.pv_kw) * SLOT_HOURS
        self_used_pv_kwh = max(pv_energy_kwh - curtailment_kwh, 0.0)
        pv_self_use_rate = self_used_pv_kwh / pv_energy_kwh * 100.0 if pv_energy_kwh else 0.0
        demand_cost = peak_grid_kw * inputs.demand_charge_per_kw
        degradation_cost = throughput_kwh * inputs.degradation_cost_per_kwh
        curtailment_cost = curtailment_kwh * inputs.curtailment_penalty_per_kwh
        total_cost = energy_cost + demand_cost + degradation_cost + curtailment_cost
        return {
            "grid_import_kwh": round(grid_import_kwh, 6),
            "grid_export_kwh": round(grid_export_kwh, 6),
            "energy_cost": round(energy_cost, 6),
            "demand_cost": round(demand_cost, 6),
            "degradation_cost": round(degradation_cost, 6),
            "curtailment_cost": round(curtailment_cost, 6),
            "cost": round(total_cost, 6),
            "peak_grid_kw": round(peak_grid_kw, 6),
            "pv_self_use_rate": round(pv_self_use_rate, 6),
            "curtailment_kwh": round(curtailment_kwh, 6),
            "throughput_kwh": round(throughput_kwh, 6),
            "equivalent_cycles": round(
                throughput_kwh / (2.0 * inputs.energy_capacity_kwh), 6
            ),
            "terminal_soc": round(soc, 6),
            "plan_execution_rate": None,
            "feasible_slot_rate": round(executed_slots / SLOT_COUNT * 100.0, 6),
        }

    @staticmethod
    def _input_checksum(inputs: StorageDispatchInput) -> str:
        payload = {
            field: getattr(inputs, field)
            for field in inputs.__dataclass_fields__
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _tariff_label(price: float) -> str:
        prices = {
            "peak": float(settings.peak_price),
            "flat": float(settings.flat_price),
            "valley": float(settings.valley_price),
        }
        return min(prices, key=lambda label: abs(prices[label] - price))

    @staticmethod
    def _rule_targets(inputs: StorageDispatchInput) -> tuple[float, ...]:
        soc = float(inputs.initial_soc)
        current_target = 0.0
        previous_nonzero: Optional[float] = None
        targets = []
        for slot_index in range(SLOT_COUNT):
            decision = decide_storage_power(
                StorageRuleInput(
                    load_kw=inputs.load_kw[slot_index],
                    pv_kw=inputs.pv_kw[slot_index],
                    tariff=StorageEnergyService._tariff_label(
                        inputs.tariff_per_kwh[slot_index]
                    ),
                    soc=soc,
                    temperature_c=25.0,
                    bms_state="normal",
                    pcs_state="running",
                    grid_connected=True,
                    available_charge_kw=inputs.max_charge_kw,
                    available_discharge_kw=inputs.max_discharge_kw,
                    current_target_power_kw=current_target,
                    previous_nonzero_target_power_kw=previous_nonzero,
                    seconds_since_last_transition=900.0,
                    soc_charge_stop=inputs.soc_max,
                    soc_charge_resume=max(inputs.soc_min, inputs.soc_max - 5.0),
                    soc_discharge_stop=inputs.soc_min,
                    soc_discharge_resume=min(inputs.soc_max, inputs.soc_min + 5.0),
                )
            )
            applied_target, soc = StorageEnergyService._bounded_target(
                inputs,
                decision.target_power_kw,
                soc,
            )
            if current_target != 0:
                previous_nonzero = current_target
            current_target = applied_target
            targets.append(applied_target)
        return tuple(targets)

    @staticmethod
    def _select_profile(
        session: Session,
        *,
        allowed_device_ids: Optional[set[int]],
        device_id: Optional[int],
    ) -> tuple[Device, StorageAssetProfile]:
        devices = StorageEnergyService._accessible_devices(
            session,
            category="storage",
            allowed_device_ids=allowed_device_ids,
        )
        if device_id is not None:
            devices = [device for device in devices if device.id == device_id]
        if not devices:
            raise ValueError("储能设备不存在或不可访问。")
        device = devices[0]
        profile = session.get(StorageAssetProfile, device.id)
        if profile is None:
            raise ValueError("储能设备尚未配置资产能力档案。")
        return device, profile

    @staticmethod
    def compare_strategies(
        session: Session,
        *,
        scenario_key: str,
        seed: int,
        initial_soc: float,
        allowed_device_ids: Optional[set[int]],
        device_id: Optional[int] = None,
    ) -> dict:
        device, profile = StorageEnergyService._select_profile(
            session,
            allowed_device_ids=allowed_device_ids,
            device_id=device_id,
        )
        inputs = StorageDispatchService.build_scenario_input(
            profile,
            scenario_key=scenario_key,
            seed=seed,
            initial_soc=initial_soc,
        )
        baseline_targets = (0.0,) * SLOT_COUNT
        rule_targets = StorageEnergyService._rule_targets(inputs)
        optimized = optimize_storage_dispatch(inputs)
        day_ahead_targets = tuple(slot.target_active_power_kw for slot in optimized.slots)
        return {
            "device_id": device.id,
            "data_source": "calculated",
            "scenario_key": scenario_key,
            "seed": seed,
            "initial_soc": initial_soc,
            "input_series_checksum": StorageEnergyService._input_checksum(inputs),
            "solver_status": optimized.solver_status,
            "strategies": {
                "baseline": StorageEnergyService.calculate_metrics(inputs, baseline_targets),
                "rule": StorageEnergyService.calculate_metrics(inputs, rule_targets),
                "day_ahead": StorageEnergyService.calculate_metrics(inputs, day_ahead_targets),
            },
        }
