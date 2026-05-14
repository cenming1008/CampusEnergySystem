import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.application.analysis import analyze_device_use_case, get_energy_analysis_overview_use_case
from app.application.device_reporting import report_device_data_use_case
from app.application.device_reporting import (
    get_device_data_use_case,
    get_device_statistics_use_case,
)
from app.application.energy_management import (
    get_carbon_summary_use_case,
    get_energy_statistics_use_case,
    save_energy_data_use_case,
)
from app.application.reporting import list_energy_report_rows_use_case
from app.application.reporting import build_device_history_field_config_use_case
from app.application.reporting import build_report_csv_export_use_case
from app.application.telemetry_ingestion import ingest_telemetry_use_case
from app.core.exceptions import PermissionDeniedException
from app.services.report_service import ReportService


class TestApplicationUseCases(unittest.TestCase):
    @patch("app.application.device_reporting.audit_log")
    @patch("app.application.device_reporting.EnergyService.save_energy_data")
    @patch("app.application.device_reporting.normalize_device_report_payload")
    @patch("app.application.device_reporting.ensure_device_access")
    def test_report_device_data_use_case_orchestrates_access_audit_and_energy_save(
        self,
        mock_ensure_access,
        mock_normalize_payload,
        mock_save_energy_data,
        mock_audit_log,
    ):
        session = MagicMock()
        current_user = SimpleNamespace(username="admin", role="admin")
        mock_ensure_access.return_value = SimpleNamespace(device_type="load", energy_type="electricity")
        mock_normalize_payload.return_value = SimpleNamespace(
            consumption=1.2,
            flow_rate=0.8,
            optional_fields={"voltage": 220.0},
        )
        fake_record = SimpleNamespace(device_id=1)
        mock_save_energy_data.return_value = fake_record

        result = report_device_data_use_case(
            session=session,
            current_user=current_user,
            device_id=1,
            data={"consumption": 1.2, "power": 0.8},
            timestamp=datetime(2026, 3, 24, 12, 0, 0),
        )

        self.assertIs(result, fake_record)
        mock_ensure_access.assert_called_once_with(session, current_user, 1)
        mock_save_energy_data.assert_called_once()
        mock_audit_log.assert_called_once()

    @patch("app.application.device_reporting.DeviceService.get_device_data")
    @patch("app.application.device_reporting.ensure_device_access")
    def test_get_device_data_use_case_checks_access_then_reads_service(self, mock_ensure_access, mock_get_device_data):
        session = MagicMock()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        fake_rows = [SimpleNamespace(device_id=1)]
        mock_get_device_data.return_value = fake_rows

        result = get_device_data_use_case(
            session=session,
            current_user=current_user,
            device_id=1,
            start_time=datetime(2026, 3, 24, 0, 0, 0),
            end_time=datetime(2026, 3, 24, 23, 59, 59),
            limit=200,
        )

        self.assertEqual(result, fake_rows)
        mock_ensure_access.assert_called_once_with(session, current_user, 1)
        mock_get_device_data.assert_called_once()

    @patch("app.application.device_reporting.DeviceService.get_device_semantic_profile")
    @patch("app.application.device_reporting.DeviceService.get_device_statistics")
    @patch("app.application.device_reporting.ensure_device_access")
    def test_get_device_statistics_use_case_checks_access_then_reads_service(
        self,
        mock_ensure_access,
        mock_get_device_statistics,
        mock_get_device_semantic_profile,
    ):
        session = MagicMock()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        mock_get_device_statistics.return_value = {"total_consumption": 42}
        mock_get_device_semantic_profile.return_value = {"device_type": "load"}

        result = get_device_statistics_use_case(
            session=session,
            current_user=current_user,
            device_id=1,
            start_time=datetime(2026, 3, 24, 0, 0, 0),
            end_time=datetime(2026, 3, 24, 23, 59, 59),
            period_type="day",
        )

        self.assertEqual(result["total_consumption"], 42)
        self.assertEqual(result["device_semantics"]["device_type"], "load")
        mock_ensure_access.assert_called_once_with(session, current_user, 1)
        mock_get_device_statistics.assert_called_once()

    @patch("app.application.telemetry_ingestion.IngestionHealthService.mark_ingestion_success")
    @patch("app.application.telemetry_ingestion.AlarmService.check_and_create_alarm")
    @patch("app.application.telemetry_ingestion.report_device_data_ingestion_use_case")
    @patch("app.application.telemetry_ingestion.IngestionHealthService.mark_message_received")
    def test_ingest_telemetry_use_case_orchestrates_services(
        self,
        mock_mark_message_received,
        mock_report_device_data,
        mock_check_and_create_alarm,
        mock_mark_ingestion_success,
    ):
        session = MagicMock()
        timestamp = datetime(2026, 3, 24, 12, 0, 0)
        mock_report_device_data.return_value = SimpleNamespace(
            voltage=380.0,
            current=12.0,
            flow_rate=4.56,
            consumption=8.9,
            timestamp=timestamp,
        )

        result = ingest_telemetry_use_case(
            session=session,
            device_id=7,
            data={"consumption": 8.9, "power": 4.56},
            timestamp=timestamp,
        )

        self.assertEqual(result.broadcast_data.device_id, 7)
        self.assertEqual(result.broadcast_data.power, 4.56)
        mock_mark_message_received.assert_called_once()
        mock_report_device_data.assert_called_once()
        mock_check_and_create_alarm.assert_called_once()
        mock_mark_ingestion_success.assert_called_once()

    @patch("app.application.telemetry_ingestion.IngestionHealthService.mark_ingestion_success")
    @patch("app.application.telemetry_ingestion.AlarmService.check_and_create_alarm")
    @patch("app.application.telemetry_ingestion.report_device_data_ingestion_use_case")
    @patch("app.application.telemetry_ingestion.IngestionHealthService.mark_message_received")
    def test_ingest_telemetry_use_case_uses_receive_time_for_online_health(
        self,
        mock_mark_message_received,
        mock_report_device_data,
        mock_check_and_create_alarm,
        mock_mark_ingestion_success,
    ):
        session = MagicMock()
        stale_device_timestamp = datetime(2026, 3, 24, 12, 0, 0)
        mock_report_device_data.return_value = SimpleNamespace(
            voltage=380.0,
            current=12.0,
            flow_rate=4.56,
            consumption=8.9,
            timestamp=stale_device_timestamp,
        )

        ingest_telemetry_use_case(
            session=session,
            device_id=7,
            data={"consumption": 8.9, "power": 4.56},
            timestamp=stale_device_timestamp,
        )

        mock_mark_message_received.assert_called_once_with(session, device_id=7)
        mock_mark_ingestion_success.assert_called_once_with(session, device_id=7)
        mock_report_device_data.assert_called_once_with(
            session=session,
            device_id=7,
            data={"consumption": 8.9, "power": 4.56},
            timestamp=stale_device_timestamp,
        )
        mock_check_and_create_alarm.assert_called_once_with(
            session=session,
            device_id=7,
            data={"consumption": 8.9, "power": 4.56},
            timestamp=stale_device_timestamp,
        )

    @patch("app.application.analysis.AnalysisService.analyze_device")
    @patch("app.application.analysis.ensure_device_access")
    def test_analyze_device_use_case_builds_response_in_application(self, mock_ensure_access, mock_analyze_device):
        session = MagicMock()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        mock_analyze_device.return_value = {
            "is_active": True,
            "energy_type": "gas",
            "semantics": {
                "label": "气",
                "flow_label": "实时流量",
                "flow_unit": "m³/h",
                "supports_electrical_quality": False,
                "consumption_label": "累计气量",
                "consumption_unit": "m³",
                "consumption_stat_basis": "period_delta_from_cumulative_reading",
            },
            "latest": SimpleNamespace(flow_rate=4.567, voltage=219.95, current=10.127),
            "today_consumption": 9.812,
            "today_cost": 5.436,
        }

        result = analyze_device_use_case(session=session, current_user=current_user, device_id=7)

        self.assertEqual(result["device_id"], 7)
        self.assertEqual(result["energy_type"], "gas")
        self.assertEqual(result["today_energy"], 9.81)
        self.assertEqual(result["current_power"], 4.57)
        self.assertEqual(result["today_consumption_unit"], "m³")
        mock_ensure_access.assert_called_once_with(session, current_user, 7)
        mock_analyze_device.assert_called_once_with(session, 7)

    @patch("app.application.analysis.EnergyService.get_analysis_overview")
    @patch("app.application.analysis.get_allowed_device_ids")
    @patch("app.application.analysis.ensure_location_access")
    def test_energy_analysis_overview_use_case_checks_scope_and_delegates(
        self,
        mock_ensure_location_access,
        mock_get_allowed_device_ids,
        mock_get_overview,
    ):
        session = MagicMock()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        start_time = datetime(2026, 4, 1, 0, 0, 0)
        end_time = datetime(2026, 4, 8, 0, 0, 0)
        mock_get_allowed_device_ids.return_value = {1, 2, 3}
        mock_get_overview.return_value = {"summary": {"device_count": 3}}

        result = get_energy_analysis_overview_use_case(
            session=session,
            current_user=current_user,
            start_time=start_time,
            end_time=end_time,
            device_id=2,
            location_id=9,
            energy_type="electricity",
            top_n=6,
            granularity="hour",
        )

        self.assertEqual(result["summary"]["device_count"], 3)
        mock_ensure_location_access.assert_called_once_with(session, current_user, 9)
        mock_get_allowed_device_ids.assert_called_once_with(session, current_user)
        mock_get_overview.assert_called_once_with(
            session=session,
            start_time=start_time,
            end_time=end_time,
            allowed_device_ids={1, 2, 3},
            device_id=2,
            location_id=9,
            energy_type="electricity",
            top_n=6,
            granularity="hour",
        )

    @patch("app.application.reporting.ReportService.list_energy_report_rows")
    def test_list_energy_report_rows_use_case_delegates_to_report_service(self, mock_list_rows):
        session = MagicMock()
        mock_list_rows.return_value = [(SimpleNamespace(device_id=1), "Device A")]

        result = list_energy_report_rows_use_case(session=session, limit=123)

        self.assertEqual(len(result), 1)
        mock_list_rows.assert_called_once_with(
            session=session,
            current_user=None,
            device_id=None,
            energy_type=None,
            start_time=None,
            end_time=None,
            limit=123,
        )

    @patch("app.application.reporting.list_energy_report_rows_use_case")
    def test_build_report_csv_export_use_case_builds_csv_payload(self, mock_list_energy_rows):
        session = MagicMock()
        mock_list_energy_rows.return_value = [
            (
                SimpleNamespace(
                    timestamp=SimpleNamespace(strftime=lambda fmt: "2026-03-26 10:00:00"),
                    device_id=1,
                    energy_type="electricity",
                    voltage=380.0,
                    current=10.0,
                    flow_rate=5.5,
                    consumption=12.3,
                ),
                "一号设备",
                "load",
                "load",
            )
        ]

        payload = build_report_csv_export_use_case(
            session=session,
            current_user=None,
            report_type="energy_detail",
            limit=10,
        )

        self.assertEqual(payload.filename, f"energy_detail_{datetime.now().strftime('%Y%m%d')}.csv")
        self.assertIn("设备名称", payload.content)
        self.assertIn("一号设备", payload.content)
        self.assertIn("对象语义", payload.content)

    def test_build_report_csv_export_use_case_requires_device_for_device_history(self):
        session = MagicMock()

        with self.assertRaisesRegex(ValueError, "device_history 需要提供 device_id"):
            build_report_csv_export_use_case(
                session=session,
                current_user=None,
                report_type="device_history",
                limit=10,
            )

    @patch("app.application.reporting.ReportService.list_device_history_report_rows")
    def test_build_report_csv_export_use_case_exports_generic_device_history(self, mock_history_rows):
        session = MagicMock()
        mock_history_rows.return_value = {
            "device": SimpleNamespace(
                id=7,
                name="总进线电表",
                device_type="meter",
                device_category="meter",
                device_subtype=None,
            ),
            "history_kind": "energy",
            "rows": [
                SimpleNamespace(
                    timestamp=SimpleNamespace(strftime=lambda fmt: "2026-05-14 09:00:00"),
                    device_id=7,
                    energy_type="electricity",
                    voltage=380.0,
                    current=12.5,
                    flow_rate=8.6,
                    consumption=123.4,
                )
            ],
        }

        payload = build_report_csv_export_use_case(
            session=session,
            current_user=None,
            report_type="device_history",
            device_id=7,
            limit=10,
        )

        self.assertEqual(payload.filename, f"device_history_7_{datetime.now().strftime('%Y%m%d')}.csv")
        self.assertIn("功率/流量", payload.content)
        self.assertIn("总进线电表", payload.content)
        self.assertIn("123.4", payload.content)
        mock_history_rows.assert_called_once_with(
            session=session,
            current_user=None,
            device_id=7,
            start_time=None,
            end_time=None,
            limit=10,
        )

    @patch("app.application.reporting.ReportService.get_device_for_history_report")
    def test_build_device_history_field_config_returns_generic_template(self, mock_get_device):
        session = MagicMock()
        mock_get_device.return_value = SimpleNamespace(
            id=7,
            device_subtype=None,
        )

        payload = build_device_history_field_config_use_case(
            session=session,
            current_user=None,
            device_id=7,
        )

        self.assertEqual(payload["template"], "generic_energy")
        self.assertIn("timestamp", payload["required_fields"])
        self.assertIn("flow_rate", payload["default_fields"])
        self.assertEqual(payload["groups"][0]["label"], "基础信息")

    @patch("app.application.reporting.ReportService.get_device_for_history_report")
    def test_build_device_history_field_config_returns_capacitor_bank_template(self, mock_get_device):
        session = MagicMock()
        mock_get_device.return_value = SimpleNamespace(
            id=8,
            device_subtype="capacitor_bank_controller",
        )

        payload = build_device_history_field_config_use_case(
            session=session,
            current_user=None,
            device_id=8,
        )

        self.assertEqual(payload["template"], "capacitor_bank_controller")
        labels = [
            field["label"]
            for group in payload["groups"]
            for field in group["fields"]
        ]
        self.assertIn("A相无功(kvar)", labels)
        self.assertIn("A相功率因数", labels)
        self.assertIn("当前投入回路总数", labels)

    @patch("app.application.reporting.ReportService.list_device_history_report_rows")
    def test_build_report_csv_export_use_case_exports_capacitor_bank_history(self, mock_history_rows):
        session = MagicMock()
        mock_history_rows.return_value = {
            "device": SimpleNamespace(
                id=8,
                name="无功补偿控制器",
                device_type="compensation",
                device_category="compensation",
                device_subtype="capacitor_bank_controller",
            ),
            "history_kind": "capacitor_bank",
            "rows": [
                SimpleNamespace(
                    timestamp=SimpleNamespace(strftime=lambda fmt: "2026-05-14 09:05:00"),
                    device_id=8,
                    voltage_a=221.0,
                    voltage_b=222.0,
                    voltage_c=223.0,
                    current_a=10.0,
                    current_b=11.0,
                    current_c=12.0,
                    power_factor_a=0.96,
                    power_factor_b=0.97,
                    power_factor_c=0.98,
                    active_power_a=1.1,
                    active_power_b=1.2,
                    active_power_c=1.3,
                    reactive_power_a=2.1,
                    reactive_power_b=2.2,
                    reactive_power_c=2.3,
                    apparent_power_a=3.1,
                    apparent_power_b=3.2,
                    apparent_power_c=3.3,
                    voltage_thd_a=4.1,
                    voltage_thd_b=4.2,
                    voltage_thd_c=4.3,
                    current_harmonic_a=5.1,
                    current_harmonic_b=5.2,
                    current_harmonic_c=5.3,
                    frequency=50.0,
                    temperature=31.5,
                    split_circuit_running_count=2,
                    common_circuit_running_count=3,
                    running_circuit_count=5,
                    control_mode="auto",
                    last_auto_action="switch_on",
                )
            ],
        }

        payload = build_report_csv_export_use_case(
            session=session,
            current_user=None,
            report_type="device_history",
            device_id=8,
            limit=10,
        )

        self.assertIn("A相无功(kvar)", payload.content)
        self.assertIn("B相功率因数", payload.content)
        self.assertIn("当前投入回路总数", payload.content)
        self.assertIn("无功补偿控制器", payload.content)
        self.assertIn("2.1", payload.content)

    @patch("app.application.reporting.ReportService.list_device_history_report_rows")
    def test_build_report_csv_export_use_case_limits_device_history_to_selected_fields(self, mock_history_rows):
        session = MagicMock()
        mock_history_rows.return_value = {
            "device": SimpleNamespace(
                id=8,
                name="无功补偿控制器",
                device_type="compensation",
                device_category="compensation",
                device_subtype="capacitor_bank_controller",
            ),
            "history_kind": "capacitor_bank",
            "rows": [
                SimpleNamespace(
                    timestamp=SimpleNamespace(strftime=lambda fmt: "2026-05-14 09:05:00"),
                    device_id=8,
                    reactive_power_a=2.1,
                    power_factor_a=0.96,
                    running_circuit_count=5,
                )
            ],
        }

        payload = build_report_csv_export_use_case(
            session=session,
            current_user=None,
            report_type="device_history",
            device_id=8,
            fields="device_name,reactive_power_a,running_circuit_count",
            limit=10,
        )

        first_line = payload.content.splitlines()[0]
        self.assertEqual(first_line, "时间,设备名称,A相无功(kvar),当前投入回路总数")
        self.assertIn("2026-05-14 09:05:00,无功补偿控制器,2.1,5", payload.content)
        self.assertNotIn("A相功率因数", payload.content)

    def test_build_report_csv_export_use_case_rejects_invalid_device_history_field(self):
        session = MagicMock()

        with self.assertRaisesRegex(ValueError, "不支持的导出字段: bad_field"):
            build_report_csv_export_use_case(
                session=session,
                current_user=None,
                report_type="device_history",
                device_id=8,
                fields="device_name,bad_field",
                limit=10,
            )

    @patch("app.services.report_service.ensure_device_access")
    def test_list_device_history_report_rows_checks_device_access(self, mock_ensure_access):
        session = MagicMock()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        mock_ensure_access.side_effect = PermissionDeniedException("当前用户无权访问该设备")

        with self.assertRaises(PermissionDeniedException):
            ReportService.list_device_history_report_rows(
                session=session,
                current_user=current_user,
                device_id=9,
                limit=10,
            )

        mock_ensure_access.assert_called_once_with(session, current_user, 9)

    @patch("app.application.reporting.EnergyService.get_carbon_summary")
    @patch("app.application.reporting.EnergyService.get_statistics_by_type")
    @patch("app.application.reporting.get_allowed_device_ids", return_value=None)
    @patch("app.application.reporting.EnergyService.list_energy_type_catalog")
    def test_build_report_csv_export_use_case_supports_multi_energy_summary(
        self,
        mock_catalog,
        mock_allowed_ids,
        mock_statistics,
        mock_carbon_summary,
    ):
        session = MagicMock()
        mock_catalog.return_value = [
            {"energy_type": "electricity"},
            {"energy_type": "heat"},
        ]
        mock_statistics.return_value = {
            "electricity": {
                "total_consumption": 10.5,
                "avg_flow_rate": 4.0,
                "peak_flow_rate": 6.2,
                "data_count": 3,
                "consumption_unit": "kWh",
                "flow_unit": "kW",
            },
            "heat": {
                "total_consumption": 0.0,
                "avg_flow_rate": 0.0,
                "peak_flow_rate": 0.0,
                "data_count": 0,
                "consumption_unit": "GJ",
                "flow_unit": "GJ/h",
            },
        }
        mock_carbon_summary.return_value = {
            "boundary": "display_estimate",
            "by_energy_type": {
                "electricity": {"carbon_emission": 6.13, "boundary": "display_estimate"},
            },
        }

        payload = build_report_csv_export_use_case(
            session=session,
            current_user=None,
            report_type="multi_energy_summary",
            start_time=datetime(2026, 3, 1),
            end_time=datetime(2026, 3, 2),
        )

        self.assertIn("能源类型", payload.content)
        self.assertIn("电", payload.content)
        self.assertIn("display_estimate", payload.content)

    @patch("app.application.energy_management.EnergyService.save_energy_data")
    def test_save_energy_data_use_case_delegates_to_energy_service(self, mock_save_energy_data):
        session = MagicMock()
        fake_record = SimpleNamespace(device_id=2)
        mock_save_energy_data.return_value = fake_record

        result = save_energy_data_use_case(
            session=session,
            device_id=2,
            energy_type="water",
            consumption=12.5,
            flow_rate=1.5,
        )

        self.assertIs(result, fake_record)
        mock_save_energy_data.assert_called_once()

    @patch("app.application.energy_management.EnergyService.calculate_statistics")
    def test_get_energy_statistics_use_case_delegates_to_energy_service(self, mock_calculate_statistics):
        session = MagicMock()
        mock_calculate_statistics.return_value = {"total_consumption": 5.0}

        result = get_energy_statistics_use_case(
            session=session,
            energy_type="electricity",
            start_time=datetime(2026, 3, 1),
            end_time=datetime(2026, 3, 24),
            device_id=1,
            period_type="day",
        )

        self.assertEqual(result["total_consumption"], 5.0)
        mock_calculate_statistics.assert_called_once()

    @patch("app.application.energy_management.EnergyService.get_carbon_summary")
    def test_get_carbon_summary_use_case_delegates_to_energy_service(self, mock_get_carbon_summary):
        session = MagicMock()
        mock_get_carbon_summary.return_value = {"total_carbon": 1.23}

        result = get_carbon_summary_use_case(
            session=session,
            start_time=datetime(2026, 3, 1),
            end_time=datetime(2026, 3, 24),
            device_id=1,
        )

        self.assertEqual(result["total_carbon"], 1.23)
        mock_get_carbon_summary.assert_called_once()

if __name__ == "__main__":
    unittest.main()
