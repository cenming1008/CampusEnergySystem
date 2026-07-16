"""Pure battery storage state transition rules for deterministic simulation."""

import math
from dataclasses import dataclass, replace


def _require_finite(name: str, value: float) -> None:
    try:
        finite = math.isfinite(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not finite:
        raise ValueError(f"{name} must be a finite number")


@dataclass(frozen=True)
class StorageAssetConfig:
    energy_kwh: float
    power_kw: float
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    soc_min: float = 10.0
    soc_max: float = 90.0
    ramp_kw_per_second: float = 25.0

    def __post_init__(self) -> None:
        _validate_config(self)


@dataclass(frozen=True)
class StorageState:
    soc: float
    actual_power_kw: float = 0.0
    temperature_c: float = 25.0
    soh: float = 100.0
    throughput_kwh: float = 0.0
    run_state: str = "standby"

    def __post_init__(self) -> None:
        _validate_state(self)


def _validate_config(config: StorageAssetConfig) -> None:
    numeric_fields = (
        "energy_kwh",
        "power_kw",
        "charge_efficiency",
        "discharge_efficiency",
        "soc_min",
        "soc_max",
        "ramp_kw_per_second",
    )
    for field_name in numeric_fields:
        _require_finite(field_name, getattr(config, field_name))

    if config.energy_kwh <= 0:
        raise ValueError("energy_kwh must be greater than zero")
    if config.power_kw <= 0:
        raise ValueError("power_kw must be greater than zero")
    if config.ramp_kw_per_second <= 0:
        raise ValueError("ramp_kw_per_second must be greater than zero")
    if not 0 < config.charge_efficiency <= 1:
        raise ValueError("charge_efficiency must be in (0, 1]")
    if not 0 < config.discharge_efficiency <= 1:
        raise ValueError("discharge_efficiency must be in (0, 1]")
    if not 0 <= config.soc_min < config.soc_max <= 100:
        raise ValueError("SOC limits must satisfy 0 <= soc_min < soc_max <= 100")


def _validate_state(state: StorageState) -> None:
    numeric_fields = (
        "soc",
        "actual_power_kw",
        "temperature_c",
        "soh",
        "throughput_kwh",
    )
    for field_name in numeric_fields:
        _require_finite(field_name, getattr(state, field_name))


def _apply_ramp_limit(
    current_power_kw: float,
    target_power_kw: float,
    ramp_kw_per_second: float,
    seconds: float,
) -> float:
    max_change_kw = ramp_kw_per_second * seconds
    requested_change_kw = target_power_kw - current_power_kw
    if requested_change_kw > max_change_kw:
        return current_power_kw + max_change_kw
    if requested_change_kw < -max_change_kw:
        return current_power_kw - max_change_kw
    return target_power_kw


def _updated_temperature(
    temperature_c: float,
    ambient_temperature_c: float,
    actual_power_kw: float,
    rated_power_kw: float,
    seconds: float,
) -> float:
    """Return a bounded first-order ambient response plus utilization heating."""
    dt_h = seconds / 3600.0
    ambient_response = min(dt_h * 0.1, 0.1)
    heating_window = min(dt_h, 1.0)
    utilization = min(abs(actual_power_kw) / rated_power_kw, 1.0)
    temperature = (
        temperature_c * (1.0 - ambient_response)
        + ambient_temperature_c * ambient_response
        + utilization * 0.5 * heating_window
    )
    _require_finite("temperature_c result", temperature)
    return temperature


def step_storage(
    config: StorageAssetConfig,
    state: StorageState,
    requested_power_kw: float,
    seconds: float,
    ambient_temperature_c: float = 25.0,
) -> StorageState:
    """Advance storage state without mutating the supplied configuration or state."""
    _validate_config(config)
    _validate_state(state)
    _require_finite("requested_power_kw", requested_power_kw)
    _require_finite("seconds", seconds)
    _require_finite("ambient_temperature_c", ambient_temperature_c)
    if seconds <= 0:
        raise ValueError("seconds must be greater than zero")
    if not config.soc_min <= state.soc <= config.soc_max:
        raise ValueError("state SOC must be within configured hard limits")

    dt_h = seconds / 3600.0
    target_power_kw = max(-config.power_kw, min(config.power_kw, requested_power_kw))
    actual_power_kw = _apply_ramp_limit(
        state.actual_power_kw,
        target_power_kw,
        config.ramp_kw_per_second,
        seconds,
    )

    saturated_soc = None
    if state.soc >= config.soc_max and actual_power_kw > 0:
        actual_power_kw = 0.0
    elif state.soc <= config.soc_min and actual_power_kw < 0:
        actual_power_kw = 0.0
    elif actual_power_kw > 0:
        charge_room_kwh = (config.soc_max - state.soc) / 100.0 * config.energy_kwh
        maximum_charge_power_kw = charge_room_kwh / (config.charge_efficiency * dt_h)
        if actual_power_kw > maximum_charge_power_kw:
            actual_power_kw = maximum_charge_power_kw
            saturated_soc = config.soc_max
    elif actual_power_kw < 0:
        discharge_room_kwh = (state.soc - config.soc_min) / 100.0 * config.energy_kwh
        maximum_discharge_power_kw = discharge_room_kwh * config.discharge_efficiency / dt_h
        if -actual_power_kw > maximum_discharge_power_kw:
            actual_power_kw = -maximum_discharge_power_kw
            saturated_soc = config.soc_min

    if actual_power_kw >= 0:
        stored_delta_kwh = actual_power_kw * config.charge_efficiency * dt_h
    else:
        stored_delta_kwh = actual_power_kw / config.discharge_efficiency * dt_h

    if saturated_soc is None:
        soc = state.soc + stored_delta_kwh / config.energy_kwh * 100.0
    else:
        soc = saturated_soc

    throughput_kwh = state.throughput_kwh + abs(actual_power_kw) * dt_h
    _require_finite("soc result", soc)
    _require_finite("throughput_kwh result", throughput_kwh)

    if actual_power_kw > 0:
        run_state = "charging"
    elif actual_power_kw < 0:
        run_state = "discharging"
    else:
        actual_power_kw = 0.0
        run_state = "standby"

    return replace(
        state,
        soc=soc,
        actual_power_kw=actual_power_kw,
        temperature_c=_updated_temperature(
            state.temperature_c,
            ambient_temperature_c,
            actual_power_kw,
            config.power_kw,
            seconds,
        ),
        throughput_kwh=throughput_kwh,
        run_state=run_state,
    )
