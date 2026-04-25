import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints import analysis
from app.api.endpoints import inspection
from app.api.endpoints import maintenance
from app.api.endpoints import users
from app.api.endpoints.devices import data as device_data
from app.api.endpoints.devices import management


class TestEndpointApplicationConvergence(unittest.TestCase):
    @patch("app.api.endpoints.devices.data.report_device_data_use_case")
    def test_report_device_data_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        request = SimpleNamespace(
            model_dump=lambda exclude_none=True: {"consumption": 3.2, "power": 1.5},
            timestamp=datetime(2026, 3, 27, 10, 0, 0),
        )
        expected = SimpleNamespace(device_id=1)
        mock_use_case.return_value = expected

        result = device_data.report_device_data(
            device_id=1,
            req=request,
            session=session,
            current_user=current_user,
            _=None,
        )

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            device_id=1,
            data={"consumption": 3.2, "power": 1.5},
            timestamp=request.timestamp,
        )

    @patch("app.api.endpoints.analysis.analyze_device_use_case")
    def test_analysis_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        mock_use_case.return_value = {"device_id": 7, "today_energy": 1.23}

        result = analysis.analyze_device(
            device_id=7,
            session=session,
            current_user=current_user,
        )

        self.assertEqual(result["device_id"], 7)
        mock_use_case.assert_called_once_with(session, current_user, 7)

    @patch("app.api.endpoints.energy.data.get_energy_analysis_overview_use_case")
    @patch("app.api.endpoints.energy.data.EnergyService")
    @patch("app.api.endpoints.energy.data.get_allowed_device_ids")
    def test_energy_overview_endpoint_includes_analysis_block(
        self,
        mock_allowed,
        mock_energy_service,
        mock_analysis_use_case,
    ):
        from app.api.endpoints.energy import data as energy_data

        session = object()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        start_time = datetime(2026, 4, 1, 0, 0, 0)
        end_time = datetime(2026, 4, 8, 0, 0, 0)
        mock_allowed.return_value = None
        mock_energy_service.get_statistics_by_type.return_value = {}
        mock_energy_service.get_carbon_summary.return_value = {"total_carbon": 0, "by_energy_type": {}}
        mock_energy_service.get_energy_type_profile.return_value = {}
        mock_analysis_use_case.return_value = {
            "time_window": {"granularity": "day"},
            "summary": {"device_count": 4},
            "trend": {
                "items": [
                    {
                        "timestamp": "2026-04-01T00:00:00",
                        "total_consumption": 12.5,
                        "total_load": 3.2,
                    }
                ]
            },
            "comparison": {
                "period_over_period": {
                    "current_total_consumption": 12.5,
                    "previous_total_consumption": 10,
                    "change_rate": 0.25,
                },
                "energy_categories": [{"energy_category": "water", "ratio": 1}],
            },
            "ranking": {"areas": [{"name": "一区"}], "buildings": [], "devices": []},
            "anomaly": {"summary": {"data_gap_count": 1, "ingestion_failure_count": 2, "active_alarm_count": 3}, "items": []},
            "insights": [{"title": "水务占比最高", "detail": "当前周期水务为主导能源"}],
            "scope": {},
        }

        result = energy_data.get_energy_overview(
            start_time=start_time,
            end_time=end_time,
            device_id=None,
            location_id=8,
            energy_type="water",
            top_n=7,
            granularity="hour",
            include_analysis=True,
            session=session,
            current_user=current_user,
        )

        self.assertEqual(result["summary"]["device_count"], 4)
        self.assertEqual(result["trend"]["granularity"], "day")
        self.assertEqual(result["trend"]["points"][0]["value"], 12.5)
        self.assertEqual(result["trend"]["points"][0]["load"], 3.2)
        self.assertEqual(result["comparison"]["current"], 12.5)
        self.assertEqual(result["comparison"]["previous"], 10)
        self.assertEqual(result["comparison"]["ratio"], 0.25)
        self.assertEqual(result["comparison"]["mix"][0]["energy_type"], "water")
        self.assertEqual(result["ranking"]["regions"][0]["name"], "一区")
        self.assertEqual(result["anomaly"]["missing_data"], 1)
        self.assertEqual(result["anomaly"]["consecutive_failures"], 2)
        self.assertEqual(result["anomaly"]["unresolved_alarms"], 3)
        self.assertEqual(result["insights"], ["水务占比最高：当前周期水务为主导能源"])
        mock_analysis_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            start_time=start_time,
            end_time=end_time,
            device_id=None,
            location_id=8,
            energy_type="water",
            top_n=7,
            granularity="hour",
        )

    @patch("app.api.endpoints.inspection.create_inspection_task_use_case")
    def test_inspection_create_task_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="maintainer", role="maintainer")
        request = SimpleNamespace(
            route_id=4,
            task_date=datetime(2026, 4, 7, 9, 0, 0),
            plan_id=8,
            inspector="alice",
        )
        expected = SimpleNamespace(id=10)
        mock_use_case.return_value = expected

        result = inspection.create_task(
            req=request,
            session=session,
            current_user=current_user,
        )

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            route_id=4,
            task_date=request.task_date,
            plan_id=8,
            inspector="alice",
        )

    @patch("app.api.endpoints.maintenance.create_maintenance_record_use_case")
    def test_maintenance_create_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="maintainer", role="maintainer")
        request = SimpleNamespace(
            device_id=3,
            maintenance_type="routine",
            scheduled_time=datetime(2026, 4, 7, 10, 0, 0),
            title="季度保养",
            description="desc",
            operator="bob",
            created_by=None,
        )
        expected = SimpleNamespace(id=12)
        mock_use_case.return_value = expected

        result = maintenance.create_maintenance(
            request=request,
            session=session,
            current_user=current_user,
        )

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            device_id=3,
            maintenance_type="routine",
            scheduled_time=request.scheduled_time,
            title="季度保养",
            description="desc",
            operator="bob",
            created_by=None,
        )

    @patch("app.api.endpoints.devices.management.create_device_smart_use_case")
    def test_device_management_create_smart_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="maintainer", role="maintainer")
        request = SimpleNamespace(
            name="1号水表",
            sn="WM-001",
            device_type="water_meter",
            location="北区",
            description="说明",
            rated_capacity=12.5,
        )
        expected = SimpleNamespace(id=30)
        mock_use_case.return_value = expected

        result = management.create_device_smart(
            req=request,
            session=session,
            current_user=current_user,
        )

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            name="1号水表",
            sn="WM-001",
            device_type="water_meter",
            location="北区",
            description="说明",
            rated_capacity=12.5,
        )

    @patch("app.api.endpoints.devices.management.toggle_device_status_use_case")
    def test_device_management_toggle_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="operator", role="operator")
        expected = SimpleNamespace(id=31, is_active=False)
        mock_use_case.return_value = expected

        result = management.toggle_device_status(
            device_id=31,
            active=False,
            reason=None,
            session=session,
            current_user=current_user,
            _=None,
        )

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            device_id=31,
            active=False,
            reason=None,
        )

    @patch("app.api.endpoints.users.create_user_use_case")
    def test_users_create_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        request = SimpleNamespace(
            username="alice",
            password="StrongPass123!",
            role="viewer",
            location_scope="1,2",
            is_active=True,
        )
        expected = SimpleNamespace(username="alice")
        mock_use_case.return_value = expected

        result = users.create_user(
            request=request,
            session=session,
            current_user=current_user,
        )

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            username="alice",
            password="StrongPass123!",
            role="viewer",
            is_active=True,
            location_scope="1,2",
        )

    @patch("app.api.endpoints.users.revoke_user_sessions_use_case")
    def test_users_revoke_sessions_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        mock_use_case.return_value = SimpleNamespace(message="用户 alice 已被强制下线")

        result = users.revoke_user_sessions(
            user_id=9,
            session=session,
            current_user=current_user,
        )

        self.assertEqual(result["message"], "用户 alice 已被强制下线")
        mock_use_case.assert_called_once_with(session, current_user, 9)

    @patch("app.api.endpoints.users.change_my_password_use_case")
    def test_users_change_my_password_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(id=6, username="alice", role="viewer")
        request = SimpleNamespace(current_password="OldPass123!", new_password="NewPass123!")
        mock_use_case.return_value = SimpleNamespace(message="密码已更新")

        result = users.change_my_password(
            request=request,
            session=session,
            current_user=current_user,
        )

        self.assertEqual(result["message"], "密码已更新")
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            current_password="OldPass123!",
            new_password="NewPass123!",
        )


if __name__ == "__main__":
    unittest.main()
