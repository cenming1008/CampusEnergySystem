import unittest
from datetime import datetime, timedelta
import os
from types import SimpleNamespace
from unittest.mock import patch

from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.devices import monitoring
from app.models.tables import Device, DeviceControlLog
from app.services.alarm_service import AlarmService
from app.services.device_monitor_service import DeviceMonitorService
from app.services.energy_service import EnergyService
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

    def test_reactive_power_compensator_realtime_includes_specialized_fields(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="无功补偿柜1",
                sn="RPC-001",
                device_type="reactive_power_compensator",
                device_category="compensation",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            EnergyService.save_energy_data(
                session=session,
                device_id=device.id,
                energy_type=device.energy_type,
                consumption=320.5,
                flow_rate=18.2,
                timestamp=now - timedelta(minutes=1),
                reactive_power=-36.8,
                power_factor=0.98,
                voltage=398.0,
                current=42.0,
            )

            realtime = DeviceMonitorService.get_latest_realtime(session, device.id)

            self.assertEqual(realtime["flow_rate"], 18.2)
            self.assertEqual(realtime["reactive_power"], -36.8)
            self.assertEqual(realtime["power_factor"], 0.98)
            self.assertEqual(realtime["voltage"], 398.0)
            self.assertEqual(realtime["current"], 42.0)
            self.assertIsNotNone(realtime["timestamp"])

    def test_reactive_power_compensator_realtime_returns_none_when_no_data(self):
        with Session(self.engine) as session:
            device = Device(
                name="无功补偿柜2",
                sn="RPC-002",
                device_type="reactive_power_compensator",
                device_category="compensation",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            realtime = DeviceMonitorService.get_latest_realtime(session, device.id)

            self.assertIn("reactive_power", realtime)
            self.assertIsNone(realtime["reactive_power"])
            self.assertIsNone(realtime["flow_rate"])
            self.assertIsNone(realtime["power_factor"])

    def test_non_compensator_realtime_behavior_remains_unchanged(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="常规负荷",
                sn="LOAD-001",
                device_type="load",
                device_category="load",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            EnergyService.save_energy_data(
                session=session,
                device_id=device.id,
                energy_type=device.energy_type,
                consumption=88.0,
                flow_rate=12.5,
                timestamp=now,
                power_factor=0.91,
                voltage=380.0,
                current=19.0,
            )

            realtime = DeviceMonitorService.get_latest_realtime(session, device.id)

            self.assertEqual(realtime["flow_rate"], 12.5)
            self.assertNotIn("reactive_power", realtime)

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

    def test_status_history_uses_precise_control_titles_and_pending_states(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="补偿器1",
                sn="CAP-001",
                device_type="compensation",
                device_subtype="capacitor_bank_controller",
                device_category="compensation",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            session.add(
                DeviceControlLog(
                    device_id=device.id,
                    action="write:switch_on_power_factor",
                    target_status=True,
                    previous_status=True,
                    operator="admin",
                    command_source="control-profile-api",
                    result="accepted",
                    reason="投入功率因数 -> 95",
                    created_at=now - timedelta(minutes=1),
                )
            )
            session.add(
                DeviceControlLog(
                    device_id=device.id,
                    action="reset_alarm",
                    target_status=True,
                    previous_status=True,
                    operator="operator",
                    command_source="remote-control-api",
                    result="rejected",
                    reason="设备处于就地模式",
                    created_at=now - timedelta(seconds=10),
                )
            )
            session.commit()

            items = DeviceMonitorService.get_status_history(session, device.id, hours=24, limit=10)
            control_items = [item for item in items if item["event_type"] == "control"]

            self.assertEqual(control_items[0]["title"], "报警复位")
            self.assertEqual(control_items[0]["status"], "rejected")
            self.assertIn("设备拒绝执行", control_items[0]["detail"])
            self.assertEqual(control_items[1]["title"], "参数写入 · 投入功率因数")
            self.assertEqual(control_items[1]["status"], "accepted")
            self.assertIn("已入队", control_items[1]["detail"])

    @patch("app.api.endpoints.devices.monitoring.ensure_device_access")
    @patch("app.api.endpoints.devices.monitoring.DeviceMonitorService.get_monitor_overview")
    def test_monitor_overview_endpoint_keeps_reactive_power_key_for_compensator(
        self,
        mock_get_overview,
        mock_ensure_access,
    ):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        mock_get_overview.return_value = {
            "archive": {"id": 16, "device_type": "reactive_power_compensator"},
            "runtime_status": {"device_id": 16},
            "realtime": {
                "device_id": 16,
                "timestamp": None,
                "energy_type": "electricity",
                "consumption": None,
                "flow_rate": None,
                "reactive_power": None,
                "power_factor": None,
                "voltage": None,
                "current": None,
                "pressure": None,
                "temperature": None,
            },
            "ingestion_health": {"device_id": 16},
            "recent_alarms": [],
            "recent_control_logs": [],
        }

        response = monitoring.get_device_monitor_overview(
            device_id=16,
            session=session,
            current_user=current_user,
        )

        mock_ensure_access.assert_called_once_with(session, current_user, 16)
        self.assertIn("reactive_power", response["data"]["realtime"])
        self.assertIsNone(response["data"]["realtime"]["reactive_power"])

    @patch("app.api.endpoints.devices.monitoring.ensure_device_access")
    @patch("app.api.endpoints.devices.monitoring.DeviceMonitorService.get_latest_realtime")
    def test_monitor_realtime_endpoint_keeps_reactive_power_key_for_compensator(
        self,
        mock_get_realtime,
        mock_ensure_access,
    ):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        mock_get_realtime.return_value = {
            "device_id": 16,
            "timestamp": None,
            "energy_type": "electricity",
            "consumption": None,
            "flow_rate": None,
            "reactive_power": None,
            "power_factor": None,
            "voltage": None,
            "current": None,
            "pressure": None,
            "temperature": None,
        }

        response = monitoring.get_device_realtime(
            device_id=16,
            session=session,
            current_user=current_user,
        )

        mock_ensure_access.assert_called_once_with(session, current_user, 16)
        self.assertIn("reactive_power", response["data"])
        self.assertIsNone(response["data"]["reactive_power"])


if __name__ == "__main__":
    unittest.main()
