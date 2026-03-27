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


if __name__ == "__main__":
    unittest.main()
