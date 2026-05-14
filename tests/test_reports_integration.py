import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import reports
from app.models.tables import UserRole


class ReportIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(reports.router, prefix="/reports")
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()

    def test_energy_detail_export_csv(self):
        fake_user = SimpleNamespace(username="admin", role=UserRole.ADMIN)
        fake_rows = [
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
            )
        ]
        self.app.dependency_overrides[reports.get_session] = lambda: object()
        self.app.dependency_overrides[reports.get_current_user] = lambda: fake_user
        self.app.dependency_overrides[reports.limit_requests(
            bucket="report-export",
            max_calls=reports.settings.report_export_rate_limit_count,
            window_seconds=reports.settings.report_export_rate_limit_window_seconds,
        )] = lambda: None

        with patch.object(
            reports,
            "build_report_csv_export_use_case",
            return_value=SimpleNamespace(filename="energy_detail_20260326.csv", content="时间,设备ID,设备名称\n2026-03-26 10:00:00,1,一号设备\n"),
        ):
            response = self.client.get("/reports/export_csv", params={"report_type": "energy_detail"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("设备名称", response.text)
        self.assertIn("一号设备", response.text)

    def test_alarm_history_export_csv(self):
        fake_user = SimpleNamespace(username="admin", role=UserRole.ADMIN)
        fake_rows = [
            (
                SimpleNamespace(
                    timestamp=SimpleNamespace(strftime=lambda fmt: "2026-03-26 10:00:00"),
                    device_id=2,
                    severity="critical",
                    is_resolved=False,
                    message="通讯中断",
                    resolved_by=None,
                    resolved_at=None,
                ),
                "二号设备",
            )
        ]
        self.app.dependency_overrides[reports.get_session] = lambda: object()
        self.app.dependency_overrides[reports.get_current_user] = lambda: fake_user
        self.app.dependency_overrides[reports.limit_requests(
            bucket="report-export",
            max_calls=reports.settings.report_export_rate_limit_count,
            window_seconds=reports.settings.report_export_rate_limit_window_seconds,
        )] = lambda: None

        with patch.object(
            reports,
            "build_report_csv_export_use_case",
            return_value=SimpleNamespace(filename="alarm_history_20260326.csv", content="时间,设备ID,设备名称,严重级别,是否已恢复,消息\n2026-03-26 10:00:00,2,二号设备,critical,否,通讯中断\n"),
        ):
            response = self.client.get("/reports/export_csv", params={"report_type": "alarm_history"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("通讯中断", response.text)

    def test_multi_energy_summary_export_csv(self):
        fake_user = SimpleNamespace(username="admin", role=UserRole.ADMIN)
        self.app.dependency_overrides[reports.get_session] = lambda: object()
        self.app.dependency_overrides[reports.get_current_user] = lambda: fake_user
        self.app.dependency_overrides[reports.limit_requests(
            bucket="report-export",
            max_calls=reports.settings.report_export_rate_limit_count,
            window_seconds=reports.settings.report_export_rate_limit_window_seconds,
        )] = lambda: None

        with patch.object(
            reports,
            "build_report_csv_export_use_case",
            return_value=SimpleNamespace(
                filename="multi_energy_summary_20260326.csv",
                content="能源类型,周期消耗,累计单位\n电,12.3,kWh\n",
            ),
        ):
            response = self.client.get(
                "/reports/export_csv",
                params={
                    "report_type": "multi_energy_summary",
                    "start_time": "2026-03-26T00:00:00",
                    "end_time": "2026-03-26T23:59:59",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("能源类型", response.text)
        self.assertIn("电", response.text)

    def test_device_history_export_requires_device_id(self):
        fake_user = SimpleNamespace(username="admin", role=UserRole.ADMIN)
        self.app.dependency_overrides[reports.get_session] = lambda: object()
        self.app.dependency_overrides[reports.get_current_user] = lambda: fake_user
        self.app.dependency_overrides[reports.limit_requests(
            bucket="report-export",
            max_calls=reports.settings.report_export_rate_limit_count,
            window_seconds=reports.settings.report_export_rate_limit_window_seconds,
        )] = lambda: None

        response = self.client.get("/reports/export_csv", params={"report_type": "device_history"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("device_history 需要提供 device_id", response.text)

    def test_device_history_fields_returns_template(self):
        fake_user = SimpleNamespace(username="admin", role=UserRole.ADMIN)
        self.app.dependency_overrides[reports.get_session] = lambda: object()
        self.app.dependency_overrides[reports.get_current_user] = lambda: fake_user

        with patch.object(
            reports,
            "build_device_history_field_config_use_case",
            return_value={
                "device_id": 8,
                "template": "capacitor_bank_controller",
                "required_fields": ["timestamp"],
                "default_fields": ["device_name", "reactive_power_a"],
                "groups": [
                    {
                        "key": "compensation_effect",
                        "label": "补偿效果",
                        "fields": [
                            {"key": "reactive_power_a", "label": "A相无功(kvar)", "default": True},
                            {"key": "power_factor_a", "label": "A相功率因数", "default": True},
                        ],
                    },
                    {
                        "key": "switching",
                        "label": "投切状态",
                        "fields": [
                            {"key": "running_circuit_count", "label": "当前投入回路总数", "default": True},
                        ],
                    },
                ],
            },
        ):
            response = self.client.get("/reports/device-history-fields", params={"device_id": 8})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["template"], "capacitor_bank_controller")
        labels = [
            field["label"]
            for group in response.json()["groups"]
            for field in group["fields"]
        ]
        self.assertIn("A相无功(kvar)", labels)
        self.assertIn("当前投入回路总数", labels)

    def test_device_history_export_passes_fields_to_use_case(self):
        fake_user = SimpleNamespace(username="admin", role=UserRole.ADMIN)
        self.app.dependency_overrides[reports.get_session] = lambda: object()
        self.app.dependency_overrides[reports.get_current_user] = lambda: fake_user
        self.app.dependency_overrides[reports.limit_requests(
            bucket="report-export",
            max_calls=reports.settings.report_export_rate_limit_count,
            window_seconds=reports.settings.report_export_rate_limit_window_seconds,
        )] = lambda: None

        with patch.object(
            reports,
            "build_report_csv_export_use_case",
            return_value=SimpleNamespace(filename="device_history_8_20260514.csv", content="时间,设备名称\n2026-05-14,无功补偿控制器\n"),
        ) as mock_export:
            response = self.client.get(
                "/reports/export_csv",
                params={
                    "report_type": "device_history",
                    "device_id": 8,
                    "fields": "device_name,reactive_power_a",
                },
            )

        self.assertEqual(response.status_code, 200)
        mock_export.assert_called_once()
        self.assertEqual(mock_export.call_args.kwargs["fields"], "device_name,reactive_power_a")


if __name__ == "__main__":
    unittest.main()
