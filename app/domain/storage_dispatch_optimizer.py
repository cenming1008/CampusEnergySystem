"""Pure 96-slot day-ahead MILP optimizer for battery storage dispatch."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence, Tuple

import pulp

SLOT_COUNT = 96
SLOT_HOURS = 0.25


class DispatchOptimizationError(RuntimeError):
    """Raised when the dispatch model does not produce an optimal solution."""

    def __init__(self, solver_status: str) -> None:
        self.solver_status = solver_status
        super().__init__(f"Storage dispatch optimization failed: {solver_status}")


@dataclass(frozen=True)
class StorageDispatchInput:
    load_kw: Tuple[float, ...]
    pv_kw: Tuple[float, ...]
    tariff_per_kwh: Tuple[float, ...]
    energy_capacity_kwh: float
    max_charge_kw: float
    max_discharge_kw: float
    initial_soc: float
    terminal_soc_target: float
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    soc_min: float = 15.0
    soc_max: float = 85.0
    demand_charge_per_kw: float = 0.0
    degradation_cost_per_kwh: float = 0.0
    curtailment_penalty_per_kwh: float = 0.0


@dataclass(frozen=True)
class StorageDispatchSlot:
    slot_index: int
    charge_kw: float
    discharge_kw: float
    target_active_power_kw: float
    grid_kw: float
    soc: float
    curtailment_kw: float


@dataclass(frozen=True)
class StorageDispatchResult:
    solver_status: str
    slots: Tuple[StorageDispatchSlot, ...]
    total_cost: float
    peak_grid_kw: float
    total_curtailment_kwh: float
    terminal_soc: float
    baseline_peak_grid_kw: float


def _require_finite(name: str, value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def _validate_series(name: str, values: Sequence[float]) -> Tuple[float, ...]:
    if len(values) != SLOT_COUNT:
        raise ValueError(f"{name} must contain exactly {SLOT_COUNT} slots")
    result = tuple(_require_finite(name, value) for value in values)
    if name in {"load_kw", "pv_kw"} and any(value < 0 for value in result):
        raise ValueError(f"{name} must contain only non-negative values")
    return result


def _validate_inputs(inputs: StorageDispatchInput) -> tuple[
    Tuple[float, ...], Tuple[float, ...], Tuple[float, ...]
]:
    load_kw = _validate_series("load_kw", inputs.load_kw)
    pv_kw = _validate_series("pv_kw", inputs.pv_kw)
    tariff = _validate_series("tariff_per_kwh", inputs.tariff_per_kwh)

    positive_fields = (
        "energy_capacity_kwh",
        "max_charge_kw",
        "max_discharge_kw",
    )
    for name in positive_fields:
        if _require_finite(name, getattr(inputs, name)) <= 0:
            raise ValueError(f"{name} must be greater than zero")

    for name in (
        "demand_charge_per_kw",
        "degradation_cost_per_kwh",
        "curtailment_penalty_per_kwh",
    ):
        if _require_finite(name, getattr(inputs, name)) < 0:
            raise ValueError(f"{name} must be non-negative")

    for name in ("charge_efficiency", "discharge_efficiency"):
        efficiency = _require_finite(name, getattr(inputs, name))
        if not 0 < efficiency <= 1:
            raise ValueError(f"{name} must be in (0, 1]")

    soc_min = _require_finite("soc_min", inputs.soc_min)
    soc_max = _require_finite("soc_max", inputs.soc_max)
    if not 0 <= soc_min < soc_max <= 100:
        raise ValueError("SOC limits must satisfy 0 <= soc_min < soc_max <= 100")
    initial_soc = _require_finite("initial_soc", inputs.initial_soc)
    if not soc_min <= initial_soc <= soc_max:
        raise ValueError("initial_soc must be within the configured SOC range")
    terminal_soc = _require_finite(
        "terminal_soc_target", inputs.terminal_soc_target
    )
    if not soc_min <= terminal_soc <= soc_max:
        raise ValueError("terminal_soc_target must be within the configured SOC range")
    return load_kw, pv_kw, tariff


def _rounded(value: object) -> float:
    number = pulp.value(value)
    if number is None:
        raise DispatchOptimizationError("MissingSolutionValue")
    rounded = round(float(number), 6)
    return 0.0 if rounded == -0.0 else rounded


def optimize_storage_dispatch(inputs: StorageDispatchInput) -> StorageDispatchResult:
    """Minimize daily energy, demand, degradation, and PV-curtailment costs."""
    load_kw, pv_kw, tariff = _validate_inputs(inputs)
    slots = range(SLOT_COUNT)
    model = pulp.LpProblem("storage_day_ahead_dispatch", pulp.LpMinimize)

    charge_kw = pulp.LpVariable.dicts(
        "charge_kw", slots, lowBound=0, upBound=inputs.max_charge_kw
    )
    discharge_kw = pulp.LpVariable.dicts(
        "discharge_kw", slots, lowBound=0, upBound=inputs.max_discharge_kw
    )
    grid_kw = pulp.LpVariable.dicts("grid_kw", slots, lowBound=0)
    curtail_kw = pulp.LpVariable.dicts("curtail_kw", slots, lowBound=0)
    is_charging = pulp.LpVariable.dicts("is_charging", slots, cat="Binary")
    is_discharging = pulp.LpVariable.dicts("is_discharging", slots, cat="Binary")
    soc = pulp.LpVariable.dicts(
        "soc", range(SLOT_COUNT + 1), lowBound=inputs.soc_min, upBound=inputs.soc_max
    )
    peak_grid_kw = pulp.LpVariable("peak_grid_kw", lowBound=0)

    model += soc[0] == inputs.initial_soc
    for slot in slots:
        model += charge_kw[slot] <= inputs.max_charge_kw * is_charging[slot]
        model += discharge_kw[slot] <= inputs.max_discharge_kw * is_discharging[slot]
        model += is_charging[slot] + is_discharging[slot] <= 1
        model += curtail_kw[slot] <= pv_kw[slot]
        model += (
            grid_kw[slot]
            == load_kw[slot]
            - pv_kw[slot]
            + curtail_kw[slot]
            + charge_kw[slot]
            - discharge_kw[slot]
        )
        model += peak_grid_kw >= grid_kw[slot]
        model += soc[slot + 1] == soc[slot] + (
            charge_kw[slot] * inputs.charge_efficiency
            - discharge_kw[slot] / inputs.discharge_efficiency
        ) * SLOT_HOURS / inputs.energy_capacity_kwh * 100.0
    model += soc[SLOT_COUNT] == inputs.terminal_soc_target

    energy_cost = pulp.lpSum(
        grid_kw[slot] * tariff[slot] * SLOT_HOURS for slot in slots
    )
    demand_cost = peak_grid_kw * inputs.demand_charge_per_kw
    degradation_cost = pulp.lpSum(
        (charge_kw[slot] + discharge_kw[slot])
        * inputs.degradation_cost_per_kwh
        * SLOT_HOURS
        for slot in slots
    )
    curtailment_cost = pulp.lpSum(
        curtail_kw[slot] * inputs.curtailment_penalty_per_kwh * SLOT_HOURS
        for slot in slots
    )
    model += energy_cost + demand_cost + degradation_cost + curtailment_cost

    try:
        status_code = model.solve(
            pulp.PULP_CBC_CMD(msg=False, threads=1, options=["randomSeed 1"])
        )
    except pulp.PulpSolverError as exc:
        raise DispatchOptimizationError("SolverError") from exc
    solver_status = pulp.LpStatus.get(status_code, str(status_code))
    if solver_status != "Optimal":
        raise DispatchOptimizationError(solver_status)

    dispatch_slots = tuple(
        StorageDispatchSlot(
            slot_index=slot,
            charge_kw=_rounded(charge_kw[slot]),
            discharge_kw=_rounded(discharge_kw[slot]),
            target_active_power_kw=_rounded(charge_kw[slot] - discharge_kw[slot]),
            grid_kw=_rounded(grid_kw[slot]),
            soc=_rounded(soc[slot + 1]),
            curtailment_kw=_rounded(curtail_kw[slot]),
        )
        for slot in slots
    )
    baseline_peak_grid_kw = round(
        max(max(load - pv, 0.0) for load, pv in zip(load_kw, pv_kw)), 6
    )
    return StorageDispatchResult(
        solver_status=solver_status,
        slots=dispatch_slots,
        total_cost=_rounded(model.objective),
        peak_grid_kw=_rounded(peak_grid_kw),
        total_curtailment_kwh=round(
            sum(slot.curtailment_kw for slot in dispatch_slots) * SLOT_HOURS, 6
        ),
        terminal_soc=_rounded(soc[SLOT_COUNT]),
        baseline_peak_grid_kw=baseline_peak_grid_kw,
    )
