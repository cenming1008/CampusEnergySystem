import os
from datetime import date, datetime
from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.domain.storage_dispatch_optimizer import (
    StorageDispatchInput,
    StorageDispatchResult,
    StorageDispatchSlot,
)
from app.models.storage import StorageAssetProfile, StorageDispatchPlan, StorageTelemetry
from app.models.tables import Device, EnergyData
from app.services.devices.storage.dispatch_service import StorageDispatchService
from app.services.storage_energy_service import StorageEnergyService


@pytest.fixture()
def storage_energy_session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        load = Device(
            name="园区负荷",
            sn="LOAD-ENERGY-001",
            device_type="load",
            device_category="load",
            energy_type="electricity",
        )
        pv = Device(
            name="园区光伏",
            sn="PV-ENERGY-001",
            device_type="solar",
            device_category="solar",
            energy_type="electricity",
        )
        storage = Device(
            name="园区储能",
            sn="STO-ENERGY-001",
            device_type="storage",
            device_category="storage",
            energy_type="electricity",
        )
        session.add_all([load, pv, storage])
        session.commit()
        for device in (load, pv, storage):
            session.refresh(device)
        session.add_all(
            [
                EnergyData(
                    device_id=load.id,
                    timestamp=datetime(2026, 7, 18, 10, 0),
                    energy_type="electricity",
                    consumption=1000.0,
                    flow_rate=420.0,
                ),
                EnergyData(
                    device_id=pv.id,
                    timestamp=datetime(2026, 7, 18, 10, 0),
                    energy_type="electricity",
                    consumption=500.0,
                    flow_rate=100.0,
                ),
                StorageAssetProfile(
                    device_id=storage.id,
                    rated_energy_kwh=500.0,
                    rated_power_kw=250.0,
                    max_charge_power_kw=250.0,
                    max_discharge_power_kw=250.0,
                ),
                StorageTelemetry(
                    device_id=storage.id,
                    timestamp=datetime(2026, 7, 18, 10, 0),
                    soc=68.4,
                    active_power=-120.0,
                    target_active_power=-120.0,
                    data_source="simulated",
                    simulation_run_id="run-task-13",
                ),
                StorageDispatchPlan(
                    device_id=storage.id,
                    dispatch_date=date(2026, 7, 18),
                    slot_index=40,
                    target_active_power=-120.0,
                    solver_status="Optimal",
                    is_valid=True,
                    data_source="simulated",
                    simulation_run_id="run-task-13",
                ),
            ]
        )
        session.commit()
        yield session, load, pv, storage


def test_overview_aggregates_latest_accessible_pv_load_and_storage(storage_energy_session):
    session, load, pv, storage = storage_energy_session

    result = StorageEnergyService.get_overview(
        session,
        allowed_device_ids={load.id, pv.id, storage.id},
        now=datetime(2026, 7, 18, 10, 2),
    )

    assert result["current"] == {
        "load_kw": 420.0,
        "pv_kw": 100.0,
        "grid_kw": 200.0,
        "storage_kw": -120.0,
        "soc": 68.4,
    }
    assert result["storage_device_ids"] == [storage.id]
    assert result["data_source"] == "simulated"
    assert result["simulation_run_id"] == "run-task-13"
    assert result["plan_execution_rate"] == 100.0
    assert result["dispatch"] == {
        "actual_power_kw": -120.0,
        "target_power_kw": -120.0,
        "deviation_kw": 0.0,
        "strategy": "day_ahead",
        "plan_status": "active",
        "solver_status": "Optimal",
        "fallback_reason": None,
        "slot_index": 40,
        "plan_generated_at": result["dispatch"]["plan_generated_at"],
    }
    assert result["provenance"]["is_stale"] is False
    assert result["provenance"]["load_timestamp"] == datetime(2026, 7, 18, 10, 0)


