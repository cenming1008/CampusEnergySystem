import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import delete
from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.storage import StorageAssetProfile, StorageTelemetry
from app.models.tables import Device, DeviceControlLog
from app.services.devices.storage import ems_service
from app.services.devices.storage.ems_service import StorageCampusInputs, StorageEmsService


@pytest.fixture()
def ems_session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        device = Device(
            name="储能柜",
            sn="STO-EMS-001",
            device_type="storage",
            device_category="storage",
            energy_type="electricity",
        )
        session.add(device)
        session.commit()
        session.refresh(device)
        session.add(
            StorageAssetProfile(
                device_id=device.id,
                rated_energy_kwh=500,
                rated_power_kw=250,
                max_charge_power_kw=200,
                max_discharge_power_kw=180,
                ems_auto_enabled=True,
            )
        )
        session.add(
            StorageTelemetry(
                device_id=device.id,
                timestamp=datetime.now(),
                soc=50,
                cell_temp_max=30,
                control_mode="auto",
                bms_status="normal",
                pcs_status="running",
                grid_status="connected",
                target_active_power=0,
                available_charge_power=200,
                available_discharge_power=180,
            )
        )
        session.commit()
        yield session, device


def _pv_surplus_inputs(*_args):
    return StorageCampusInputs(load_kw=100, pv_kw=180, tariff="peak", demand_limit_kw=300)


def test_evaluate_device_requires_global_and_device_gates(ems_session):
    session, device = ems_session
    queue = MagicMock()

    disabled = StorageEmsService.evaluate_device(
        session,
        device,
        campus_input_provider=_pv_surplus_inputs,
        ems_enabled=False,
        queue_command=queue,
    )
    profile = session.get(StorageAssetProfile, device.id)
    profile.ems_auto_enabled = False
    session.add(profile)
    session.commit()
    device_disabled = StorageEmsService.evaluate_device(
        session,
        device,
        campus_input_provider=_pv_surplus_inputs,
        ems_enabled=True,
        queue_command=queue,
    )

    assert disabled["status"] == "skipped"
    assert disabled["reason"] == "global_gate_disabled"
    assert device_disabled["reason"] == "device_gate_disabled"
    queue.assert_not_called()


def test_evaluate_device_queues_rule_command_through_task6_service(ems_session):
    session, device = ems_session
    queue = MagicMock(return_value={"command_id": "88", "status": "accepted"})

    result = StorageEmsService.evaluate_device(
        session,
        device,
        campus_input_provider=_pv_surplus_inputs,
        ems_enabled=True,
        queue_command=queue,
    )

    assert result["status"] == "queued"
    assert result["decision"].target_power_kw == 80
    assert queue.call_args.kwargs["command"] == "set_active_power"
    assert queue.call_args.kwargs["target_active_power"] == 80
    assert queue.call_args.kwargs["source"] == "rule"
    assert queue.call_args.kwargs["reason"] == "pv_surplus"


def test_evaluate_device_rejects_stale_telemetry(ems_session):
    session, device = ems_session
    telemetry = StorageEmsService.get_latest_telemetry(session, device.id)
    telemetry.timestamp = datetime.now() - timedelta(minutes=6)
    session.add(telemetry)
    session.commit()
    queue = MagicMock()

    result = StorageEmsService.evaluate_device(
        session,
        device,
        campus_input_provider=_pv_surplus_inputs,
        ems_enabled=True,
        queue_command=queue,
    )

    assert result["reason"] == "stale_telemetry"
    queue.assert_not_called()


def test_evaluate_device_rejects_incomplete_safety_telemetry(ems_session):
    session, device = ems_session
    telemetry = StorageEmsService.get_latest_telemetry(session, device.id)
    telemetry.soc = None
    session.add(telemetry)
    session.commit()
    queue = MagicMock()

    result = StorageEmsService.evaluate_device(
        session,
        device,
        campus_input_provider=_pv_surplus_inputs,
        ems_enabled=True,
        queue_command=queue,
    )

    assert result["reason"] == "incomplete_telemetry"
    queue.assert_not_called()


