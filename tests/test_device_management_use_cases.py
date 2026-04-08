import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.application.device_management import (
    create_device_smart_use_case,
    delete_device_use_case,
    toggle_device_status_use_case,
    update_device_profile_use_case,
)


class TestDeviceManagementUseCases(unittest.TestCase):
    @patch("app.application.device_management.audit_log")
    @patch("app.application.device_management.DeviceService.create_device_smart")
    def test_create_device_smart_use_case_audits_created_device(self, mock_create_device, mock_audit_log):
        session = MagicMock()
        current_user = SimpleNamespace(username="maintainer", role="maintainer")
        device = SimpleNamespace(id=7)
        mock_create_device.return_value = device

        result = create_device_smart_use_case(
            session=session,
            current_user=current_user,
            name="1号水表",
            sn="WM-001",
            device_type="water_meter",
        )

        self.assertIs(result, device)
        mock_create_device.assert_called_once()
        mock_audit_log.assert_called_once_with(
            "device.create",
            "maintainer",
            "device:7",
            role="maintainer",
        )

    @patch("app.application.device_management.audit_log")
    @patch("app.application.device_management.DeviceService.update_device")
    @patch("app.application.device_management.ensure_device_access")
    def test_update_device_profile_use_case_checks_access_and_audits(
        self,
        mock_ensure_access,
        mock_update_device,
        mock_audit_log,
    ):
        session = MagicMock()
        current_user = SimpleNamespace(username="maintainer", role="maintainer")
        updated = SimpleNamespace(id=9)
        mock_update_device.return_value = updated

        result = update_device_profile_use_case(
            session=session,
            current_user=current_user,
            device_id=9,
            name="新名称",
        )

        self.assertIs(result, updated)
        mock_ensure_access.assert_called_once_with(session, current_user, 9)
        mock_update_device.assert_called_once()
        mock_audit_log.assert_called_once()

    @patch("app.application.device_management.audit_log")
    @patch("app.application.device_management.publish_control_command_async")
    @patch("app.application.device_management.DeviceService.toggle_device_status")
    @patch("app.application.device_management.ensure_device_access")
    def test_toggle_device_status_use_case_coordinates_access_defaults_mqtt_and_audit(
        self,
        mock_ensure_access,
        mock_toggle_device,
        mock_publish_command,
        mock_audit_log,
    ):
        session = MagicMock()
        current_user = SimpleNamespace(username="operator", role="operator")
        toggled = SimpleNamespace(id=11, is_active=False)
        mock_toggle_device.return_value = toggled

        result = toggle_device_status_use_case(
            session=session,
            current_user=current_user,
            device_id=11,
            active=False,
            reason=None,
        )

        self.assertIs(result, toggled)
        mock_ensure_access.assert_called_once_with(session, current_user, 11)
        mock_toggle_device.assert_called_once_with(
            session,
            11,
            False,
            operator="operator",
            reason="API停用设备",
            command_source="api",
        )
        mock_publish_command.assert_called_once_with(11, "stop")
        mock_audit_log.assert_called_once_with(
            "device.toggle",
            "operator",
            "device:11",
            active=False,
            reason="API停用设备",
            command_action="stop",
            role="operator",
        )

    @patch("app.application.device_management.audit_log")
    @patch("app.application.device_management.DeviceService.delete_device")
    @patch("app.application.device_management.ensure_device_access")
    def test_delete_device_use_case_returns_stable_message_and_audits(
        self,
        mock_ensure_access,
        mock_delete_device,
        mock_audit_log,
    ):
        session = MagicMock()
        current_user = SimpleNamespace(username="maintainer", role="maintainer")
        mock_ensure_access.return_value = SimpleNamespace(name="3号配电柜")

        result = delete_device_use_case(
            session=session,
            current_user=current_user,
            device_id=3,
        )

        self.assertEqual(result.message, "设备 3号配电柜 已删除")
        mock_delete_device.assert_called_once_with(session, 3)
        mock_audit_log.assert_called_once()


if __name__ == "__main__":
    unittest.main()
