import unittest
from datetime import datetime, timedelta
import os
from types import SimpleNamespace
from unittest.mock import patch

from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.devices import monitoring
from app.models.tables import CapacitorBankControlProfile, CapacitorBankTelemetry, Device, DeviceControlLog, SVGAssetProfile, SVGTelemetry
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
            self.assertIsNone(overview["archive"]["device_subtype"])
            self.assertEqual(overview["runtime_status"]["code"], "alarm")
            self.assertEqual(overview["realtime"]["flow_rate"], 2.2)
            self.assertEqual(len(overview["recent_alarms"]), 1)

    def test_monitor_overview_preserves_device_subtype_for_compensation_devices(self):
        with Session(self.engine) as session:
            device = Device(
                name="补偿器子类型测试",
                sn="CAP-SUB-001",
                device_type="compensation",
                device_subtype="capacitor_bank_controller",
                device_category="compensation",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            overview = DeviceMonitorService.get_monitor_overview(session, device.id)

            self.assertEqual(overview["archive"]["device_type"], "compensation")
            self.assertEqual(overview["archive"]["device_subtype"], "capacitor_bank_controller")
            self.assertIsNotNone(overview["compensation_monitor"])
            self.assertEqual(overview["compensation_monitor"]["subtype"], "capacitor_bank_controller")

    def test_monitor_overview_returns_capacitor_bank_compensation_monitor_semantics(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="补偿器监控语义测试",
                sn="CAP-MON-001",
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

            EnergyService.save_energy_data(
                session=session,
                device_id=device.id,
                energy_type=device.energy_type,
                consumption=12.0,
                flow_rate=26.0,
                timestamp=now - timedelta(minutes=1),
                reactive_power=-32.0,
                power_factor=0.95,
                voltage=389.0,
                current=43.0,
                temperature=38.6,
            )
            session.add(
                CapacitorBankTelemetry(
                    device_id=device.id,
                    timestamp=now,
                    control_mode="manual",
                    running_circuit_count=6,
                    circuit_state_phase_a=0b00000011,
                    circuit_state_phase_b=0b00000001,
                    temperature=39.8,
                )
            )
            session.add(
                CapacitorBankControlProfile(
                    device_id=device.id,
                    source="telemetry",
                    snapshot_timestamp=now,
                    terminal_assignment_scheme="自动模式",
                    common_output_circuit_count=18,
                    split_output_circuit_count=6,
                )
            )
            session.add(
                DeviceControlLog(
                    device_id=device.id,
                    action="switch_control_mode",
                    target_status=True,
                    previous_status=True,
                    operator="admin",
                    command_source="remote-control-api",
                    result="success",
                    reason="控制模式切换到自动模式",
                    created_at=now - timedelta(minutes=2),
                )
            )
            session.commit()

            overview = DeviceMonitorService.get_monitor_overview(session, device.id)

            compensation_monitor = overview["compensation_monitor"]
            self.assertEqual(compensation_monitor["subtype"], "capacitor_bank_controller")
            self.assertEqual(compensation_monitor["control_mode"]["value"], "手动")
            self.assertEqual(compensation_monitor["control_mode"]["source"], "telemetry")
            self.assertEqual(compensation_monitor["control_mode"]["state"], "live")
            self.assertEqual(compensation_monitor["circuit_summary"]["running_count"], 6)
            self.assertEqual(compensation_monitor["circuit_summary"]["total_count"], 24)
            self.assertEqual(compensation_monitor["circuit_summary"]["source"], "telemetry")
            self.assertEqual(compensation_monitor["key_metrics"]["capacity_utilization"]["value"], 25.0)
            self.assertEqual(compensation_monitor["key_metrics"]["capacity_utilization"]["source"], "telemetry")
            self.assertEqual(compensation_monitor["key_metrics"]["cabinet_temperature"]["value"], 39.8)
            self.assertEqual(compensation_monitor["profile_status"]["source_status"], "fresh")
            self.assertTrue(compensation_monitor["capabilities_summary"]["supports_remote_control"])

    def test_monitor_overview_capacitor_bank_falls_back_to_profile_then_logs_then_placeholder(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="补偿器回退优先级测试",
                sn="CAP-MON-002",
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

            EnergyService.save_energy_data(
                session=session,
                device_id=device.id,
                energy_type=device.energy_type,
                consumption=10.0,
                flow_rate=20.0,
                timestamp=now - timedelta(minutes=1),
                reactive_power=-24.0,
                power_factor=0.96,
                voltage=390.0,
                current=40.0,
            )
            session.add(
                CapacitorBankControlProfile(
                    device_id=device.id,
                    source="telemetry",
                    snapshot_timestamp=now,
                    control_mode="manual",
                    running_circuit_count=5,
                    terminal_assignment_scheme="手动模式",
                    common_output_circuit_count=16,
                    split_output_circuit_count=8,
                )
            )
            session.add(
                DeviceControlLog(
                    device_id=device.id,
                    action="switch_control_mode",
                    target_status=True,
                    previous_status=True,
                    operator="admin",
                    command_source="remote-control-api",
                    result="success",
                    reason="控制模式切换到自动模式",
                    created_at=now - timedelta(minutes=2),
                )
            )
            session.commit()

            overview = DeviceMonitorService.get_monitor_overview(session, device.id)
            compensation_monitor = overview["compensation_monitor"]

            self.assertEqual(compensation_monitor["control_mode"]["value"], "手动")
            self.assertEqual(compensation_monitor["control_mode"]["source"], "profile")
            self.assertEqual(compensation_monitor["circuit_summary"]["running_count"], 5)
            self.assertEqual(compensation_monitor["circuit_summary"]["source"], "profile")
            self.assertEqual(compensation_monitor["key_metrics"]["capacity_utilization"]["value"], 20.8)
            self.assertEqual(compensation_monitor["key_metrics"]["capacity_utilization"]["source"], "profile")
            self.assertEqual(compensation_monitor["key_metrics"]["temperature_health"]["value"], "待判断")
            self.assertEqual(compensation_monitor["key_metrics"]["temperature_health"]["source"], "missing")

            session.exec(CapacitorBankControlProfile.__table__.delete())
            session.commit()

            overview = DeviceMonitorService.get_monitor_overview(session, device.id)
            compensation_monitor = overview["compensation_monitor"]

            self.assertEqual(compensation_monitor["control_mode"]["value"], "自动")
            self.assertEqual(compensation_monitor["control_mode"]["source"], "control_log")

            session.exec(DeviceControlLog.__table__.delete())
            session.commit()

            overview = DeviceMonitorService.get_monitor_overview(session, device.id)
            compensation_monitor = overview["compensation_monitor"]

            self.assertEqual(compensation_monitor["control_mode"]["value"], "自动")
            self.assertEqual(compensation_monitor["control_mode"]["source"], "placeholder")
            self.assertEqual(compensation_monitor["control_mode"]["state"], "mock")

    def test_monitor_overview_capacitor_bank_builds_temperature_health_from_threshold_and_alarm(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="补偿器温度健康度测试",
                sn="CAP-TEMP-001",
                device_type="compensation",
                device_subtype="capacitor_bank_controller",
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
                consumption=12.0,
                flow_rate=21.0,
                timestamp=now - timedelta(minutes=1),
                temperature=54.0,
            )
            session.add(
                CapacitorBankControlProfile(
                    device_id=device.id,
                    source="telemetry",
                    snapshot_timestamp=now,
                    temperature_upper_limit=55.0,
                )
            )
            session.commit()

            overview = DeviceMonitorService.get_monitor_overview(session, device.id)
            health_metric = overview["compensation_monitor"]["key_metrics"]["temperature_health"]
            self.assertEqual(health_metric["value"], "接近上限")
            self.assertEqual(health_metric["source"], "profile")
            self.assertEqual(health_metric["state"], "live")

            session.add(
                CapacitorBankTelemetry(
                    device_id=device.id,
                    timestamp=now,
                    temperature=56.0,
                    temp_alarm=True,
                )
            )
            session.commit()

            overview = DeviceMonitorService.get_monitor_overview(session, device.id)
            health_metric = overview["compensation_monitor"]["key_metrics"]["temperature_health"]
            self.assertEqual(health_metric["value"], "温度告警")
            self.assertEqual(health_metric["source"], "telemetry")
            self.assertEqual(health_metric["state"], "live")

    def test_monitor_overview_capacitor_bank_temperature_warning_margin_is_configurable(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="补偿器温度边距配置测试",
                sn="CAP-TEMP-002",
                device_type="compensation",
                device_subtype="capacitor_bank_controller",
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
                consumption=12.0,
                flow_rate=21.0,
                timestamp=now - timedelta(minutes=1),
                temperature=54.0,
            )
            session.add(
                CapacitorBankControlProfile(
                    device_id=device.id,
                    source="telemetry",
                    snapshot_timestamp=now,
                    temperature_upper_limit=55.0,
                )
            )
            session.commit()

            with patch(
                "app.services.devices.compensation.monitor_service.settings.compensation_temperature_warning_margin_c",
                0.5,
            ):
                overview = DeviceMonitorService.get_monitor_overview(session, device.id)

            health_metric = overview["compensation_monitor"]["key_metrics"]["temperature_health"]
            self.assertEqual(health_metric["value"], "正常")
            self.assertEqual(health_metric["source"], "profile")
            self.assertEqual(health_metric["state"], "live")

    def test_monitor_overview_returns_svg_compensation_monitor_semantics(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="SVG 语义测试",
                sn="SVG-MON-001",
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

            EnergyService.save_energy_data(
                session=session,
                device_id=device.id,
                energy_type=device.energy_type,
                consumption=16.0,
                flow_rate=28.0,
                timestamp=now - timedelta(minutes=1),
                reactive_power=42.0,
                power_factor=0.99,
                voltage=398.0,
                current=38.0,
            )
            session.add(
                SVGTelemetry(
                    device_id=device.id,
                    timestamp=now,
                    auto_mode=True,
                    capacity_utilization=64.5,
                    cabinet_temp=35.6,
                    svg_reactive_output=48.0,
                )
            )
            session.commit()

            overview = DeviceMonitorService.get_monitor_overview(session, device.id)
            compensation_monitor = overview["compensation_monitor"]

            self.assertEqual(compensation_monitor["subtype"], "svg")
            self.assertEqual(compensation_monitor["control_mode"]["value"], "自动")
            self.assertEqual(compensation_monitor["control_mode"]["source"], "telemetry")
            self.assertEqual(compensation_monitor["key_metrics"]["capacity_utilization"]["value"], 64.5)
            self.assertEqual(compensation_monitor["key_metrics"]["cabinet_temperature"]["value"], 35.6)

    def test_monitor_overview_svg_circuit_summary_prefers_asset_profile_module_count(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="SVG 模块数测试",
                sn="SVG-MON-002",
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

            session.add(
                SVGAssetProfile(
                    device_id=device.id,
                    module_count=12,
                )
            )
            session.add(
                SVGTelemetry(
                    device_id=device.id,
                    timestamp=now,
                    capacity_utilization=50.0,
                    auto_mode=True,
                )
            )
            session.commit()

            overview = DeviceMonitorService.get_monitor_overview(session, device.id)
            compensation_monitor = overview["compensation_monitor"]

            self.assertEqual(compensation_monitor["circuit_summary"]["total_count"], 12)
            self.assertEqual(compensation_monitor["circuit_summary"]["running_count"], 6)

    def test_monitor_overview_non_compensation_device_does_not_return_compensation_monitor(self):
        with Session(self.engine) as session:
            device = Device(
                name="普通负荷",
                sn="LOAD-002",
                device_type="load",
                device_category="load",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            overview = DeviceMonitorService.get_monitor_overview(session, device.id)

            self.assertIsNone(overview["compensation_monitor"])

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
