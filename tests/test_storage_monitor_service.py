from datetime import datetime

from sqlmodel import Session, SQLModel, create_engine

from app.models.storage import StorageTelemetry
from app.services.devices.storage.monitor_service import StorageMonitorService


def test_build_storage_monitor_exposes_simulator_control_and_component_metrics():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(
            StorageTelemetry(
                device_id=1,
                timestamp=datetime(2026, 7, 17, 10, 0, 0),
                active_power=-120.0,
                target_active_power=-125.0,
                available_charge_power=250.0,
                available_discharge_power=180.0,
                bms_status="normal",
                pcs_status="running",
                grid_status="connected",
                command_source="rule",
                data_source="simulated",
            )
        )
        session.commit()

        monitor = StorageMonitorService.build_storage_monitor(session, 1)

    metrics = monitor["key_metrics"]
    assert metrics["active_power"]["value"] == -120.0
    assert metrics["target_active_power"]["value"] == -125.0
    assert metrics["available_charge_power"]["value"] == 250.0
    assert metrics["available_discharge_power"]["value"] == 180.0
    assert metrics["bms_state"] == {
        "value": "normal",
        "source": "telemetry",
        "state": "live",
    }
    assert metrics["pcs_state"]["value"] == "running"
    assert metrics["grid_connection_state"]["value"] == "connected"
    assert metrics["command_source"]["value"] == "rule"
    assert metrics["data_source"] == {
        "value": "simulated",
        "source": "telemetry",
        "state": "simulated",
    }
