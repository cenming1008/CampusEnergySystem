import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.application.inspection import (
    create_inspection_route_use_case,
    start_inspection_task_use_case,
    submit_inspection_record_use_case,
)
from app.application.maintenance import (
    create_maintenance_record_use_case,
    start_maintenance_use_case,
    summarize_maintenance_statistics_use_case,
)


class TestInspectionMaintenanceUseCases(unittest.TestCase):
    @patch("app.application.inspection.audit_log")
    @patch("app.application.inspection.InspectionService.create_route")
    def test_create_inspection_route_use_case_audits_after_service(self, mock_create_route, mock_audit_log):
        session = MagicMock()
        current_user = SimpleNamespace(username="maintainer", role="maintainer")
        route = SimpleNamespace(id=18)
        mock_create_route.return_value = route

        result = create_inspection_route_use_case(
            session=session,
            current_user=current_user,
            name="园区南线",
            code="R-01",
            description="南区设备巡检",
            estimated_duration=45,
        )

        self.assertIs(result, route)
        mock_create_route.assert_called_once()
        mock_audit_log.assert_called_once_with(
            "inspection.route.create",
            "maintainer",
            "route:18",
            role="maintainer",
        )

    @patch("app.application.inspection.audit_log")
    @patch("app.application.inspection.InspectionService.start_task")
    @patch("app.application.inspection.ensure_route_access")
    @patch("app.application.inspection.InspectionService.get_task_by_id")
    def test_start_inspection_task_use_case_fills_default_inspector_and_audits(
        self,
        mock_get_task,
        mock_ensure_route_access,
        mock_start_task,
        mock_audit_log,
    ):
        session = MagicMock()
        current_user = SimpleNamespace(username="operator_a", role="operator")
        task = SimpleNamespace(route_id=7)
        started_task = SimpleNamespace(id=3)
        mock_get_task.return_value = task
        mock_start_task.return_value = started_task

        result = start_inspection_task_use_case(
            session=session,
            current_user=current_user,
            task_id=3,
            inspector=None,
        )

        self.assertIs(result, started_task)
        mock_ensure_route_access.assert_called_once_with(session, current_user, 7)
        mock_start_task.assert_called_once_with(session, 3, "operator_a")
        mock_audit_log.assert_called_once()

    @patch("app.application.inspection.audit_log")
    @patch("app.application.inspection.InspectionService.submit_inspection_record")
    @patch("app.application.inspection.ensure_device_access")
    @patch("app.application.inspection.ensure_route_access")
    @patch("app.application.inspection.InspectionService.get_task_by_id")
    def test_submit_inspection_record_use_case_coordinates_access_defaults_and_audit(
        self,
        mock_get_task,
        mock_ensure_route_access,
        mock_ensure_device_access,
        mock_submit_record,
        mock_audit_log,
    ):
        session = MagicMock()
        session.get.return_value = SimpleNamespace(device_id=11)
        current_user = SimpleNamespace(username="operator_b", role="operator")
        mock_get_task.return_value = SimpleNamespace(route_id=9)
        record = SimpleNamespace(id=88)
        mock_submit_record.return_value = record

        result = submit_inspection_record_use_case(
            session=session,
            current_user=current_user,
            task_id=5,
            point_id=6,
            inspector=None,
        )

        self.assertIs(result, record)
        mock_ensure_route_access.assert_called_once_with(session, current_user, 9)
        mock_ensure_device_access.assert_called_once_with(session, current_user, 11)
        mock_submit_record.assert_called_once_with(
            session=session,
            task_id=5,
            point_id=6,
            result="normal",
            check_details=None,
            meter_reading=None,
            abnormal_description=None,
            abnormal_level=None,
            images=None,
            inspector="operator_b",
        )
        mock_audit_log.assert_called_once()

    @patch("app.application.maintenance.audit_log")
    @patch("app.application.maintenance.MaintenanceService.create_maintenance")
    @patch("app.application.maintenance.ensure_device_access")
    def test_create_maintenance_use_case_applies_created_by_default_and_audits(
        self,
        mock_ensure_device_access,
        mock_create_maintenance,
        mock_audit_log,
    ):
        session = MagicMock()
        current_user = SimpleNamespace(username="maintainer", role="maintainer")
        maintenance = SimpleNamespace(id=21)
        mock_create_maintenance.return_value = maintenance

        result = create_maintenance_record_use_case(
            session=session,
            current_user=current_user,
            device_id=2,
            maintenance_type="routine",
            scheduled_time=datetime(2026, 4, 7, 8, 0, 0),
            title="月度保养",
            created_by=None,
        )

        self.assertIs(result, maintenance)
        mock_ensure_device_access.assert_called_once_with(session, current_user, 2)
        self.assertEqual(mock_create_maintenance.call_args.kwargs["created_by"], "maintainer")
        mock_audit_log.assert_called_once()

    @patch("app.application.maintenance.audit_log")
    @patch("app.application.maintenance.MaintenanceService.start_maintenance")
    @patch("app.application.maintenance._get_accessible_maintenance")
    def test_start_maintenance_use_case_fills_default_operator_and_audits(
        self,
        mock_get_accessible,
        mock_start_maintenance,
        mock_audit_log,
    ):
        session = MagicMock()
        current_user = SimpleNamespace(username="maintainer_a", role="maintainer")
        mock_get_accessible.return_value = SimpleNamespace(device_id=5)
        started = SimpleNamespace(id=9)
        mock_start_maintenance.return_value = started

        result = start_maintenance_use_case(
            session=session,
            current_user=current_user,
            maintenance_id=9,
            operator=None,
        )

        self.assertIs(result, started)
        mock_start_maintenance.assert_called_once_with(session, 9, "maintainer_a")
        mock_audit_log.assert_called_once()

    @patch("app.application.maintenance.MaintenanceService.get_maintenance_statistics")
    @patch("app.application.maintenance.get_allowed_device_ids")
    @patch("app.application.maintenance.ensure_device_access")
    def test_summarize_maintenance_statistics_use_case_checks_device_access_when_filtered(
        self,
        mock_ensure_device_access,
        mock_allowed_ids,
        mock_get_stats,
    ):
        session = MagicMock()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        mock_allowed_ids.return_value = {1, 2}
        mock_get_stats.return_value = {"total_count": 3}

        result = summarize_maintenance_statistics_use_case(
            session=session,
            current_user=current_user,
            device_id=2,
            start_date=datetime(2026, 4, 1),
            end_date=datetime(2026, 4, 7),
        )

        self.assertEqual(result["total_count"], 3)
        mock_ensure_device_access.assert_called_once_with(session, current_user, 2)
        mock_get_stats.assert_called_once()


if __name__ == "__main__":
    unittest.main()
