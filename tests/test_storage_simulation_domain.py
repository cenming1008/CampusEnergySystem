import math
import os
from dataclasses import FrozenInstanceError

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.domain.storage_simulation import StorageAssetConfig, StorageState, step_storage


def config(**overrides):
    values = {
        "energy_kwh": 500.0,
        "power_kw": 250.0,
        "ramp_kw_per_second": 1_000.0,
    }
    values.update(overrides)
    return StorageAssetConfig(**values)


def test_charge_updates_power_soc_throughput_and_run_state():
    initial = StorageState(soc=50.0)

    result = step_storage(config(), initial, requested_power_kw=100.0, seconds=900.0)

    assert result.actual_power_kw == pytest.approx(100.0)
    assert result.soc == pytest.approx(54.75)
    assert result.throughput_kwh == pytest.approx(25.0)
    assert result.run_state == "charging"


def test_discharge_at_lower_soc_limit_stays_on_standby():
    result = step_storage(
        config(),
        StorageState(soc=10.0),
        requested_power_kw=-200.0,
        seconds=60.0,
    )

    assert result.actual_power_kw == 0.0
    assert result.soc == 10.0
    assert result.run_state == "standby"


def test_discharge_power_is_recalculated_to_reach_lower_soc_limit_exactly():
    result = step_storage(
        config(discharge_efficiency=0.95),
        StorageState(soc=20.0),
        requested_power_kw=-250.0,
        seconds=3600.0,
    )

    assert result.actual_power_kw == pytest.approx(-47.5)
    assert result.soc == 10.0
    assert result.throughput_kwh == pytest.approx(47.5)
    assert result.run_state == "discharging"


@pytest.mark.parametrize(
    ("requested_power_kw", "expected_power_kw"),
    [(400.0, 250.0), (-400.0, -250.0)],
)
def test_requested_power_is_clipped_to_rated_power(requested_power_kw, expected_power_kw):
    result = step_storage(
        config(energy_kwh=10_000.0),
        StorageState(soc=50.0),
        requested_power_kw=requested_power_kw,
        seconds=1.0,
    )

    assert result.actual_power_kw == expected_power_kw


def test_power_change_is_limited_by_ramp_rate():
    result = step_storage(
        config(energy_kwh=10_000.0, ramp_kw_per_second=25.0),
        StorageState(soc=50.0, actual_power_kw=20.0),
        requested_power_kw=100.0,
        seconds=2.0,
    )

    assert result.actual_power_kw == 70.0


def test_direction_change_obeys_ramp_before_crossing_zero():
    result = step_storage(
        config(energy_kwh=10_000.0, ramp_kw_per_second=25.0),
        StorageState(soc=50.0, actual_power_kw=-100.0),
        requested_power_kw=100.0,
        seconds=1.0,
    )

    assert result.actual_power_kw == -75.0
    assert result.run_state == "discharging"


def test_charge_power_is_recalculated_to_reach_upper_soc_limit_exactly():
    result = step_storage(
        config(charge_efficiency=0.8),
        StorageState(soc=89.0),
        requested_power_kw=250.0,
        seconds=3600.0,
    )

    assert result.actual_power_kw == pytest.approx(6.25)
    assert result.soc == 90.0
    assert result.throughput_kwh == pytest.approx(6.25)
    assert result.run_state == "charging"


def test_step_returns_a_new_state_without_mutating_frozen_inputs():
    asset = config()
    initial = StorageState(
        soc=50.0,
        actual_power_kw=0.0,
        temperature_c=24.0,
        soh=98.0,
        throughput_kwh=12.0,
    )

    result = step_storage(asset, initial, requested_power_kw=0.0, seconds=60.0)

    assert result is not initial
    assert initial == StorageState(
        soc=50.0,
        actual_power_kw=0.0,
        temperature_c=24.0,
        soh=98.0,
        throughput_kwh=12.0,
    )
    assert result.soh == 98.0
    assert math.isfinite(result.temperature_c)
    with pytest.raises(FrozenInstanceError):
        initial.soc = 51.0
    with pytest.raises(FrozenInstanceError):
        asset.energy_kwh = 600.0


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf])
def test_non_finite_power_and_seconds_are_rejected(invalid):
    asset = config()
    state = StorageState(soc=50.0)

    with pytest.raises(ValueError):
        step_storage(asset, state, requested_power_kw=invalid, seconds=60.0)
    with pytest.raises(ValueError):
        step_storage(asset, state, requested_power_kw=0.0, seconds=invalid)


@pytest.mark.parametrize("seconds", [0.0, -1.0])
def test_non_positive_seconds_are_rejected(seconds):
    with pytest.raises(ValueError):
        step_storage(config(), StorageState(soc=50.0), 0.0, seconds)


@pytest.mark.parametrize(
    "overrides",
    [
        {"energy_kwh": 0.0},
        {"energy_kwh": -1.0},
        {"power_kw": 0.0},
        {"power_kw": -1.0},
        {"ramp_kw_per_second": 0.0},
        {"ramp_kw_per_second": -1.0},
        {"charge_efficiency": 0.0},
        {"charge_efficiency": 1.01},
        {"discharge_efficiency": 0.0},
        {"discharge_efficiency": 1.01},
        {"soc_min": -1.0},
        {"soc_max": 101.0},
        {"soc_min": 90.0, "soc_max": 90.0},
        {"soc_min": 91.0, "soc_max": 90.0},
    ],
)
def test_invalid_asset_configuration_is_rejected(overrides):
    with pytest.raises(ValueError):
        config(**overrides)


@pytest.mark.parametrize(
    "field",
    [
        "energy_kwh",
        "power_kw",
        "charge_efficiency",
        "discharge_efficiency",
        "soc_min",
        "soc_max",
        "ramp_kw_per_second",
    ],
)
@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf])
def test_non_finite_asset_configuration_is_rejected(field, invalid):
    with pytest.raises(ValueError):
        config(**{field: invalid})


@pytest.mark.parametrize(
    "field",
    ["soc", "actual_power_kw", "temperature_c", "soh", "throughput_kwh"],
)
@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf])
def test_non_finite_state_is_rejected(field, invalid):
    values = {"soc": 50.0, field: invalid}
    with pytest.raises(ValueError):
        StorageState(**values)


@pytest.mark.parametrize("soc", [9.9, 90.1])
def test_state_soc_outside_asset_hard_limits_is_rejected(soc):
    with pytest.raises(ValueError):
        step_storage(config(), StorageState(soc=soc), 0.0, 60.0)
