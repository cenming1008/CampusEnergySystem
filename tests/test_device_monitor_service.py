import unittest
from datetime import datetime, timedelta
import os
from types import SimpleNamespace
from unittest.mock import patch

from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.devices import monitoring
from app.models.storage import StorageTelemetry
from app.models.tables import CapacitorBankControlProfile, CapacitorBankTelemetry, Device, DeviceControlLog, SVGAssetProfile, SVGTelemetry
from app.services.alarm_service import AlarmService
from app.services.device_monitor_service import DeviceMonitorService
from app.services.devices.monitor_template_service import MonitorTemplateService
from app.services.energy_service import EnergyService
from app.services.device_service import DeviceService
from app.services.ingestion_health_service import IngestionHealthService


class TestDeviceMonitorService(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(self.engine)

    def test_monitor_template_contract_matrix_covers_supported_templates(self):
        matrix = MonitorTemplateService.get_template_contract_matrix()
        expected_keys = {
            "generic_device",
            "capacitor_bank_controller",
            "svg",
            "storage",
            "water_meter",
            "gas_meter",
            "heat_meter",
            "cooling_meter",
        }

        self.assertEqual(set(matrix), expected_keys)
        for template_key, spec in matrix.items():
            self.assertEqual(spec["template_key"], template_key)
            self.assertGreaterEqual(len(spec["metric_keys"]), 1)
            self.assertGreaterEqual(len(spec["trend_keys"]), 1)
            self.assertIn("display_name", spec)
            self.assertIn("specific_panels", spec)
            self.assertIn("supports_remote_control", spec)

    def test_monitor_template_outputs_required_fields_for_all_supported_templates(self):
        cases = [
            (
                "generic_device",
                SimpleNamespace(device_category="vendor_box", device_subtype=None, device_type="vendor_box", energy_type="electricity"),
                None,
                None,
            ),
            (
                "capacitor_bank_controller",
                SimpleNamespace(
                    device_category="compensation",
                    device_subtype="capacitor_bank_controller",
                    device_type="compensation",
                    energy_type="electricity",
                ),
                {
                    "subtype": "capacitor_bank_controller",
                    "circuit_summary": {"running_count": 1, "source": "telemetry", "state": "live"},
                    "key_metrics": {
                        "capacity_utilization": {"value": 25.0, "source": "telemetry", "state": "live"},
                    },
                    "capabilities_summary": {"supports_remote_control": True},
                },
                None,
            ),
            (
                "svg",
                SimpleNamespace(device_category="compensation", device_subtype="svg", device_type="svg", energy_type="electricity"),
                {
                    "subtype": "svg",
                    "circuit_summary": {"total_count": 8, "source": "profile", "state": "live"},
                    "key_metrics": {
                        "capacity_utilization": {"value": 50.0, "source": "telemetry", "state": "live"},
                        "cabinet_temperature": {"value": 36.0, "source": "telemetry", "state": "live"},
                    },
                },
                None,
            ),
            (
                "storage",
                SimpleNamespace(device_category="storage", device_subtype=None, device_type="storage", energy_type="electricity"),
                None,
                {
                    "key_metrics": {
                        "soc": {"value": 76.0, "source": "telemetry", "state": "live"},
                    },
                },
            ),
            (
                "water_meter",
                SimpleNamespace(device_category="water_meter", device_subtype=None, device_type="water_meter", energy_type="water"),
                None,
                None,
            ),
            (
                "gas_meter",
                SimpleNamespace(device_category="gas_meter", device_subtype=None, device_type="gas_meter", energy_type="gas"),
                None,
                None,
            ),
            (
                "heat_meter",
                SimpleNamespace(device_category="heat_meter", device_subtype=None, device_type="heat_meter", energy_type="heat"),
                None,
                None,
            ),
            (
                "cooling_meter",
                SimpleNamespace(device_category="cooling_meter", device_subtype=None, device_type="cooling_meter", energy_type="cooling"),
                None,
                None,
            ),
        ]
        required_fields = {
            "monitor_template",
            "metric_cards",
            "trend_fields",
            "control_summary",
            "diagnostics_summary",
            "template_diagnostics",
        }

        for expected_key, device, compensation_monitor, storage_monitor in cases:
            with self.subTest(template=expected_key):
                payload = MonitorTemplateService.build_overview_template(
                    device=device,
                    realtime={
                        "flow_rate": 1.2,
                        "consumption": 10.0,
                        "voltage": 220.0,
                        "current": 5.0,
                        "pressure": 0.3,
                        "temperature": 22.0,
                        "reactive_power": -12.0,
                        "power_factor": 0.96,
                    },
                    runtime_status={"ingestion_status": "online", "is_online": True},
                    ingestion_health={"status": "online", "is_online": True},
                    compensation_monitor=compensation_monitor,
                    storage_monitor=storage_monitor,
                )

                self.assertTrue(required_fields.issubset(payload.keys()))
                self.assertEqual(payload["monitor_template"]["template_key"], expected_key)
                self.assertGreaterEqual(len(payload["metric_cards"]), 1)
                self.assertGreaterEqual(len(payload["trend_fields"]), 1)
                self.assertEqual(payload["template_diagnostics"]["template_key"], expected_key)

    def test_monitor_template_diagnostics_marks_partial_missing_and_offline(self):
        device = SimpleNamespace(
            device_category="water_meter",
            device_subtype=None,
            device_type="water_meter",
            energy_type="water",
        )

        partial_payload = MonitorTemplateService.build_overview_template(
            device=device,
            realtime={"flow_rate": 2.2, "consumption": 12.5, "pressure": 0.33},
            runtime_status={"ingestion_status": "online", "is_online": True},
            ingestion_health={"status": "online", "is_online": True},
        )
        partial_diagnostics = partial_payload["template_diagnostics"]
        self.assertEqual(partial_diagnostics["overall_status"], "partial")
        self.assertEqual(partial_diagnostics["metric_coverage"]["total"], 4)
        self.assertEqual(partial_diagnostics["metric_coverage"]["live"], 3)
        self.assertEqual(partial_diagnostics["metric_coverage"]["missing"], 1)
        self.assertEqual(partial_diagnostics["metric_coverage"]["missing_keys"], ["temperature"])
        self.assertEqual(
            partial_diagnostics["trend_coverage"]["drawable_keys"],
            ["flow_rate", "consumption"],
        )
        self.assertEqual(
            partial_diagnostics["trend_coverage"]["unsupported_keys"],
            ["pressure", "temperature"],
        )

        missing_payload = MonitorTemplateService.build_overview_template(
            device=device,
            realtime={},
            runtime_status={"ingestion_status": "online", "is_online": True},
            ingestion_health={"status": "online", "is_online": True},
        )
        self.assertEqual(missing_payload["template_diagnostics"]["overall_status"], "missing")

        offline_payload = MonitorTemplateService.build_overview_template(
            device=device,
            realtime={"flow_rate": 2.2, "consumption": 12.5, "pressure": 0.33, "temperature": 21.5},
            runtime_status={"ingestion_status": "offline", "is_online": False},
            ingestion_health={"status": "offline", "is_online": False},
        )
        self.assertEqual(offline_payload["template_diagnostics"]["overall_status"], "offline")

    def test_monitor_template_diagnostics_keeps_metric_coverage_consistent_for_capacitor_bank(self):
        device = SimpleNamespace(
            device_category="compensation",
            device_subtype="capacitor_bank_controller",
            device_type="compensation",
            energy_type="electricity",
        )

        payload = MonitorTemplateService.build_overview_template(
            device=device,
            realtime={
                "reactive_power": -12.0,
                "power_factor": 0.96,
                "voltage": 220.0,
            },
            runtime_status={"ingestion_status": "offline", "is_online": False},
            ingestion_health={"status": "offline", "is_online": False},
            compensation_monitor={
                "subtype": "capacitor_bank_controller",
                "circuit_summary": {},
                "key_metrics": {},
                "capabilities_summary": {"supports_remote_control": True},
            },
        )

        coverage = payload["template_diagnostics"]["metric_coverage"]
        self.assertEqual(coverage["total"], 6)
        self.assertEqual(coverage["live"], 3)
        self.assertEqual(coverage["missing"], 3)
        self.assertEqual(
            coverage["missing_keys"],
            ["current", "running_circuit_count", "capacity_utilization"],
        )
        self.assertEqual(coverage["live"] + coverage["missing"], coverage["total"])
        self.assertEqual(payload["template_diagnostics"]["overall_status"], "offline")

    def test_monitor_overview_calibrates_heat_and_cooling_meter_supply_return_delta(self):
        now = datetime.now()
        with Session(self.engine) as session:
            heat_device = Device(
                name="热量表准真实联调",
                sn="HEAT-UAT-001",
                device_type="heat_meter",
                device_category="heat_meter",
                energy_type="heat",
                is_active=True,
            )
            cooling_device = Device(
                name="冷量表准真实联调",
                sn="COOL-UAT-001",
                device_type="cooling_meter",
                device_category="cooling_meter",
                energy_type="cooling",
                is_active=True,
            )
            session.add(heat_device)
            session.add(cooling_device)
            session.commit()
            session.refresh(heat_device)
            session.refresh(cooling_device)

            DeviceService.report_device_data(
                session,
                heat_device.id,
                data={
                    "consumption": 128.4,
                    "heat_power": 52.6,
                    "supply_temp": 60.2,
                    "return_temp": 47.7,
                    "pressure": 0.41,
                },
                timestamp=now - timedelta(minutes=3),
            )
            DeviceService.report_device_data(
                session,
                cooling_device.id,
                data={
                    "consumption": 96.7,
                    "cooling_power": 44.3,
                    "supply_temp": 7.1,
                    "return_temp": 12.6,
                    "pressure": 0.37,
                },
                timestamp=now - timedelta(minutes=2),
            )
            IngestionHealthService.mark_ingestion_success(session, heat_device.id, now)
            IngestionHealthService.mark_ingestion_success(session, cooling_device.id, now)
            session.commit()

            heat_overview = DeviceMonitorService.get_monitor_overview(session, heat_device.id)
            cooling_overview = DeviceMonitorService.get_monitor_overview(session, cooling_device.id)

            self.assertEqual(heat_overview["realtime"]["heat_flow"], 52.6)
            self.assertEqual(heat_overview["realtime"]["temperature_delta"], 12.5)
            heat_metrics = {item["key"]: item for item in heat_overview["metric_cards"]}
            self.assertEqual(heat_metrics["consumption"]["unit"], "GJ")
            self.assertEqual(heat_metrics["flow_rate"]["label"], "瞬时热功率")
            self.assertEqual(heat_metrics["flow_rate"]["unit"], "kW")
            self.assertEqual(heat_metrics["supply_temp"]["value"], 60.2)
            self.assertEqual(heat_metrics["return_temp"]["value"], 47.7)
            self.assertEqual(heat_metrics["temperature_delta"]["value"], 12.5)
            self.assertEqual(heat_overview["template_diagnostics"]["overall_status"], "passed")

            self.assertIsNone(cooling_overview["realtime"]["heat_flow"])
            self.assertEqual(cooling_overview["realtime"]["temperature_delta"], 5.5)
            cooling_metrics = {item["key"]: item for item in cooling_overview["metric_cards"]}
            self.assertEqual(cooling_metrics["consumption"]["unit"], "GJ")
            self.assertEqual(cooling_metrics["flow_rate"]["label"], "瞬时冷功率")
            self.assertEqual(cooling_metrics["flow_rate"]["unit"], "kW")
            self.assertEqual(cooling_metrics["supply_temp"]["value"], 7.1)
            self.assertEqual(cooling_metrics["return_temp"]["value"], 12.6)
            self.assertEqual(cooling_metrics["temperature_delta"]["value"], 5.5)
            self.assertEqual(cooling_overview["template_diagnostics"]["overall_status"], "passed")

    def test_monitor_diagnostics_attribute_missing_svg_and_storage_fields(self):
        now = datetime.now()
        with Session(self.engine) as session:
            svg_device = Device(
                name="SVG 缺字段归因",
                sn="SVG-UAT-MISSING",
                device_type="svg",
                device_subtype="svg",
                device_category="compensation",
                energy_type="electricity",
                is_active=True,
            )
            storage_device = Device(
                name="储能缺字段归因",
                sn="ESS-UAT-MISSING",
                device_type="storage",
                device_category="storage",
                energy_type="electricity",
                is_active=True,
            )
            session.add(svg_device)
            session.add(storage_device)
            session.commit()
            session.refresh(svg_device)
            session.refresh(storage_device)

            EnergyService.save_energy_data(
                session=session,
                device_id=svg_device.id,
                energy_type=svg_device.energy_type,
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
                    device_id=svg_device.id,
                    timestamp=now,
                    auto_mode=True,
                    capacity_utilization=64.5,
                    cabinet_temp=35.6,
                )
            )
            EnergyService.save_energy_data(
                session=session,
                device_id=storage_device.id,
                energy_type=storage_device.energy_type,
                consumption=100.0,
                flow_rate=12.5,
                timestamp=now - timedelta(minutes=1),
                voltage=380.0,
                current=25.0,
                temperature=32.0,
            )
            session.add(
                StorageTelemetry(
                    device_id=storage_device.id,
                    timestamp=now,
                    soc=76.5,
                    active_power=-18.2,
                    run_state="discharging",
                )
            )
            IngestionHealthService.mark_ingestion_success(session, svg_device.id, now)
            IngestionHealthService.mark_ingestion_success(session, storage_device.id, now)
            session.commit()

            svg_diagnostics = DeviceMonitorService.get_monitor_overview(session, svg_device.id)["template_diagnostics"]
            storage_diagnostics = DeviceMonitorService.get_monitor_overview(session, storage_device.id)["template_diagnostics"]

            self.assertEqual(svg_diagnostics["overall_status"], "partial")
            self.assertEqual(svg_diagnostics["metric_coverage"]["missing_keys"], ["module_count"])
            self.assertEqual(storage_diagnostics["overall_status"], "partial")
            self.assertEqual(
                storage_diagnostics["metric_coverage"]["missing_keys"],
                ["soh", "cell_temp_max", "charge_energy_today", "discharge_energy_today"],
            )

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
            self.assertEqual(overview["archive"]["archive_status"], "complete")
            self.assertIsNone(overview["archive"]["device_subtype"])
            self.assertEqual(overview["runtime_status"]["code"], "alarm")
            self.assertEqual(overview["realtime"]["flow_rate"], 2.2)
            self.assertEqual(len(overview["recent_alarms"]), 1)
            self.assertEqual(overview["recent_alarms"][0]["source"], "telemetry")
            self.assertEqual(overview["recent_alarms"][0]["last_seen_at"], now)
            self.assertIsNone(overview["recent_alarms"][0]["recovered_at"])
            self.assertEqual(overview["monitor_template"]["template_key"], "water_meter")
            self.assertEqual(overview["monitor_template"]["category"], "water_meter")
            self.assertEqual(overview["monitor_template"]["specific_panels"], [])
            self.assertFalse(overview["control_summary"]["supports_remote_control"])
            self.assertEqual(overview["diagnostics_summary"]["ingestion_status"], "online")
            metric_by_key = {item["key"]: item for item in overview["metric_cards"]}
            self.assertEqual(metric_by_key["flow_rate"]["value"], 2.2)
            self.assertEqual(metric_by_key["flow_rate"]["state"], "live")
            self.assertEqual(metric_by_key["pressure"]["value"], 0.33)
            self.assertEqual(metric_by_key["temperature"]["value"], 21.5)

    def test_runtime_status_ignores_system_recovered_alarms(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="补偿器恢复态",
                sn="CAP-RECOVERED-001",
                device_type="capacitor_bank_controller",
                device_subtype="capacitor_bank_controller",
                device_category="compensation",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            DeviceService.report_device_data(
                session,
                device.id,
                data={
                    "consumption": 1.0,
                    "voltage": 220.0,
                    "current": 8.0,
                    "power_factor": 0.96,
                    "reactive_power": 3.2,
                },
                timestamp=now - timedelta(minutes=1),
            )
            IngestionHealthService.mark_ingestion_success(session, device.id, now)
            AlarmService.create_alarm(
                session,
                device.id,
                "A 相电压谐波超限：15.80%（门限 5.00%）",
                timestamp=now - timedelta(minutes=5),
                severity="warning",
                category="cap_voltage_thd_a",
                source="platform_rule",
                recovered_at=now - timedelta(minutes=4),
            )

            status = DeviceMonitorService.get_runtime_status(session, device.id)

            self.assertEqual(status["code"], "running")
            self.assertEqual(status["unresolved_alarm_count"], 0)

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

            self.assertEqual(overview["monitor_template"]["template_key"], "capacitor_bank_controller")
            self.assertEqual(overview["monitor_template"]["category"], "compensation")
            self.assertEqual(overview["monitor_template"]["subtype"], "capacitor_bank_controller")
            self.assertEqual(overview["monitor_template"]["display_name"], "电容补偿控制器")
            self.assertEqual(
                overview["monitor_template"]["specific_panels"],
                ["three_phase", "circuit_state", "harmonic_spectrum", "control_profile", "control_summary"],
            )
            metric_by_key = {item["key"]: item for item in overview["metric_cards"]}
            self.assertEqual(metric_by_key["reactive_power"]["value"], -32.0)
            self.assertEqual(metric_by_key["power_factor"]["value"], 0.95)
            self.assertEqual(metric_by_key["running_circuit_count"]["value"], 6)
            self.assertEqual(metric_by_key["running_circuit_count"]["source"], "telemetry")
            self.assertEqual(metric_by_key["capacity_utilization"]["value"], 25.0)
            self.assertEqual(metric_by_key["capacity_utilization"]["source"], "telemetry")
            self.assertEqual(
                [item["key"] for item in overview["trend_fields"]],
                ["reactive_power", "power_factor", "voltage", "current"],
            )
            self.assertTrue(overview["control_summary"]["supports_remote_control"])
            self.assertTrue(overview["control_summary"]["receipt_required"])
            self.assertIn("manual_switch", overview["control_summary"]["supported_commands"])

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
            session.add(
                SVGAssetProfile(
                    device_id=device.id,
                    module_count=8,
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
            self.assertEqual(overview["monitor_template"]["template_key"], "svg")
            metric_by_key = {item["key"]: item for item in overview["metric_cards"]}
            self.assertEqual(metric_by_key["capacity_utilization"]["value"], 64.5)
            self.assertEqual(metric_by_key["cabinet_temperature"]["value"], 35.6)
            self.assertEqual(metric_by_key["module_count"]["value"], 8)
            self.assertEqual(
                [item["key"] for item in overview["trend_fields"]],
                ["reactive_power", "power_factor", "voltage", "current"],
            )

    def test_monitor_overview_returns_storage_template_semantics(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="储能柜模板测试",
                sn="ESS-MON-001",
                device_type="storage",
                device_category="storage",
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
                consumption=100.0,
                flow_rate=12.5,
                timestamp=now - timedelta(minutes=1),
                voltage=380.0,
                current=25.0,
                temperature=32.0,
            )
            session.add(
                StorageTelemetry(
                    device_id=device.id,
                    timestamp=now,
                    soc=76.5,
                    soh=98.1,
                    active_power=-18.2,
                    run_state="discharging",
                    cell_temp_max=36.7,
                    charge_energy_today=42.0,
                    discharge_energy_today=38.5,
                )
            )
            session.commit()

            overview = DeviceMonitorService.get_monitor_overview(session, device.id)

            self.assertEqual(overview["monitor_template"]["template_key"], "storage")
            self.assertEqual(overview["monitor_template"]["category"], "storage")
            metric_by_key = {item["key"]: item for item in overview["metric_cards"]}
            self.assertEqual(metric_by_key["soc"]["value"], 76.5)
            self.assertEqual(metric_by_key["soh"]["value"], 98.1)
            self.assertEqual(metric_by_key["active_power"]["value"], -18.2)
            self.assertEqual(metric_by_key["run_state"]["value"], "放电中")
            self.assertEqual(metric_by_key["cell_temp_max"]["value"], 36.7)
            self.assertEqual(metric_by_key["charge_energy_today"]["value"], 42.0)
            self.assertEqual(metric_by_key["discharge_energy_today"]["value"], 38.5)
            self.assertFalse(overview["control_summary"]["supports_remote_control"])

    def test_monitor_overview_specializes_meter_templates_and_unknown_fallback(self):
        with Session(self.engine) as session:
            gas_device = Device(
                name="燃气表模板测试",
                sn="GAS-MON-001",
                device_type="gas_meter",
                device_category="gas_meter",
                energy_type="gas",
                is_active=True,
            )
            unknown_device = Device(
                name="未知设备模板测试",
                sn="UNK-MON-001",
                device_type="vendor_box",
                device_category="vendor_box",
                energy_type="electricity",
                is_active=True,
            )
            session.add(gas_device)
            session.add(unknown_device)
            session.commit()
            session.refresh(gas_device)
            session.refresh(unknown_device)

            gas_overview = DeviceMonitorService.get_monitor_overview(session, gas_device.id)
            unknown_overview = DeviceMonitorService.get_monitor_overview(session, unknown_device.id)

            self.assertEqual(gas_overview["monitor_template"]["template_key"], "gas_meter")
            self.assertEqual(
                [item["key"] for item in gas_overview["metric_cards"]],
                ["flow_rate", "consumption", "pressure"],
            )
            self.assertEqual(unknown_overview["monitor_template"]["template_key"], "generic_device")

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

            alarm = AlarmService.create_alarm(session, device.id, "通讯中断", timestamp=now - timedelta(hours=2), severity="critical")
            AlarmService.resolve_alarm(session, alarm.id, resolved_by="tester")
            DeviceService.toggle_device_status(session, device.id, False, operator="tester")

            items = DeviceMonitorService.get_status_history(session, device.id, hours=24, limit=10)

            event_types = {item["event_type"] for item in items}
            self.assertIn("alarm", event_types)
            self.assertIn("alarm_resolution", event_types)
            self.assertIn("control", event_types)
            resolution_event = next(item for item in items if item["event_type"] == "alarm_resolution")
            self.assertTrue(resolution_event["title"].startswith("告警已处理: "))

    def test_status_history_marks_system_recovered_alarm_as_recovered(self):
        now = datetime.now()
        with Session(self.engine) as session:
            device = Device(
                name="补偿器恢复历史",
                sn="CAP-HISTORY-RECOVERED",
                device_type="capacitor_bank_controller",
                device_subtype="capacitor_bank_controller",
                device_category="compensation",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            AlarmService.create_alarm(
                session,
                device.id,
                "A 相电压谐波超限：15.80%（门限 5.00%）",
                timestamp=now - timedelta(minutes=10),
                severity="warning",
                category="cap_voltage_thd_a",
                source="platform_rule",
                recovered_at=now - timedelta(minutes=9),
            )

            items = DeviceMonitorService.get_status_history(session, device.id, hours=24, limit=10)

            alarm_event = next(item for item in items if item["event_type"] == "alarm")
            recovery_event = next(item for item in items if item["event_type"] == "alarm_recovery")
            self.assertEqual(alarm_event["status"], "resolved")
            self.assertTrue(recovery_event["title"].startswith("告警已恢复: "))

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
    @patch("app.api.endpoints.devices.monitoring.get_device_monitor_overview_use_case")
    def test_monitor_overview_endpoint_keeps_reactive_power_key_for_compensator(
        self,
        mock_get_overview_use_case,
        mock_ensure_access,
    ):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        mock_get_overview_use_case.return_value = {
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
        mock_get_overview_use_case.assert_called_once_with(session=session, device_id=16)
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
