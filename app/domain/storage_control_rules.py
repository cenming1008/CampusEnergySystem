"""储能安全优先实时控制纯规则。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StorageRuleInput:
    load_kw: float = 0.0
    pv_kw: float = 0.0
    tariff: str = "flat"
    demand_limit_kw: Optional[float] = None
    soc: float = 50.0
    temperature_c: float = 25.0
    bms_state: str = "normal"
    pcs_state: str = "running"
    grid_connected: bool = True
    available_charge_kw: float = 0.0
    available_discharge_kw: float = 0.0
    current_target_power_kw: float = 0.0
    previous_nonzero_target_power_kw: Optional[float] = None
    seconds_since_last_transition: Optional[float] = None
    deadband_kw: float = 5.0
    minimum_run_seconds: float = 120.0
    minimum_stop_seconds: float = 60.0
    direction_change_standby_seconds: float = 60.0
    soc_charge_stop: float = 90.0
    soc_charge_resume: float = 85.0
    soc_discharge_stop: float = 10.0
    soc_discharge_resume: float = 15.0
    temperature_stop_c: float = 55.0
    temperature_resume_c: float = 50.0


@dataclass(frozen=True)
class StorageRuleDecision:
    target_power_kw: float
    reason_code: str


_PCS_AVAILABLE_STATES = {"available", "ready", "running", "standby"}


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _safety_decision(inputs: StorageRuleInput) -> Optional[StorageRuleDecision]:
    if (
        str(inputs.bms_state).lower() != "normal"
        or str(inputs.pcs_state).lower() not in _PCS_AVAILABLE_STATES
        or not inputs.grid_connected
        or inputs.temperature_c >= inputs.temperature_stop_c
    ):
        return StorageRuleDecision(0.0, "safety_fault")
    if (
        inputs.current_target_power_kw == 0
        and inputs.temperature_c > inputs.temperature_resume_c
    ):
        return StorageRuleDecision(0.0, "safety_temperature_hysteresis")
    return None


def _base_decision(inputs: StorageRuleInput) -> StorageRuleDecision:
    net_load_kw = inputs.load_kw - inputs.pv_kw
    pv_surplus_kw = max(-net_load_kw, 0.0)
    if pv_surplus_kw > inputs.deadband_kw:
        return StorageRuleDecision(
            min(pv_surplus_kw, max(inputs.available_charge_kw, 0.0)),
            "pv_surplus",
        )

    if inputs.demand_limit_kw is not None:
        excess_kw = net_load_kw - inputs.demand_limit_kw
        if excess_kw > inputs.deadband_kw:
            return StorageRuleDecision(
                -min(excess_kw, max(inputs.available_discharge_kw, 0.0)),
                "demand_limit",
            )

    tariff = str(inputs.tariff).lower()
    if tariff == "peak" and net_load_kw > inputs.deadband_kw:
        return StorageRuleDecision(
            -min(net_load_kw, max(inputs.available_discharge_kw, 0.0)),
            "tariff_peak",
        )
    if tariff == "valley" and inputs.available_charge_kw > inputs.deadband_kw:
        return StorageRuleDecision(max(inputs.available_charge_kw, 0.0), "tariff_valley")
    return StorageRuleDecision(0.0, "idle")


def _apply_soc_limits(
    inputs: StorageRuleInput,
    decision: StorageRuleDecision,
) -> StorageRuleDecision:
    if decision.target_power_kw > 0:
        if inputs.soc >= inputs.soc_charge_stop:
            return StorageRuleDecision(0.0, "soc_charge_limit")
        if inputs.current_target_power_kw <= 0 and inputs.soc > inputs.soc_charge_resume:
            return StorageRuleDecision(0.0, "soc_charge_hysteresis")
    if decision.target_power_kw < 0:
        if inputs.soc <= inputs.soc_discharge_stop:
            return StorageRuleDecision(0.0, "soc_discharge_limit")
        if inputs.current_target_power_kw >= 0 and inputs.soc < inputs.soc_discharge_resume:
            return StorageRuleDecision(0.0, "soc_discharge_hysteresis")
    return decision


def _apply_transition_guards(
    inputs: StorageRuleInput,
    decision: StorageRuleDecision,
) -> StorageRuleDecision:
    current = inputs.current_target_power_kw
    target = decision.target_power_kw
    elapsed = inputs.seconds_since_last_transition
    if target == current:
        return decision

    if current != 0 and elapsed is not None and elapsed < inputs.minimum_run_seconds:
        return StorageRuleDecision(current, "minimum_run_duration")

    if current != 0 and target != 0 and _sign(current) != _sign(target):
        return StorageRuleDecision(0.0, "direction_change_standby")

    previous = inputs.previous_nonzero_target_power_kw
    if (
        current == 0
        and target != 0
        and previous not in (None, 0)
        and _sign(float(previous)) != _sign(target)
        and elapsed is not None
        and elapsed < inputs.direction_change_standby_seconds
    ):
        return StorageRuleDecision(0.0, "direction_change_standby")

    if current == 0 and target != 0 and elapsed is not None and elapsed < inputs.minimum_stop_seconds:
        return StorageRuleDecision(0.0, "minimum_stop_duration")
    return decision


def decide_storage_power(inputs: StorageRuleInput) -> StorageRuleDecision:
    """按 safety、光伏、需量、电价、idle 固定优先级生成目标功率。"""
    numeric_values = (
        inputs.load_kw,
        inputs.pv_kw,
        inputs.soc,
        inputs.temperature_c,
        inputs.available_charge_kw,
        inputs.available_discharge_kw,
        inputs.current_target_power_kw,
        inputs.deadband_kw,
    )
    if inputs.demand_limit_kw is not None:
        numeric_values = (*numeric_values, inputs.demand_limit_kw)
    if not all(math.isfinite(float(value)) for value in numeric_values):
        return StorageRuleDecision(0.0, "safety_invalid_input")

    safety = _safety_decision(inputs)
    if safety is not None:
        return safety

    decision = _apply_soc_limits(inputs, _base_decision(inputs))
    if 0 < abs(decision.target_power_kw) <= inputs.deadband_kw:
        decision = StorageRuleDecision(0.0, "idle_deadband")
    elif decision.target_power_kw == 0 and decision.reason_code == "idle":
        decision = StorageRuleDecision(0.0, "idle_deadband")
    return _apply_transition_guards(inputs, decision)