def test_metric_calculation_uses_physical_energy_balance():
    inputs = StorageDispatchInput(
        load_kw=(100.0,) * 96,
        pv_kw=(50.0,) * 96,
        tariff_per_kwh=(0.5,) * 96,
        energy_capacity_kwh=500.0,
        max_charge_kw=250.0,
        max_discharge_kw=250.0,
        initial_soc=50.0,
        terminal_soc_target=50.0,
    )

    metrics = StorageEnergyService.calculate_metrics(inputs, (0.0,) * 96)

    assert metrics["grid_import_kwh"] == 1200.0
    assert metrics["cost"] == 600.0
    assert metrics["peak_grid_kw"] == 50.0
    assert metrics["pv_self_use_rate"] == 100.0
    assert metrics["curtailment_kwh"] == 0.0
    assert metrics["throughput_kwh"] == 0.0
    assert metrics["equivalent_cycles"] == 0.0
    assert metrics["terminal_soc"] == 50.0
    assert metrics["plan_execution_rate"] is None
    assert metrics["feasible_slot_rate"] == 100.0


def test_metric_calculation_separates_battery_export_from_pv_curtailment():
    inputs = StorageDispatchInput(
        load_kw=(0.0,) * 96,
        pv_kw=(0.0,) * 96,
        tariff_per_kwh=(0.5,) * 96,
        energy_capacity_kwh=500.0,
        max_charge_kw=250.0,
        max_discharge_kw=250.0,
        initial_soc=50.0,
        terminal_soc_target=50.0,
    )

    metrics = StorageEnergyService.calculate_metrics(inputs, (-100.0,) + (0.0,) * 95)

    assert metrics["curtailment_kwh"] == 0.0
    assert metrics["grid_export_kwh"] == 25.0


def test_metric_calculation_attributes_mixed_surplus_to_pv_and_battery():
    inputs = StorageDispatchInput(
        load_kw=(20.0,) * 96,
        pv_kw=(100.0,) * 96,
        tariff_per_kwh=(0.5,) * 96,
        energy_capacity_kwh=500.0,
        max_charge_kw=250.0,
        max_discharge_kw=250.0,
        initial_soc=50.0,
        terminal_soc_target=50.0,
    )

    metrics = StorageEnergyService.calculate_metrics(inputs, (-50.0,) + (0.0,) * 95)

    assert metrics["curtailment_kwh"] == 1920.0
    assert metrics["grid_export_kwh"] == 12.5


def test_overview_does_not_claim_rule_fallback_without_execution_evidence(
    storage_energy_session,
):
    session, load, pv, storage = storage_energy_session
    plan = session.exec(select(StorageDispatchPlan)).first()
    session.delete(plan)
    session.commit()

    result = StorageEnergyService.get_overview(
        session,
        allowed_device_ids={load.id, pv.id, storage.id},
        now=datetime(2026, 7, 18, 10, 2),
    )

    assert result["dispatch"]["plan_status"] == "missing"
    assert result["dispatch"]["strategy"] is None
    assert result["dispatch"]["solver_status"] is None
    assert result["dispatch"]["fallback_reason"] is None
    assert result["plan_execution_rate"] is None


def test_metric_calculation_reports_soc_clipping_as_replay_feasibility():
    inputs = StorageDispatchInput(
        load_kw=(0.0,) * 96,
        pv_kw=(0.0,) * 96,
        tariff_per_kwh=(0.5,) * 96,
        energy_capacity_kwh=500.0,
        max_charge_kw=250.0,
        max_discharge_kw=250.0,
        initial_soc=84.0,
        terminal_soc_target=84.0,
        soc_min=15.0,
        soc_max=85.0,
    )

    metrics = StorageEnergyService.calculate_metrics(inputs, (250.0,) + (0.0,) * 95)

    assert metrics["terminal_soc"] == 85.0
    assert metrics["throughput_kwh"] == pytest.approx(5.263158, abs=1e-6)
    assert metrics["feasible_slot_rate"] == pytest.approx(98.958333, abs=1e-6)
    assert metrics["plan_execution_rate"] is None


