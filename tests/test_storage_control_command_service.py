import json
import math
import os
from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.storage import StorageAssetProfile, StorageTelemetry
from app.models.tables import Device, DeviceControlLog
from app.services.devices.storage.control_command_service import StorageControlCommandService
from app.services.devices.storage.specs import CONTROL_RECEIPT_TIMEOUT


@pytest.fixture()
def storage_session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        device = Device(
            name="园区储能柜",
            sn="STO-001",
            device_type="storage",
            device_category="storage",
            energy_type="electricity",
            is_active=True,
        )
        session.add(device)
        session.commit()
        session.refresh(device)
        session.add(
            StorageAssetProfile(
                device_id=device.id,
                rated_energy_kwh=500.0,
                rated_power_kw=250.0,
                max_charge_power_kw=200.0,
                max_discharge_power_kw=180.0,
            )
        )
        session.add(
            StorageTelemetry(
                device_id=device.id,
                timestamp=datetime(2026, 7, 17, 10, 0, 0),
                data_source="simulated",
            )
        )
        session.commit()
        yield session, device


def test_queue_active_power_command_persists_structured_context_and_publishes(storage_session):
    session, device = storage_session
    published = []

    result = StorageControlCommandService.queue_command(
        session,
        device,
        command="set_active_power",
        operator="admin",
        source="manual",
        target_active_power=-120.0,
        publish_control_payload=lambda *args, **kwargs: published.append((args, kwargs)),
    )

    log = session.exec(select(DeviceControlLog)).one()
    reason = json.loads(log.reason)
    assert result["accepted"] is True
    assert result["command_id"] == str(log.id)
    assert log.command_source == "storage-control-api"
    assert log.result == "accepted"
    assert reason == {
        "command": "set_active_power",
        "target_active_power": -120.0,
        "control_mode": None,
        "source": "manual",
        "data_source": "simulated",
        "simulation_run_id": None,
    }
    payload = published[0][0][1]
    assert payload["protocol_version"] == "storage-v1"
    assert payload["command_id"] == str(log.id)
    assert payload["device_code"] == "STO-001"
    assert payload["source"] == "manual"
    assert payload["target_active_power"] == -120.0


@pytest.mark.parametrize("target", [math.nan, math.inf, 201.0, -181.0])
def test_queue_active_power_command_rejects_non_finite_or_profile_bound_values(storage_session, target):
    session, device = storage_session

    with pytest.raises(ValueError):
        StorageControlCommandService.queue_command(
            session,
            device,
            command="set_active_power",
            operator="admin",
            source="manual",
            target_active_power=target,
            publish_control_payload=lambda *args, **kwargs: None,
        )


def test_queue_command_validates_source_mode_and_single_pending_command(storage_session):
    session, device = storage_session

    with pytest.raises(ValueError, match="source"):
        StorageControlCommandService.queue_command(
            session,
            device,
            command="stop",
            operator="admin",
            source="unknown",
            publish_control_payload=lambda *args, **kwargs: None,
        )

    StorageControlCommandService.queue_command(
        session,
        device,
        command="set_control_mode",
        operator="admin",
        source="rule",
        control_mode="auto",
        publish_control_payload=lambda *args, **kwargs: None,
    )
    with pytest.raises(ValueError, match="待完成"):
        StorageControlCommandService.queue_command(
            session,
            device,
            command="stop",
            operator="admin",
            source="manual",
            publish_control_payload=lambda *args, **kwargs: None,
        )


def test_receipt_terminal_state_is_idempotent_and_reason_stays_json(storage_session):
    session, device = storage_session
    queued = StorageControlCommandService.queue_command(
        session,
        device,
        command="stop",
        operator="admin",
        source="manual",
        publish_control_payload=lambda *args, **kwargs: None,
    )
    notifier_events = []

    log = StorageControlCommandService.apply_control_receipt(
        session,
        device_id=device.id,
        command_id=queued["command_id"],
        result="success",
        detail="PCS 已停机",
        control_event_notifier=notifier_events.append,
    )
    duplicate = StorageControlCommandService.apply_control_receipt(
        session,
        device_id=device.id,
        command_id=queued["command_id"],
        result="success",
        detail="重复回执",
        control_event_notifier=notifier_events.append,
    )
    late = StorageControlCommandService.apply_control_receipt(
        session,
        device_id=device.id,
        command_id=queued["command_id"],
        result="failed",
        detail="迟到失败",
        control_event_notifier=notifier_events.append,
    )

    assert duplicate is log
    assert late.result == "success"
    reason = json.loads(late.reason)
    assert reason["receipt_detail"] == "PCS 已停机"
    assert reason["ignored_receipts"] == [{"result": "failed", "detail": "迟到失败"}]
    assert len(notifier_events) == 1


def test_timeout_only_updates_storage_control_api_pending_logs(storage_session):
    session, device = storage_session
    old = datetime.now() - CONTROL_RECEIPT_TIMEOUT - timedelta(seconds=1)
    storage_log = DeviceControlLog(
        device_id=device.id,
        action="stop",
        target_status=False,
        previous_status=True,
        operator="admin",
        command_source="storage-control-api",
        result="running",
        reason=json.dumps({"command": "stop"}),
        created_at=old,
    )
    other_log = DeviceControlLog(
        device_id=device.id,
        action="stop",
        target_status=False,
        previous_status=True,
        operator="admin",
        command_source="remote-control-api",
        result="accepted",
        reason="补偿控制",
        created_at=old,
    )
    session.add(storage_log)
    session.add(other_log)
    session.commit()

    expired = StorageControlCommandService.expire_pending_control_logs(session)

    assert [item.id for item in expired] == [storage_log.id]
    assert storage_log.result == "timeout"
    assert json.loads(storage_log.reason)["timeout_detail"]
    assert other_log.result == "accepted"
