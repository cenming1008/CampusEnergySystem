import os
import unittest
from datetime import datetime
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from sqlmodel import Session, SQLModel, create_engine, select

from app.integrations.mqtt.device_extensions import persist_device_extensions
from app.models.storage import StorageTelemetry
from app.models.tables import Alarm, Device
from app.services.alarm_service import AlarmService


class TestStorageTelemetryPersistence(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(self.engine)

    def test_persist_device_extensions_writes_storage_telemetry_and_checks_alarms(self):
        timestamp = datetime(2026, 5, 18, 13, 0, 0)
        with Session(self.engine) as session:
            device = Device(
                name="储能柜-STO-001",
                sn="STO-001",
                device_type="storage",
                device_category="storage",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            with patch.object(
                AlarmService,
                "load_thresholds",
                return_value={
                    "alarm_rules": {
                        "platform_rules": {
                            "storage": {
                                "default": {"enabled": False},
                                "device_categories": {
                                    "storage": {
                                        "enabled": True,
                                        "soc_min": 20.0,
                                        "cell_temp_max": 55.0,
                                    },
                                },
                            },
                        },
                    },
                },
            ):
                persist_device_extensions(
                    session,
                    device.id,
                    timestamp,
                    {
                        "soc": 18.0,
                        "soh": 96.0,
                        "power": -42.5,
                        "cell_temp_max": 40.0,
                        "run_state": "discharging",
                    },
                )
                session.commit()

            telemetry = session.exec(select(StorageTelemetry)).one()
            self.assertEqual(telemetry.device_id, device.id)
            self.assertEqual(telemetry.timestamp, timestamp)
            self.assertEqual(telemetry.soc, 18.0)
            self.assertEqual(telemetry.active_power, -42.5)
            self.assertEqual(telemetry.run_state, "discharging")

            alarm = session.exec(select(Alarm)).one()
            self.assertEqual(alarm.category, "storage_soc_low")
            self.assertEqual(alarm.source, "platform_rule")

    def test_persist_device_extensions_maps_simulator_state_fields_without_changing_power_sign(self):
        timestamp = datetime(2026, 7, 17, 10, 0, 0)
        with Session(self.engine) as session:
            device = Device(
                name="储能仿真柜-STO-001",
                sn="STO-SIM-001",
                device_type="storage",
                device_subtype="battery_energy_storage_system",
                device_category="storage",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            payload = {
                "soc": 68.4,
                "soh": 97.8,
                "active_power": -120.0,
                "target_active_power": -125.0,
                "available_charge_power": 250.0,
                "available_discharge_power": 180.0,
                "bms_state": "normal",
                "pcs_state": "running",
                "grid_connection_state": "connected",
                "command_source": "rule",
                "data_source": "simulated",
            }

            with patch.object(AlarmService, "check_storage_faults"):
                persist_device_extensions(
                    session,
                    device.id,
                    timestamp,
                    payload,
                )
                session.commit()

            telemetry = session.exec(select(StorageTelemetry)).one()
            self.assertEqual(telemetry.active_power, -120.0)
            self.assertEqual(telemetry.target_active_power, -125.0)
            self.assertEqual(telemetry.available_charge_power, 250.0)
            self.assertEqual(telemetry.available_discharge_power, 180.0)
            self.assertEqual(telemetry.bms_status, "normal")
            self.assertEqual(telemetry.pcs_status, "running")
            self.assertEqual(telemetry.grid_status, "connected")
            self.assertEqual(telemetry.command_source, "rule")
            self.assertEqual(telemetry.data_source, "simulated")


if __name__ == "__main__":
    unittest.main()
