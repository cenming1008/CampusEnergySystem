import os
import unittest
from datetime import datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.tables import CapacitorBankControlProfile, CapacitorBankTelemetry, Device
from app.services.devices.compensation.monitor_service import CompensationMonitorService


class TestCompensationMonitorServiceBoundary(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(self.engine)

    def test_build_monitor_handles_capacitor_bank_without_device_monitor_service(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="补偿监控服务边界测试",
                sn="CAP-BND-001",
                device_type="compensation",
                device_subtype="capacitor_bank_controller",
                device_category="compensation",
                energy_type="electricity",
                rated_capacity=120.0,
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            session.add(
                CapacitorBankTelemetry(
                    device_id=device.id,
                    timestamp=now,
                    control_mode="manual",
                    running_circuit_count=6,
                    temperature=38.8,
                )
            )
            session.add(
                CapacitorBankControlProfile(
                    device_id=device.id,
                    source="telemetry",
                    snapshot_timestamp=now - timedelta(seconds=5),
                    common_output_circuit_count=18,
                    split_output_circuit_count=6,
                )
            )
            session.commit()

            monitor = CompensationMonitorService.build_monitor(
                session,
                device,
                {"reactive_power": -30.0, "temperature": 37.5},
            )

        self.assertEqual(monitor["subtype"], "capacitor_bank_controller")
        self.assertEqual(monitor["control_mode"]["source"], "telemetry")
        self.assertEqual(monitor["circuit_summary"]["running_count"], 6)
        self.assertEqual(monitor["key_metrics"]["capacity_utilization"]["value"], 25.0)
        self.assertEqual(monitor["key_metrics"]["cabinet_temperature"]["value"], 38.8)


if __name__ == "__main__":
    unittest.main()
