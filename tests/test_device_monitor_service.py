import unittest
from datetime import datetime, timedelta
import os

from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.tables import Device
from app.services.alarm_service import AlarmService
from app.services.device_monitor_service import DeviceMonitorService
from app.services.device_service import DeviceService
from app.services.ingestion_health_service import IngestionHealthService


class TestDeviceMonitorService(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(self.engine)

    def test_toggle_device_status_creates_control_log(self):
        with Session(self.engine) as session:
            device = Device(
                name="1号配电柜",
                sn="CAB-001",
                device_type="load",
                device_category="load",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            updated = DeviceService.toggle_device_status(
                session,
                device.id,
                False,
                operator="tester",
                reason="巡检停机",
            )

            logs = DeviceMonitorService.get_control_logs(session, device.id)

            self.assertFalse(updated.is_active)
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].action, "stop")
            self.assertEqual(logs[0].operator, "tester")
            self.assertEqual(logs[0].reason, "巡检停机")

    def test_monitor_overview_aggregates_runtime_alarm_and_realtime(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="2号水表",
                sn="WT-001",
                device_type="water_meter",
                device_category="water_meter",
                energy_type="water",
                is_active=True,
                location="北区泵房",
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            DeviceService.report_device_data(
                session,
                device.id,
                data={
                    "consumption": 12.5,
                    "flow_rate": 2.2,
                    "pressure": 0.33,
                    "temperature": 21.5,
                },
                timestamp=now - timedelta(minutes=5),
            )
            IngestionHealthService.mark_ingestion_success(session, device.id, now - timedelta(minutes=1))
            session.commit()

            AlarmService.create_alarm(
                session,
                device.id,
                "压力异常",
                timestamp=now,
                severity="warning",
                category="pressure_out_of_range",
            )

            overview = DeviceMonitorService.get_monitor_overview(session, device.id)

            self.assertEqual(overview["archive"]["name"], "2号水表")
            self.assertEqual(overview["runtime_status"]["code"], "alarm")
            self.assertEqual(overview["realtime"]["flow_rate"], 2.2)
            self.assertEqual(len(overview["recent_alarms"]), 1)

    def test_status_history_contains_alarm_and_control_events(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="3号储能柜",
                sn="ST-001",
                device_type="storage",
                device_category="storage",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            AlarmService.create_alarm(session, device.id, "通讯中断", timestamp=now - timedelta(hours=2), severity="critical")
            DeviceService.toggle_device_status(session, device.id, False, operator="tester")

            items = DeviceMonitorService.get_status_history(session, device.id, hours=24, limit=10)

            event_types = {item["event_type"] for item in items}
            self.assertIn("alarm", event_types)
            self.assertIn("control", event_types)


if __name__ == "__main__":
    unittest.main()
