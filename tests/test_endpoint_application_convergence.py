import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints import analysis, auth, inspection, locations, maintenance, users
from app.api.endpoints.devices import data as device_data
from app.api.endpoints.devices import ingestion_health
from app.api.endpoints.devices import management
from app.api.endpoints.devices import monitoring as device_monitoring


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

    @patch("app.api.endpoints.energy.data.get_energy_overview_use_case")
    @patch("app.api.endpoints.energy.data.ensure_device_access")
    def test_energy_overview_endpoint_delegates_to_application(
        self,
        mock_ensure_access,
        mock_use_case,
    ):
        from app.api.endpoints.energy import data as energy_data

        session = object()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        start_time = datetime(2026, 4, 1, 0, 0, 0)
        end_time = datetime(2026, 4, 8, 0, 0, 0)
        expected = {"summary": {"device_count": 4}, "trend": {"points": []}}
        mock_use_case.return_value = expected

        result = energy_data.get_energy_overview(
            start_time=start_time,
            end_time=end_time,
            device_id=12,
            location_id=8,
            energy_type="water",
            top_n=7,
            granularity="hour",
            include_analysis=True,
            session=session,
            current_user=current_user,
        )

        self.assertIs(result, expected)
        mock_ensure_access.assert_called_once_with(session, current_user, 12)
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            start_time=start_time,
            end_time=end_time,
            device_id=12,
            location_id=8,
            energy_type="water",
            top_n=7,
            granularity="hour",
            include_analysis=True,
        )

    @patch("app.api.endpoints.devices.monitoring.get_device_monitor_overview_use_case")
    @patch("app.api.endpoints.devices.monitoring.ensure_device_access")
    def test_device_monitor_overview_endpoint_delegates_to_application(self, mock_ensure_access, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        expected = {"archive": {"id": 3}, "template_diagnostics": {"overall_status": "passed"}}
        mock_use_case.return_value = expected

        result = device_monitoring.get_device_monitor_overview(
            device_id=3,
            session=session,
            current_user=current_user,
        )

        self.assertEqual(result["data"], expected)
        mock_ensure_access.assert_called_once_with(session, current_user, 3)
        mock_use_case.assert_called_once_with(session=session, device_id=3)

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

    @patch("app.api.endpoints.locations.list_locations_use_case")
    def test_locations_list_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        expected = [SimpleNamespace(id=1, name="北区")]
        mock_use_case.return_value = expected

        result = locations.get_locations(
            location_type="area",
            parent_id=3,
            is_active=True,
            session=session,
            current_user=current_user,
        )

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            location_type="area",
            parent_id=3,
            is_active=True,
        )

    @patch("app.api.endpoints.locations.get_location_tree_use_case")
    def test_locations_tree_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        mock_use_case.return_value = [{"id": 1, "children": []}]

        result = locations.get_location_tree(
            root_id=1,
            max_depth=2,
            session=session,
            current_user=current_user,
        )

        self.assertEqual(result["data"], [{"id": 1, "children": []}])
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            root_id=1,
            max_depth=2,
        )

    @patch("app.api.endpoints.locations.create_location_use_case")
    def test_locations_create_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        request = SimpleNamespace(
            name="北区",
            location_type="area",
            parent_id=1,
            code="NORTH",
            description="desc",
            area_sqm=1200.0,
            manager="alice",
            contact="123",
        )
        expected = SimpleNamespace(id=2, name="北区")
        mock_use_case.return_value = expected

        result = locations.create_location(
            request=request,
            session=session,
            current_user=current_user,
        )

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            name="北区",
            location_type="area",
            parent_id=1,
            code="NORTH",
            description="desc",
            area_sqm=1200.0,
            manager="alice",
            contact="123",
        )

    @patch("app.api.endpoints.locations.get_location_statistics_use_case")
    def test_locations_statistics_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        mock_use_case.return_value = {"device_count": {"total": 3}}

        result = locations.get_location_statistics(
            location_id=5,
            recursive=False,
            session=session,
            current_user=current_user,
        )

        self.assertEqual(result["data"], {"device_count": {"total": 3}})
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            location_id=5,
            recursive=False,
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

    @patch("app.api.endpoints.auth.login_use_case")
    def test_auth_login_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        request = SimpleNamespace()
        form_data = SimpleNamespace(username="alice", password="StrongPass123!")
        expected = {"access_token": "a", "token_type": "bearer"}
        mock_use_case.return_value = expected

        result = auth.login(request=request, form_data=form_data, session=session)

        self.assertIs(result, expected)
        mock_use_case.assert_called_once()
        kwargs = mock_use_case.call_args.kwargs
        self.assertIs(kwargs["session"], session)
        self.assertEqual(kwargs["username"], "alice")
        self.assertEqual(kwargs["password"], "StrongPass123!")
        self.assertTrue(callable(kwargs["enforce_rate_limit"]))

    @patch("app.api.endpoints.auth.refresh_access_token_use_case")
    def test_auth_refresh_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        request = SimpleNamespace(refresh_token="rt-123")
        expected = {"access_token": "new"}
        mock_use_case.return_value = expected

        result = auth.refresh_access_token(request=request, session=session)

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(session=session, refresh_token="rt-123")

    @patch("app.api.endpoints.auth.logout_use_case")
    def test_auth_logout_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="alice", role="viewer")
        expected = {"success": True, "message": "已退出登录", "token_version": 3}
        mock_use_case.return_value = expected

        result = auth.logout(current_user=current_user, session=session)

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(session=session, current_user=current_user)


if __name__ == "__main__":
    unittest.main()
