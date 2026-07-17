import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.storage import StorageAssetProfile, StorageDispatchPlan, StorageTelemetry
from app.models.tables import AuditEvent, Device, DeviceControlLog, User
from app.services.devices.storage.simulation_cutover_service import (
    CutoverCounts,
    StorageSimulationCutoverService,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def cutover_session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        target = Device(
            name="目标储能柜",
            sn="STO-CUTOVER-001",
            device_type="storage",
            device_subtype="battery_energy_storage_system",
            device_category="storage",
            energy_type="electricity",
            archive_status="complete",
        )
        other = Device(
            name="其他储能柜",
            sn="STO-CUTOVER-002",
            device_type="storage",
            device_subtype="battery_energy_storage_system",
            device_category="storage",
            energy_type="electricity",
        )
        non_storage = Device(
            name="园区负荷",
            sn="LOAD-CUTOVER-001",
            device_type="load",
            device_category="load",
            energy_type="electricity",
        )
        user = User(username="admin", hashed_password="not-used", role="admin")
        session.add_all([target, other, non_storage, user])
        session.commit()
        for row in (target, other, non_storage, user):
            session.refresh(row)
        session.add_all(
            [
                StorageAssetProfile(
                    device_id=target.id,
                    rated_energy_kwh=500,
                    rated_power_kw=250,
                    ems_auto_enabled=False,
                ),
                StorageAssetProfile(
                    device_id=other.id,
                    rated_energy_kwh=500,
                    rated_power_kw=250,
                    ems_auto_enabled=False,
                ),
            ]
        )
        old = datetime.now() - timedelta(hours=1)
        for index in range(12):
            session.add(
                StorageTelemetry(
                    device_id=target.id,
                    timestamp=old + timedelta(seconds=index),
                    soc=50,
                    data_source="simulated",
                    simulation_run_id="run-target",
                )
            )
        session.add(
            StorageTelemetry(
                device_id=target.id,
                timestamp=old + timedelta(minutes=1),
                soc=51,
                data_source="real",
            )
        )
        session.add(
            StorageTelemetry(
                device_id=other.id,
                timestamp=old,
                soc=52,
                data_source="simulated",
                simulation_run_id="run-other",
            )
        )
        for index in range(96):
            session.add(
                StorageDispatchPlan(
                    device_id=target.id,
                    dispatch_date=date.today(),
                    slot_index=index,
                    target_active_power=0,
                    data_source="simulated",
                    simulation_run_id="run-target",
                )
            )
        session.add_all(
            [
                StorageDispatchPlan(
                    device_id=target.id,
                    dispatch_date=date.today() + timedelta(days=1),
                    slot_index=0,
                    target_active_power=0,
                    data_source="real",
                ),
                StorageDispatchPlan(
                    device_id=other.id,
                    dispatch_date=date.today(),
                    slot_index=0,
                    target_active_power=0,
                    data_source="simulated",
                    simulation_run_id="run-other",
                ),
            ]
        )
        for index in range(3):
            session.add(
                DeviceControlLog(
                    device_id=target.id,
                    action="set_active_power",
                    target_status=True,
                    command_source="storage-control-api",
                    reason=json.dumps({"data_source": "simulated", "index": index}),
                )
            )
        session.add_all(
            [
                DeviceControlLog(
                    device_id=target.id,
                    action="set_active_power",
                    target_status=True,
                    command_source="storage-control-api",
                    reason=json.dumps({"data_source": "real"}),
                ),
                DeviceControlLog(
                    device_id=target.id,
                    action="set_active_power",
                    target_status=True,
                    command_source="storage-control-api",
                    reason="unstructured simulated text",
                ),
                DeviceControlLog(
                    device_id=other.id,
                    action="set_active_power",
                    target_status=True,
                    command_source="storage-control-api",
                    reason=json.dumps({"data_source": "simulated"}),
                ),
            ]
        )
        session.commit()
        yield session, target, other, non_storage, user


def test_preview_and_execute_only_remove_exact_allowlisted_simulated_rows(cutover_session):
    session, target, other, _, user = cutover_session

    preview = StorageSimulationCutoverService.preview(session, device_id=target.id)
    assert preview == CutoverCounts(telemetry_count=12, plan_count=96, control_log_count=3)

    result = StorageSimulationCutoverService.execute(
        session,
        device_id=target.id,
        expected=preview,
        operator="admin",
    )

    assert result.deleted == preview
    assert session.exec(
        select(StorageTelemetry).where(StorageTelemetry.device_id == target.id)
    ).one().data_source == "real"
    assert session.exec(
        select(StorageDispatchPlan).where(StorageDispatchPlan.device_id == target.id)
    ).one().data_source == "real"
    assert len(
        session.exec(
            select(DeviceControlLog).where(DeviceControlLog.device_id == target.id)
        ).all()
    ) == 2
    assert len(
        session.exec(select(StorageTelemetry).where(StorageTelemetry.device_id == other.id)).all()
    ) == 1
    assert len(
        session.exec(select(StorageDispatchPlan).where(StorageDispatchPlan.device_id == other.id)).all()
    ) == 1
    assert session.get(Device, target.id).archive_status == "complete"
    assert session.get(StorageAssetProfile, target.id) is not None
    assert session.get(User, user.id).role == "admin"
    audit = session.exec(select(AuditEvent)).one()
    details = json.loads(audit.details)
    assert audit.action == "storage.simulation_cutover"
    assert audit.actor == "admin"
    assert details["device_id"] == target.id
    assert details["counts"] == preview.as_dict()
    assert details["timestamp"]


def test_execute_rechecks_all_blockers_and_count_drift(cutover_session):
    session, target, _, non_storage, _ = cutover_session
    expected = StorageSimulationCutoverService.preview(session, device_id=target.id)

    with pytest.raises(ValueError, match="operator"):
        StorageSimulationCutoverService.execute(
            session, device_id=target.id, expected=expected, operator=" "
        )

    with pytest.raises(ValueError, match="storage"):
        StorageSimulationCutoverService.execute(
            session, device_id=non_storage.id, expected=CutoverCounts(), operator="admin"
        )

    profile = session.get(StorageAssetProfile, target.id)
    profile.ems_auto_enabled = True
    session.add(profile)
    session.commit()
    with pytest.raises(ValueError, match="自动控制"):
        StorageSimulationCutoverService.execute(
            session, device_id=target.id, expected=expected, operator="admin"
        )
    profile.ems_auto_enabled = False
    session.add(profile)
    session.commit()

    session.add(
        StorageTelemetry(
            device_id=target.id,
            timestamp=datetime.now(),
            soc=50,
            data_source="simulated",
            simulation_run_id="still-active",
        )
    )
    session.commit()
    with pytest.raises(ValueError, match="仍活跃"):
        StorageSimulationCutoverService.execute(
            session, device_id=target.id, expected=expected, operator="admin"
        )
    recent = session.exec(
        select(StorageTelemetry)
        .where(StorageTelemetry.device_id == target.id)
        .where(StorageTelemetry.simulation_run_id == "still-active")
    ).one()
    session.delete(recent)
    session.commit()

    with pytest.raises(ValueError, match="漂移"):
        StorageSimulationCutoverService.execute(
            session,
            device_id=target.id,
            expected=CutoverCounts(telemetry_count=11, plan_count=96, control_log_count=3),
            operator="admin",
        )

    assert StorageSimulationCutoverService.preview(session, device_id=target.id) == expected


def test_cutover_help_does_not_require_database_configuration():
    environment = os.environ.copy()
    environment.pop("DATABASE_URL", None)

    result = subprocess.run(
        [sys.executable, "scripts/python/storage_cutover.py", "--help"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--preview" in result.stdout
    assert "--execute" in result.stdout
