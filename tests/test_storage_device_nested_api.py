import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.devices import storage
from app.api.endpoints.devices.storage_schemas import (
    StorageAssetProfileUpdate,
    StorageControlRequest,
    StorageSimulationControlRequest,
)
from app.core.exceptions import PermissionDeniedException
from app.models.storage import StorageTelemetry
from app.models.tables import UserRole


def _make_user() -> SimpleNamespace:
    return SimpleNamespace(role="admin", id=1, username="tester", location_scope=None)


def _make_storage_device() -> SimpleNamespace:
    return SimpleNamespace(id=1, sn="STO-001", device_category="storage", is_active=True)


class TestStorageNestedApi(unittest.TestCase):
    def test_storage_routes_extend_existing_nested_boundary(self):
        paths = {(route.path, next(iter(route.methods))) for route in storage.router.routes}

        self.assertIn(("/{device_id}/storage/profile", "GET"), paths)
        self.assertIn(("/{device_id}/storage/profile", "PUT"), paths)
        self.assertIn(("/{device_id}/storage/control/capabilities", "GET"), paths)
        self.assertIn(("/{device_id}/storage/control", "POST"), paths)
        self.assertIn(("/{device_id}/storage/simulation/capabilities", "GET"), paths)
        self.assertIn(("/{device_id}/storage/simulation/control", "POST"), paths)

    def test_viewer_can_read_but_control_dependency_rejects_viewer(self):
        viewer = SimpleNamespace(role=UserRole.VIEWER, location_scope=None)
        session = object()
        expected = SimpleNamespace(device_id=1, ems_auto_enabled=False)
        with patch.object(storage, "ensure_device_access", return_value=_make_storage_device()), patch.object(
            storage.StorageAssetProfileService,
            "get_profile",
            return_value=expected,
        ):
            self.assertIs(storage.get_storage_profile(1, session, viewer), expected)
        with self.assertRaises(PermissionDeniedException):
            storage.MAINTAINER_OPERATOR_OR_ADMIN(viewer)

    def test_get_profile_uses_existing_access_boundary_and_service(self):
        user = _make_user()
        session = object()
        expected = SimpleNamespace(device_id=1, ems_auto_enabled=False)
        with patch.object(
            storage,
            "ensure_device_access",
            return_value=_make_storage_device(),
        ) as access, patch.object(
            storage.StorageAssetProfileService,
            "get_profile",
            return_value=expected,
        ) as get_profile:
            result = storage.get_storage_profile(1, session, user)

        access.assert_called_once_with(session, user, 1)
        get_profile.assert_called_once_with(session, 1)
        self.assertIs(result, expected)

    def test_put_profile_forwards_admin_gate_authority(self):
        user = _make_user()
        session = object()
        body = StorageAssetProfileUpdate(
            rated_energy_kwh=500,
            rated_power_kw=250,
            ems_auto_enabled=False,
        )
        expected = SimpleNamespace(device_id=1, ems_auto_enabled=False)
        with patch.object(storage, "ensure_device_access", return_value=_make_storage_device()), patch.object(
            storage.StorageAssetProfileService,
            "upsert_profile",
            return_value=expected,
        ) as upsert, patch.object(storage, "audit_log"):
            result = storage.put_storage_profile(1, body, session, user)

        self.assertIs(result, expected)
        self.assertTrue(upsert.call_args.kwargs["allow_auto_gate_update"])

    def test_control_uses_task6_service_and_maps_validation_to_400(self):
        user = _make_user()
        session = object()
        device = SimpleNamespace(id=1, sn="STO-001", device_category="storage", is_active=True)
        body = StorageControlRequest(
            command="set_active_power",
            target_active_power=999,
            source="manual",
        )
        with patch.object(storage, "ensure_device_access", return_value=device), patch.object(
            storage.StorageControlCommandService,
            "queue_command",
            side_effect=ValueError("充电功率超限"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                storage.send_storage_control(1, body, session, user)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "充电功率超限")

    def test_simulation_endpoints_are_hidden_when_flag_is_disabled(self):
        user = _make_user()
        session = object()
        with patch.object(storage.settings, "storage_simulation_enabled", False):
            with self.assertRaises(HTTPException) as read_ctx:
                storage.get_storage_simulation_capabilities(1, session, user)
            with self.assertRaises(HTTPException) as control_ctx:
                storage.send_storage_simulation_control(
                    1,
                    StorageSimulationControlRequest(action="set_speed", speed=10),
                    session,
                    user,
                )

        self.assertEqual(read_ctx.exception.status_code, 404)
        self.assertEqual(control_ctx.exception.status_code, 404)

    def test_simulation_control_uses_dedicated_topic(self):
        user = _make_user()
        session = object()
        device = SimpleNamespace(id=1, sn="STO-001", device_category="storage")
        publisher = MagicMock()
        with patch.object(storage.settings, "storage_simulation_enabled", True), patch.object(
            storage,
            "ensure_device_access",
            return_value=device,
        ), patch.object(storage, "publish_topic_payload_async", publisher), patch.object(storage, "audit_log"):
            result = storage.send_storage_simulation_control(
                1,
                StorageSimulationControlRequest(action="set_scenario", scenario="sunny_workday"),
                session,
                user,
            )

        self.assertTrue(result["accepted"])
        self.assertEqual(publisher.call_args.args[0], "campus/simulation/STO-001/control")
        self.assertNotIn("campus/control/", publisher.call_args.args[0])

    def test_simulation_control_rejects_topic_configuration_overlapping_production(self):
        user = _make_user()
        session = object()
        publisher = MagicMock()
        with patch.object(storage.settings, "storage_simulation_enabled", True), patch.object(
            storage.settings,
            "storage_simulation_topic_prefix",
            "campus/control/",
        ), patch.object(storage.settings, "mqtt_control_topic_prefix", "campus/control/"), patch.object(
            storage,
            "ensure_device_access",
            return_value=_make_storage_device(),
        ), patch.object(storage, "publish_topic_payload_async", publisher):
            with self.assertRaises(HTTPException) as ctx:
                storage.send_storage_simulation_control(
                    1,
                    StorageSimulationControlRequest(action="clear_fault"),
                    session,
                    user,
                )

        self.assertEqual(ctx.exception.status_code, 503)
        publisher.assert_not_called()

    def test_unknown_device_keeps_existing_access_control_exception(self):
        user = _make_user()
        session = object()
        with patch.object(
            storage,
            "ensure_device_access",
            side_effect=PermissionDeniedException("设备不存在或不可访问"),
        ):
            with self.assertRaises(PermissionDeniedException):
                storage.get_storage_control_capabilities(999, session, user)

    def test_control_role_dependency_rejects_viewer_and_accepts_operational_roles(self):
        viewer = SimpleNamespace(role=UserRole.VIEWER)
        with self.assertRaises(PermissionDeniedException):
            storage.MAINTAINER_OPERATOR_OR_ADMIN(viewer)
        for role in (UserRole.MAINTAINER, UserRole.OPERATOR, UserRole.ADMIN):
            user = SimpleNamespace(role=role)
            self.assertIs(storage.MAINTAINER_OPERATOR_OR_ADMIN(user), user)

    def test_storage_telemetry_latest_uses_service(self):
        user = _make_user()
        mock_session = object()
        telemetry = StorageTelemetry(device_id=1, timestamp=datetime.fromisoformat("2026-04-14T10:00:00"))
        with patch.object(storage, "ensure_device_access") as mock_access:
            with patch.object(storage.StorageMonitorService, "get_latest_telemetry", return_value=telemetry) as mock_get:
                result = storage.get_storage_telemetry_latest(1, mock_session, user)

        mock_access.assert_called_once_with(mock_session, user, 1)
        mock_get.assert_called_once_with(mock_session, 1)
        self.assertEqual(result, telemetry)

    def test_storage_telemetry_latest_returns_404_when_missing(self):
        user = _make_user()
        mock_session = object()
        with patch.object(storage, "ensure_device_access"):
            with patch.object(storage.StorageMonitorService, "get_latest_telemetry", return_value=None):
                with self.assertRaises(HTTPException) as ctx:
                    storage.get_storage_telemetry_latest(1, mock_session, user)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "暂无遥测数据")

    def test_storage_telemetry_history_uses_service(self):
        user = _make_user()
        mock_session = object()
        start = datetime.fromisoformat("2026-04-14T10:00:00")
        end = datetime.fromisoformat("2026-04-14T11:00:00")
        expected = [StorageTelemetry(device_id=1, timestamp=start)]
        with patch.object(storage, "ensure_device_access") as mock_access:
            with patch.object(storage.StorageMonitorService, "list_telemetry_history", return_value=expected) as mock_list:
                result = storage.get_storage_telemetry_history(
                    1,
                    start,
                    end,
                    50,
                    mock_session,
                    user,
                )

        mock_access.assert_called_once_with(mock_session, user, 1)
        mock_list.assert_called_once_with(mock_session, 1, start_time=start, end_time=end, limit=50)
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
