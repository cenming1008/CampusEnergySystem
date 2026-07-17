import math

import pytest

from app.domain.storage_dispatch_optimizer import (
    DispatchOptimizationError,
    StorageDispatchInput,
    optimize_storage_dispatch,
)


def _sunny_day_input(**overrides: object) -> StorageDispatchInput:
    load_kw = []
    pv_kw = []
    tariff_per_kwh = []
    for slot in range(96):
        hour = slot / 4
        load_kw.append(420.0 if 17 <= hour < 21 else 260.0)
        pv_kw.append(480.0 if 10 <= hour < 15 else 0.0)
        tariff_per_kwh.append(1.2 if 17 <= hour < 21 else 0.35)

    values = {
        "load_kw": tuple(load_kw),
        "pv_kw": tuple(pv_kw),
        "tariff_per_kwh": tuple(tariff_per_kwh),
        "energy_capacity_kwh": 500.0,
        "max_charge_kw": 200.0,
        "max_discharge_kw": 200.0,
        "initial_soc": 50.0,
        "terminal_soc_target": 50.0,
        "charge_efficiency": 0.95,
        "discharge_efficiency": 0.95,
        "demand_charge_per_kw": 10.0,
        "degradation_cost_per_kwh": 0.01,
        "curtailment_penalty_per_kwh": 0.2,
    }
    values.update(overrides)
    return StorageDispatchInput(**values)


def test_sunny_day_dispatch_is_feasible_peak_shaving_and_deterministic():
    inputs = _sunny_day_input()

    first = optimize_storage_dispatch(inputs)
    second = optimize_storage_dispatch(inputs)

    assert first.solver_status == "Optimal"
    assert len(first.slots) == 96
    assert all(not (slot.charge_kw > 0 and slot.discharge_kw > 0) for slot in first.slots)
    assert all(15.0 <= slot.soc <= 85.0 for slot in first.slots)
    assert all(slot.grid_kw >= 0 for slot in first.slots)
    assert first.terminal_soc == pytest.approx(inputs.terminal_soc_target, abs=1e-5)
    assert first.peak_grid_kw < first.baseline_peak_grid_kw
    assert first == second

    for slot in first.slots:
        assert slot.target_active_power_kw == pytest.approx(
            slot.charge_kw - slot.discharge_kw,
            abs=1e-6,
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"load_kw": (1.0,) * 95}, "load_kw must contain exactly 96 slots"),
        ({"pv_kw": (math.nan,) + (0.0,) * 95}, "pv_kw must be a finite number"),
        ({"charge_efficiency": 0.0}, "charge_efficiency must be in (0, 1]"),
        ({"initial_soc": 10.0}, "initial_soc must be within the configured SOC range"),
    ],
)
def test_invalid_inputs_are_rejected(overrides: dict[str, object], message: str):
    with pytest.raises(ValueError) as exc_info:
        optimize_storage_dispatch(_sunny_day_input(**overrides))

    assert str(exc_info.value) == message


def test_non_optimal_solver_status_raises_domain_error():
    inputs = _sunny_day_input(
        energy_capacity_kwh=1000.0,
        max_charge_kw=1.0,
        initial_soc=15.0,
        terminal_soc_target=85.0,
    )

    with pytest.raises(DispatchOptimizationError, match="Infeasible") as exc_info:
        optimize_storage_dispatch(inputs)

    assert exc_info.value.solver_status == "Infeasible"