def test_tariff_for_time_reuses_project_peak_flat_valley_ranges():
    with patch.object(ems_service.settings, "electricity_peak_hours", "8-12"), patch.object(
        ems_service.settings,
        "electricity_flat_hours",
        "12-18",
    ):
        assert StorageEmsService._tariff_for_time(datetime(2026, 7, 17, 9)) == "peak"
        assert StorageEmsService._tariff_for_time(datetime(2026, 7, 17, 14)) == "flat"
        assert StorageEmsService._tariff_for_time(datetime(2026, 7, 17, 2)) == "valley"


def test_evaluate_device_skips_manual_mode_pending_and_deadband(ems_session):
    session, device = ems_session
    queue = MagicMock()
    telemetry = StorageEmsService.get_latest_telemetry(session, device.id)
    telemetry.control_mode = "manual"
    session.add(telemetry)
    session.commit()
    manual = StorageEmsService.evaluate_device(
        session,
        device,
        campus_input_provider=_pv_surplus_inputs,
        ems_enabled=True,
        queue_command=queue,
    )

    telemetry.control_mode = "auto"
    session.add(telemetry)
    session.add(
        DeviceControlLog(
            device_id=device.id,
            action="set_active_power",
            target_status=True,
            previous_status=True,
            command_source="storage-control-api",
            result="accepted",
        )
    )
    session.commit()
    pending = StorageEmsService.evaluate_device(
        session,
        device,
        campus_input_provider=_pv_surplus_inputs,
        ems_enabled=True,
        queue_command=queue,
    )

    session.exec(delete(DeviceControlLog))
    telemetry.target_active_power = 78
    session.add(telemetry)
    session.commit()
    deadband = StorageEmsService.evaluate_device(
        session,
        device,
        campus_input_provider=_pv_surplus_inputs,
        ems_enabled=True,
        queue_command=queue,
    )

    assert manual["reason"] == "manual_mode"
    assert pending["reason"] == "pending_command"
    assert deadband["reason"] == "target_deadband"
    queue.assert_not_called()


def test_safety_stop_uses_stop_command_and_does_not_duplicate_pending_stop(ems_session):
    session, device = ems_session
    telemetry = StorageEmsService.get_latest_telemetry(session, device.id)
    telemetry.bms_status = "fault"
    telemetry.target_active_power = -100
    session.add(telemetry)
    session.commit()
    queue = MagicMock(return_value={"command_id": "89", "status": "accepted"})

    first = StorageEmsService.evaluate_device(
        session,
        device,
        campus_input_provider=_pv_surplus_inputs,
        ems_enabled=True,
        queue_command=queue,
    )
    assert first["status"] == "queued"
    assert queue.call_args.kwargs["command"] == "stop"

    session.add(
        DeviceControlLog(
            device_id=device.id,
            action="stop",
            target_status=False,
            previous_status=True,
            command_source="storage-control-api",
            result="running",
        )
    )
    session.commit()
    second = StorageEmsService.evaluate_device(
        session,
        device,
        campus_input_provider=_pv_surplus_inputs,
        ems_enabled=True,
        queue_command=queue,
    )

    assert second["reason"] == "pending_command"
    assert queue.call_count == 1


def test_evaluate_all_only_selects_device_enabled_profiles(ems_session):
    session, device = ems_session
    with patch.object(StorageEmsService, "evaluate_device", return_value={"status": "skipped"}) as evaluate:
        results = StorageEmsService.evaluate_all(
            session,
            campus_input_provider=_pv_surplus_inputs,
            ems_enabled=True,
        )

    assert results == [{"status": "skipped"}]
    evaluate.assert_called_once()


def test_evaluate_all_contains_single_device_failure(ems_session):
    session, device = ems_session
    with patch.object(StorageEmsService, "evaluate_device", side_effect=ValueError("bad input")):
        results = StorageEmsService.evaluate_all(
            session,
            campus_input_provider=_pv_surplus_inputs,
            ems_enabled=True,
        )

    assert results == [
        {
            "status": "failed",
            "reason": "evaluation_error",
            "device_id": device.id,
            "detail": "bad input",
        }
    ]
