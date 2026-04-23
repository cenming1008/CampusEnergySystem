import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.models.tables import DeviceControlLog
from app.services.devices.compensation.capacitor_bank.control_command_service import CapacitorBankControlCommandService
from app.services.devices.compensation.capacitor_bank.specs import CONTROL_RECEIPT_TIMEOUT


class TestCapacitorBankControlCommandServiceBoundary(unittest.TestCase):
    def test_manual_switch_payload_and_mode_bridge_are_built_in_command_layer(self):
        manual_args = CapacitorBankControlCommandService.build_manual_switch_command_args(
            {"manual_mode": "manual", "phase": "A", "switch_action": "on"}
        )
        mode_args = CapacitorBankControlCommandService.build_control_mode_switch_command_args("切换到自动模式")
        payload = CapacitorBankControlCommandService.build_command_payload(
            16,
            device_code="CAP-016",
            command="manual_switch",
            command_id="93",
            reason="协议联调",
            extras=manual_args,
        )

        self.assertEqual(manual_args["protocol_function_code"], "0x44")
        self.assertEqual(manual_args["manual_mode_code"], 1)
        self.assertEqual(manual_args["phase_code"], 0)
        self.assertEqual(manual_args["switch_action_code"], 17)
        self.assertEqual(mode_args["manual_mode"], "auto")
        self.assertEqual(payload["protocol_version"], "campus-control.v1")
        self.assertEqual(payload["device_code"], "CAP-016")
        self.assertEqual(payload["command"], "manual_switch")

    @patch("app.services.devices.compensation.capacitor_bank.control_command_service.publish_control_payload_async")
    def test_submit_remote_control_command_records_log_and_publishes(self, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, sn="CAP-016", is_active=True)
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 66))

        result = CapacitorBankControlCommandService.submit_remote_control_command(
            session,
            device,
            action="reset_alarm",
            operator="operator",
            reason="前端联调",
        )

        added_log = session.add.call_args[0][0]
        self.assertIsInstance(added_log, DeviceControlLog)
        self.assertEqual(added_log.command_source, "remote-control-api")
        self.assertEqual(added_log.result, "accepted")
        mock_publish.assert_called_once()
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["command_id"], "66")

    def test_receipt_status_and_timeout_live_in_command_layer(self):
        session = MagicMock()
        expired_log = DeviceControlLog(
            id=101,
            device_id=16,
            action="manual_switch_test",
            target_status=True,
            previous_status=True,
            operator="admin",
            command_source="remote-control-api",
            result="accepted",
            reason="控制台手动投切测试",
            created_at=datetime.now() - CONTROL_RECEIPT_TIMEOUT - timedelta(seconds=1),
        )
        session.exec.return_value.all.return_value = [expired_log]
        session.add = MagicMock()
        session.commit = MagicMock()

        logs = CapacitorBankControlCommandService.expire_pending_control_logs(session, device_id=16)

        self.assertEqual(CapacitorBankControlCommandService.normalize_control_result("bad-value"), "failed")
        self.assertEqual(CapacitorBankControlCommandService.get_result_label("running"), "设备执行中")
        self.assertEqual(len(logs), 1)
        self.assertEqual(expired_log.result, "timeout")
        self.assertIn("设备回执超时", expired_log.reason)


if __name__ == "__main__":
    unittest.main()
