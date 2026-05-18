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
        self.assertNotIn("common_group", manual_args)
        self.assertEqual(mode_args["manual_mode"], "auto")
        self.assertEqual(mode_args["common_group"], 1)
        self.assertEqual(mode_args["common_group_code"], 0)
        self.assertEqual(payload["protocol_version"], "campus-control.v1")
        self.assertEqual(payload["device_code"], "CAP-016")
        self.assertEqual(payload["command"], "manual_switch")

    def test_manual_switch_common_phase_requires_group_and_carries_group_code(self):
        common_args = CapacitorBankControlCommandService.build_manual_switch_command_args(
            {"manual_mode": "manual", "phase": "COMMON", "switch_action": "on", "group": 2}
        )
        self.assertEqual(common_args["phase_code"], 3)
        self.assertEqual(common_args["common_group"], 2)
        self.assertEqual(common_args["common_group_code"], 1)

        with self.assertRaises(ValueError) as ctx_missing:
            CapacitorBankControlCommandService.build_manual_switch_command_args(
                {"manual_mode": "manual", "phase": "COMMON", "switch_action": "on"}
            )
        self.assertIn("group=1/2/3", str(ctx_missing.exception))

        with self.assertRaises(ValueError) as ctx_invalid:
            CapacitorBankControlCommandService.build_manual_switch_command_args(
                {"manual_mode": "manual", "phase": "COMMON", "switch_action": "on", "group": 4}
            )
        self.assertIn("1/2/3", str(ctx_invalid.exception))

        with self.assertRaises(ValueError) as ctx_phase_a_with_group:
            CapacitorBankControlCommandService.build_manual_switch_command_args(
                {"manual_mode": "manual", "phase": "A", "switch_action": "on", "group": 1}
            )
        self.assertIn("不允许指定 group", str(ctx_phase_a_with_group.exception))

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

    @patch("app.services.devices.compensation.capacitor_bank.control_command_service.publish_control_payload_async")
    def test_submit_remote_control_command_rejects_pending_remote_command(self, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, sn="CAP-016", is_active=True)
        pending_log = DeviceControlLog(
            id=71,
            device_id=16,
            action="manual_switch",
            target_status=True,
            previous_status=True,
            operator="admin",
            command_source="remote-control-api",
            result="running",
            reason="控制台手动投切 A 相 投入",
        )
        session.exec.return_value.first.side_effect = [device, pending_log]
        session.add = MagicMock()

        with self.assertRaises(ValueError) as ctx:
            CapacitorBankControlCommandService.submit_remote_control_command(
                session,
                device,
                action="manual_switch",
                operator="operator",
                reason="协议联调",
                command_args={"manual_mode": "manual", "phase": "B", "switch_action": "on"},
            )

        self.assertIn("已有待完成的远程控制", str(ctx.exception))
        session.add.assert_not_called()
        mock_publish.assert_not_called()

    @patch("app.services.devices.compensation.capacitor_bank.control_command_service.publish_control_payload_async")
    def test_submit_manual_switch_rejects_when_latest_mode_log_is_auto(self, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, sn="CAP-016", is_active=True)
        auto_mode_log = DeviceControlLog(
            id=81,
            device_id=16,
            action="manual_switch",
            target_status=True,
            previous_status=True,
            operator="admin",
            command_source="remote-control-api",
            result="success",
            reason="控制台控制模式切换 -> 自动模式 | 设备回执已处理: 已切回自动模式",
            created_at=datetime(2026, 5, 17, 21, 3, 43),
        )
        session.exec.return_value.first.side_effect = [device, None, auto_mode_log]
        session.add = MagicMock()

        with self.assertRaises(ValueError) as ctx:
            CapacitorBankControlCommandService.submit_remote_control_command(
                session,
                device,
                action="manual_switch",
                operator="operator",
                reason="控制台手动投切 A 相 切除",
                command_args={"manual_mode": "manual", "phase": "A", "switch_action": "off"},
            )

        self.assertIn("当前为自动模式", str(ctx.exception))
        session.add.assert_not_called()
        mock_publish.assert_not_called()

    def test_reconcile_failed_manual_switch_with_telemetry_marks_success_when_target_count_changes(self):
        session = MagicMock()
        failed_log = DeviceControlLog(
            id=91,
            device_id=16,
            action="manual_switch",
            target_status=True,
            previous_status=True,
            operator="admin",
            command_source="remote-control-api",
            result="failed",
            reason="控制台手动投切 A 相 投入 | 设备回执失败: timed out waiting for write/manual response",
            created_at=datetime(2026, 5, 17, 14, 30, 26),
        )
        before = SimpleNamespace(phase_a_circuit_running_count=0)
        after = SimpleNamespace(
            timestamp=datetime(2026, 5, 17, 14, 30, 45),
            phase_a_circuit_running_count=1,
            phase_b_circuit_running_count=0,
            phase_c_circuit_running_count=0,
            common_circuit_running_count=0,
        )
        session.exec.return_value.all.return_value = [failed_log]
        session.exec.return_value.first.return_value = before
        session.add = MagicMock()
        session.flush = MagicMock()
        notifier = MagicMock()

        reconciled = CapacitorBankControlCommandService.reconcile_failed_manual_switch_with_telemetry(
            session,
            device_id=16,
            telemetry=after,
            control_event_notifier=notifier,
        )

        self.assertEqual(reconciled, [failed_log])
        self.assertEqual(failed_log.result, "success")
        self.assertIn("遥测复核已处理", failed_log.reason)
        session.add.assert_called_once_with(failed_log)
        session.flush.assert_called_once()
        notifier.assert_called_once()

    def test_reconcile_failed_manual_switch_uses_common_group_count_when_group_present_in_reason(self):
        session = MagicMock()
        failed_log = DeviceControlLog(
            id=93,
            device_id=16,
            action="manual_switch",
            target_status=True,
            previous_status=True,
            operator="admin",
            command_source="remote-control-api",
            result="failed",
            reason="控制台手动投切 共补 2 组 投入 | 设备回执失败: crc validation failed",
            created_at=datetime(2026, 5, 17, 14, 30, 26),
        )
        before = SimpleNamespace(common_group_2_running_count=1)
        after = SimpleNamespace(
            timestamp=datetime(2026, 5, 17, 14, 30, 45),
            common_group_1_running_count=0,
            common_group_2_running_count=2,
            common_group_3_running_count=0,
            common_circuit_running_count=2,
        )
        session.exec.return_value.all.return_value = [failed_log]
        session.exec.return_value.first.return_value = before
        session.add = MagicMock()
        session.flush = MagicMock()

        reconciled = CapacitorBankControlCommandService.reconcile_failed_manual_switch_with_telemetry(
            session,
            device_id=16,
            telemetry=after,
        )

        self.assertEqual(reconciled, [failed_log])
        self.assertEqual(failed_log.result, "success")
        self.assertIn("遥测复核已处理: COMMON2 on 1->2", failed_log.reason)

    def test_reconcile_failed_manual_switch_ignores_unchanged_target_count(self):
        session = MagicMock()
        failed_log = DeviceControlLog(
            id=92,
            device_id=16,
            action="manual_switch",
            target_status=True,
            previous_status=True,
            operator="admin",
            command_source="remote-control-api",
            result="failed",
            reason="控制台手动投切 B 相 投入 | 设备回执失败: timed out waiting for write/manual response",
            created_at=datetime(2026, 5, 17, 14, 30, 43),
        )
        before = SimpleNamespace(phase_b_circuit_running_count=1)
        after = SimpleNamespace(
            timestamp=datetime(2026, 5, 17, 14, 30, 50),
            phase_a_circuit_running_count=1,
            phase_b_circuit_running_count=1,
            phase_c_circuit_running_count=0,
            common_circuit_running_count=0,
        )
        session.exec.return_value.all.return_value = [failed_log]
        session.exec.return_value.first.return_value = before
        session.add = MagicMock()
        session.flush = MagicMock()

        reconciled = CapacitorBankControlCommandService.reconcile_failed_manual_switch_with_telemetry(
            session,
            device_id=16,
            telemetry=after,
        )

        self.assertEqual(reconciled, [])
        self.assertEqual(failed_log.result, "failed")
        session.add.assert_not_called()
        session.flush.assert_not_called()

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
        self.assertEqual(CapacitorBankControlCommandService.get_result_label("success"), "已处理")
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
        self.assertIn("设备回执已处理", updated.reason)
        self.assertNotIn("网关已执行报警复位", updated.reason)
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
