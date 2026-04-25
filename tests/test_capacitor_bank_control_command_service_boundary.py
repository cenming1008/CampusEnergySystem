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
    def test_submit_remote_control_command_rejects_unsupported_gateway_action(self, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, sn="CAP-016", is_active=True)
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 66))

        with self.assertRaises(ValueError) as ctx:
            CapacitorBankControlCommandService.submit_remote_control_command(
                session,
                device,
                action="reset_alarm",
                operator="operator",
                reason="前端联调",
            )

        self.assertIn("真实网关暂未提供报警复位寄存器/功能码", str(ctx.exception))
        session.add.assert_not_called()
        mock_publish.assert_not_called()

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

    def test_expire_pending_control_logs_notifies_timeout_events(self):
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
        notifier = MagicMock()
        session.exec.return_value.all.return_value = [expired_log]
        session.add = MagicMock()
        session.commit = MagicMock()

        logs = CapacitorBankControlCommandService.expire_pending_control_logs(
            session,
            device_id=16,
            control_event_notifier=notifier,
        )

        self.assertEqual(logs, [expired_log])
        notifier.assert_called_once()
        event = notifier.call_args[0][0]
        self.assertEqual(event["type"], "device_control_log_update")
        self.assertEqual(event["data"]["device_id"], 16)
        self.assertEqual(event["data"]["command_id"], "101")
        self.assertEqual(event["data"]["result"], "timeout")

    def test_apply_control_receipt_notifies_log_update_and_tolerates_notifier_failure(self):
        session = MagicMock()
        control_log = DeviceControlLog(
            id=91,
            device_id=16,
            action="reset_alarm",
            target_status=True,
            previous_status=True,
            operator="admin",
            command_source="remote-control-api",
            result="accepted",
            reason="控制台报警复位",
        )
        notifier = MagicMock(side_effect=RuntimeError("websocket unavailable"))
        session.add = MagicMock()
        session.flush = MagicMock()

        with patch(
            "app.repositories.device_repository.DeviceRepository.get_control_log_by_id",
            return_value=control_log,
        ):
            with self.assertLogs(
                "app.services.devices.compensation.capacitor_bank.control_command_service",
                level="WARNING",
            ) as captured:
                updated = CapacitorBankControlCommandService.apply_control_receipt(
                    session,
                    device_id=16,
                    command_id="91",
                    result="success",
                    detail="网关已执行报警复位",
                    control_event_notifier=notifier,
                )

        self.assertEqual(updated.result, "success")
        session.flush.assert_called_once()
        notifier.assert_called_once()
        event = notifier.call_args[0][0]
        self.assertEqual(event["type"], "device_control_log_update")
        self.assertEqual(event["data"]["result"], "success")
        self.assertTrue(any("control log notifier failed" in line for line in captured.output))

    def test_receipt_timeout_uses_settings_value(self):
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
            created_at=datetime(2026, 4, 24, 12, 0, 0) - timedelta(seconds=31),
        )
        session.exec.return_value.all.return_value = [expired_log]
        session.add = MagicMock()
        session.commit = MagicMock()

        with patch(
            "app.services.devices.compensation.capacitor_bank.specs.settings.compensation_control_receipt_timeout_seconds",
            30,
            create=True,
        ):
            logs = CapacitorBankControlCommandService.expire_pending_control_logs(
                session,
                device_id=16,
                now=datetime(2026, 4, 24, 12, 0, 0),
            )

        self.assertEqual(logs, [expired_log])
        self.assertEqual(expired_log.result, "timeout")


if __name__ == "__main__":
    unittest.main()
