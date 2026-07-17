import os
from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.core.exceptions import PermissionDeniedException
from app.models.storage import StorageTelemetry
from app.models.tables import Device
from app.services.devices.storage.asset_profile_service import StorageAssetProfileService


@pytest.fixture()
def profile_session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        device = Device(
            name="储能柜",
            sn="STO-API-001",
            device_type="storage",
            device_category="storage",
            energy_type="electricity",
        )
        session.add(device)
        session.commit()
        session.refresh(device)
        yield session, device


def _profile_values(ems_auto_enabled=False):
    return {
        "rated_energy_kwh": 500,
        "rated_power_kw": 250,
        "ems_auto_enabled": ems_auto_enabled,
    }


def test_auto_gate_requires_existing_profile_and_admin(profile_session):
    session, device = profile_session

    with pytest.raises(ValueError, match="先保存"):
        StorageAssetProfileService.upsert_profile(
            session,
            device.id,
            _profile_values(True),
            allow_auto_gate_update=True,
        )

    StorageAssetProfileService.upsert_profile(
        session,
        device.id,
        _profile_values(False),
        allow_auto_gate_update=True,
    )
    with pytest.raises(PermissionDeniedException):
        StorageAssetProfileService.upsert_profile(
            session,
            device.id,
            _profile_values(True),
            allow_auto_gate_update=False,
        )


def test_auto_gate_requires_fresh_healthy_telemetry(profile_session):
    session, device = profile_session
    StorageAssetProfileService.upsert_profile(
        session,
        device.id,
        _profile_values(False),
        allow_auto_gate_update=True,
    )
    session.add(
        StorageTelemetry(
            device_id=device.id,
            timestamp=datetime.now() - timedelta(minutes=6),
            bms_status="normal",
            pcs_status="running",
            grid_status="connected",
        )
    )
    session.commit()

    with pytest.raises(ValueError, match="过期"):
        StorageAssetProfileService.upsert_profile(
            session,
            device.id,
            _profile_values(True),
            allow_auto_gate_update=True,
        )

    session.add(
        StorageTelemetry(
            device_id=device.id,
            timestamp=datetime.now(),
            bms_status="normal",
            pcs_status="running",
            grid_status="connected",
        )
    )
    session.commit()
    updated = StorageAssetProfileService.upsert_profile(
        session,
        device.id,
        _profile_values(True),
        allow_auto_gate_update=True,
    )

    assert updated.ems_auto_enabled is True


def test_profile_validation_rejects_invalid_soc_and_power(profile_session):
    session, device = profile_session
    values = _profile_values(False)
    values.update({"rated_power_kw": -1, "soc_min": 90, "soc_max": 10})

    with pytest.raises(ValueError):
        StorageAssetProfileService.upsert_profile(
            session,
            device.id,
            values,
            allow_auto_gate_update=True,
        )

    with pytest.raises(ValueError, match="额定功率"):
        StorageAssetProfileService.upsert_profile(
            session,
            device.id,
            {
                **_profile_values(False),
                "max_charge_power_kw": 251,
            },
            allow_auto_gate_update=True,
        )
