import os
from datetime import date, datetime

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.domain.storage_dispatch_optimizer import (
    DispatchOptimizationError,
    StorageDispatchInput,
    StorageDispatchResult,
    StorageDispatchSlot,
)
from app.models.storage import StorageDispatchPlan
from app.models.tables import Device
from app.services.devices.storage.dispatch_service import StorageDispatchService


@pytest.fixture()
def dispatch_session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        device = Device(
            name="储能柜",
            sn="STO-DISPATCH-001",
            device_type="storage",
            device_category="storage",
            energy_type="electricity",
        )
        session.add(device)
        session.commit()
        session.refresh(device)
        yield session, device


def _optimizer_input() -> StorageDispatchInput:
    return StorageDispatchInput(
        load_kw=(300.0,) * 96,
        pv_kw=(0.0,) * 96,
        tariff_per_kwh=(0.5,) * 96,
        energy_capacity_kwh=500.0,
        max_charge_kw=200.0,
        max_discharge_kw=200.0,
        initial_soc=50.0,
        terminal_soc_target=50.0,
    )


def _optimal_result() -> StorageDispatchResult:
    slots = tuple(
        StorageDispatchSlot(
            slot_index=index,
            charge_kw=25.0 if index < 4 else 0.0,
            discharge_kw=25.0 if 68 <= index < 72 else 0.0,
            target_active_power_kw=(25.0 if index < 4 else (-25.0 if 68 <= index < 72 else 0.0)),
            grid_kw=300.0,
            soc=50.0,
            curtailment_kw=0.0,
        )
        for index in range(96)
    )
    return StorageDispatchResult(
        solver_status="Optimal",
        slots=slots,
        total_cost=1000.0,
        peak_grid_kw=300.0,
        total_curtailment_kwh=0.0,
        terminal_soc=50.0,
        baseline_peak_grid_kw=300.0,
    )


def test_generate_plan_replaces_previous_plan_in_one_committed_version(dispatch_session):
    session, device = dispatch_session
    dispatch_date = date(2026, 7, 18)
    session.add(
        StorageDispatchPlan(
            device_id=device.id,
            dispatch_date=dispatch_date,
            slot_index=0,
            target_active_power=10.0,
            strategy_version="v0.9.0",
            is_valid=True,
        )
    )
    session.commit()

    result = StorageDispatchService.generate_plan(
        session,
        device_id=device.id,
        dispatch_date=dispatch_date,
        optimizer_input=_optimizer_input(),
        data_source="simulated",
        simulation_run_id="run-12",
        optimizer=lambda _inputs: _optimal_result(),
        generated_at=datetime(2026, 7, 17, 23, 5),
    )

    rows = list(
        session.exec(
            select(StorageDispatchPlan)
            .where(StorageDispatchPlan.device_id == device.id)
            .where(StorageDispatchPlan.dispatch_date == dispatch_date)
        ).all()
    )
    current = [row for row in rows if row.is_valid]
    assert result.status == "optimal"
    assert len(current) == 96
    assert len(rows) == 96
    assert {row.slot_index for row in current} == set(range(96))
    assert {row.strategy_version for row in current} == {"v1.0.0"}
    assert {row.data_source for row in current} == {"simulated"}
    assert {row.simulation_run_id for row in current} == {"run-12"}


def test_optimizer_failure_preserves_previous_valid_plan(dispatch_session):
    session, device = dispatch_session
    dispatch_date = date(2026, 7, 18)
    previous = StorageDispatchPlan(
        device_id=device.id,
        dispatch_date=dispatch_date,
        slot_index=0,
        target_active_power=10.0,
        solver_status="Optimal",
        is_valid=True,
    )
    session.add(previous)
    session.commit()

    def fail(_inputs):
        raise DispatchOptimizationError("Infeasible")

    result = StorageDispatchService.generate_plan(
        session,
        device_id=device.id,
        dispatch_date=dispatch_date,
        optimizer_input=_optimizer_input(),
        optimizer=fail,
    )

    session.refresh(previous)
    assert result.status == "failed"
    assert result.solver_status == "Infeasible"
    assert previous.is_valid is True
    assert len(list(session.exec(select(StorageDispatchPlan)).all())) == 1


def test_simulated_plan_requires_a_simulation_run_id(dispatch_session):
    session, device = dispatch_session

    with pytest.raises(ValueError, match="simulation_run_id"):
        StorageDispatchService.generate_plan(
            session,
            device_id=device.id,
            dispatch_date=date(2026, 7, 18),
            optimizer_input=_optimizer_input(),
            data_source="simulated",
            optimizer=lambda _inputs: _optimal_result(),
        )


def test_current_slot_returns_only_valid_unexpired_plan(dispatch_session):
    session, device = dispatch_session
    session.add(
        StorageDispatchPlan(
            device_id=device.id,
            dispatch_date=date(2026, 7, 18),
            slot_index=41,
            target_active_power=-80.0,
            solver_status="Optimal",
            is_valid=True,
        )
    )
    session.commit()

    current = StorageDispatchService.get_current_slot(
        session,
        device.id,
        now=datetime(2026, 7, 18, 10, 22),
    )
    expired = StorageDispatchService.get_current_slot(
        session,
        device.id,
        now=datetime(2026, 7, 19, 10, 22),
    )

    assert current is not None
    assert current.slot_index == 41
    assert current.target_active_power == -80.0
    assert expired is None
