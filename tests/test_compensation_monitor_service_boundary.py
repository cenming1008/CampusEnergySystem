import os
import unittest
from datetime import datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.tables import CapacitorBankControlProfile, CapacitorBankTelemetry, Device, DeviceControlLog
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

    def test_build_monitor_uses_successful_mode_log_over_stale_manual_telemetry(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="补偿控制模式日志优先测试",
                sn="CAP-BND-002",
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
                    timestamp=now - timedelta(seconds=10),
                    control_mode="manual",
                    running_circuit_count=6,
                )
            )
            session.add(
                DeviceControlLog(
                    device_id=device.id,
                    action="manual_switch",
                    target_status=True,
                    previous_status=True,
                    operator="admin",
                    command_source="remote-control-api",
                    result="success",
                    reason="控制台控制模式切换 -> 自动模式 | 设备回执已处理: 已切回自动模式",
                    created_at=now,
                )
            )
            session.commit()

            monitor = CompensationMonitorService.build_monitor(
                session,
                device,
                {},
            )

        self.assertEqual(monitor["control_mode"]["value"], "自动")
        self.assertEqual(monitor["control_mode"]["source"], "control_log")

    def test_build_monitor_marks_svg_as_read_only_capability(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="SVG 能力边界测试",
                sn="SVG-BND-001",
                device_type="svg",
                device_subtype="svg",
                device_category="compensation",
                energy_type="electricity",
                rated_capacity=150.0,
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            monitor = CompensationMonitorService.build_monitor(
                session,
                device,
                {"reactive_power": 30.0, "temperature": 32.5},
            )

        self.assertEqual(monitor["subtype"], "svg")
        self.assertTrue(monitor["capabilities_summary"]["supports_read"])
        self.assertFalse(monitor["capabilities_summary"]["supports_write"])
        self.assertFalse(monitor["capabilities_summary"]["supports_remote_control"])


if __name__ == "__main__":
    unittest.main()