def test_comparison_replays_three_strategies_against_one_checksum(storage_energy_session):
    session, load, pv, storage = storage_energy_session
    allowed = {load.id, pv.id, storage.id}

    first = StorageEnergyService.compare_strategies(
        session,
        scenario_key="sunny_workday",
        seed=20260718,
        initial_soc=50.0,
        allowed_device_ids=allowed,
        device_id=storage.id,
    )
    second = StorageEnergyService.compare_strategies(
        session,
        scenario_key="sunny_workday",
        seed=20260718,
        initial_soc=50.0,
        allowed_device_ids=allowed,
        device_id=storage.id,
    )

    assert set(first["strategies"]) == {"baseline", "rule", "day_ahead"}
    assert first == second
    assert first["scenario_key"] == "sunny_workday"
    assert first["seed"] == 20260718
    assert first["initial_soc"] == 50.0
    assert first["input_series_checksum"] == second["input_series_checksum"]
    assert len(first["input_series_checksum"]) == 64
    for metrics in first["strategies"].values():
        assert {
            "grid_import_kwh",
            "grid_export_kwh",
            "cost",
            "peak_grid_kw",
            "pv_self_use_rate",
            "curtailment_kwh",
            "throughput_kwh",
            "equivalent_cycles",
            "terminal_soc",
            "plan_execution_rate",
            "feasible_slot_rate",
        } <= set(metrics)


def test_comparison_calculates_each_strategy_from_the_same_fixture(storage_energy_session):
    session, load, pv, storage = storage_energy_session
    inputs = StorageDispatchInput(
        load_kw=(100.0,) * 96,
        pv_kw=(50.0,) * 96,
        tariff_per_kwh=(0.5,) * 96,
        energy_capacity_kwh=500.0,
        max_charge_kw=250.0,
        max_discharge_kw=250.0,
        initial_soc=50.0,
        terminal_soc_target=50.0,
        demand_charge_per_kw=0.0,
        degradation_cost_per_kwh=0.0,
        curtailment_penalty_per_kwh=0.0,
    )
    rule_targets = (100.0, -90.25) + (0.0,) * 94
    day_ahead_targets = (50.0, -45.125) + (0.0,) * 94

    def optimized(_inputs):
        slots = tuple(
            StorageDispatchSlot(
                slot_index=index,
                charge_kw=max(day_ahead_targets[index], 0.0),
                discharge_kw=max(-day_ahead_targets[index], 0.0),
                target_active_power_kw=day_ahead_targets[index],
                grid_kw=0.0,
                soc=50.0,
                curtailment_kw=0.0,
            )
            for index in range(96)
        )
        return StorageDispatchResult(
            solver_status="Optimal",
            slots=slots,
            total_cost=0.0,
            peak_grid_kw=0.0,
            total_curtailment_kwh=0.0,
            terminal_soc=50.0,
            baseline_peak_grid_kw=50.0,
        )

    with patch.object(
        StorageDispatchService,
        "build_scenario_input",
        return_value=inputs,
    ), patch.object(StorageEnergyService, "_rule_targets", return_value=rule_targets), patch(
        "app.services.storage_energy_service.optimize_storage_dispatch",
        side_effect=optimized,
    ):
        result = StorageEnergyService.compare_strategies(
            session,
            scenario_key="sunny_workday",
            seed=1,
            initial_soc=50.0,
            allowed_device_ids={load.id, pv.id, storage.id},
            device_id=storage.id,
        )

    assert result["solver_status"] == "Optimal"
    assert result["strategies"]["baseline"]["cost"] == 600.0
    assert result["strategies"]["baseline"]["peak_grid_kw"] == 50.0
    assert result["strategies"]["rule"]["throughput_kwh"] == 47.5625
    assert result["strategies"]["rule"]["terminal_soc"] == 50.0
    assert result["strategies"]["day_ahead"]["throughput_kwh"] == 23.78125
    assert result["strategies"]["day_ahead"]["terminal_soc"] == 50.0


def test_comparison_rejects_a_storage_device_outside_scope(storage_energy_session):
    session, load, pv, storage = storage_energy_session

    with pytest.raises(ValueError, match="不可访问"):
        StorageEnergyService.compare_strategies(
            session,
            scenario_key="sunny_workday",
            seed=1,
            initial_soc=50.0,
            allowed_device_ids={load.id, pv.id},
            device_id=storage.id,
        )
