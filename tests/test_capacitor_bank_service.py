import os
import unittest
import json
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.tables import CapacitorBankControlProfile, DeviceControlLog
from app.services.devices.compensation.capacitor_bank.service import (
    CONTROL_RECEIPT_TIMEOUT,
    CapacitorBankService,
    ControlProfileWritePreconditionError,
    PARAMETER_WRITE_SPECS,
)


class TestCapacitorBankService(unittest.TestCase):
    def test_get_parameter_spec_supports_full_protocol_write_range(self):
        expected_keys = {
            "switch_on_power_factor",
            "switch_off_power_factor",
            "switch_on_delay_seconds",
            "switch_off_delay_seconds",
            "common_output_circuit_count",
            "split_output_circuit_count",
            "common_capacity_code",
            "split_capacity_code",
            "common_step_capacity_kvar",
            "split_step_capacity_kvar",
            "ct_primary_current",
            "overvoltage_threshold",
            "voltage_harmonic_threshold",
            "current_harmonic_threshold",
            "temperature_upper_limit",
            "alarm_drive_event",
            "baud_rate",
            "terminal_assignment_scheme",
            "current_polarity_identification_enabled",
        }

        self.assertEqual(set(PARAMETER_WRITE_SPECS.keys()), expected_keys)

    def test_control_capabilities_use_configured_receipt_timeout(self):
        with patch(
            "app.services.devices.compensation.capacitor_bank.specs.settings.compensation_control_receipt_timeout_seconds",
            45,
        ):
            capabilities = CapacitorBankService.get_control_capabilities()

        self.assertEqual(capabilities["receipt_timeout_seconds"], 45)

    def test_control_capabilities_expose_gateway_limited_commands_and_writable_parameters(self):
        capabilities = CapacitorBankService.get_control_capabilities()

        self.assertEqual(
            capabilities["writable_parameters"],
            [
                "switch_on_power_factor",
                "switch_off_power_factor",
                "switch_on_delay_seconds",
                "switch_off_delay_seconds",
                "overvoltage_threshold",
                "temperature_upper_limit",
            ],
        )
        reset_alarm = next(item for item in capabilities["remote_commands"] if item["action"] == "reset_alarm")
        self.assertFalse(reset_alarm["supported"])
        self.assertIn("真实网关暂未提供报警复位寄存器/功能码", reset_alarm["disabled_reason"])
        switch_mode = next(item for item in capabilities["remote_commands"] if item["action"] == "switch_control_mode")
        self.assertTrue(switch_mode["supported"])

    def test_normalize_write_value_accepts_decimal_pf(self):
        result = CapacitorBankService.normalize_write_value("switch_on_power_factor", 0.95)
        self.assertEqual(result, 95)

    def test_normalize_write_value_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            CapacitorBankService.normalize_write_value("temperature_upper_limit", 120)

    def test_build_capacity_expansion_payload_prefers_direct_capacity_step_arrays(self):
        profile = CapacitorBankControlProfile(
            device_id=16,
            common_capacity_code="4:1233",
            split_capacity_code="7:1124",
            common_step_capacity_kvar=30.0,
            split_step_capacity_kvar=12.0,
            phase_a_capacity_steps_kvar_json=json.dumps([12.0, 12.0, 24.0]),
            phase_b_capacity_steps_kvar_json=json.dumps([48.0, 12.0, 12.0]),
            phase_c_capacity_steps_kvar_json=json.dumps([24.0, 48.0]),
            common_1_capacity_steps_kvar_json=json.dumps([30.0, 60.0, 90.0]),
            common_2_capacity_steps_kvar_json=json.dumps([90.0, 30.0]),
            common_3_capacity_steps_kvar_json=json.dumps([90.0]),
        )

        payload = CapacitorBankService.build_capacity_expansion_payload(profile)

        self.assertEqual(payload["phase_a_capacity_steps_kvar"], [12.0, 12.0, 24.0])
        self.assertEqual(payload["common_2_capacity_steps_kvar"], [90.0, 30.0])
        self.assertEqual(payload["split_capacity_expansion"]["phase_b_groups"], [48.0, 12.0, 12.0])
        self.assertEqual(payload["common_capacity_expansion"]["common_3_groups"], [90.0])

    @patch("app.services.devices.compensation.capacitor_bank.service.publish_parameter_write_async")
    @patch("app.services.devices.compensation.capacitor_bank.service.IngestionHealthService.get_device_health")
    def test_submit_control_profile_write_records_log_and_publishes(self, mock_health, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, sn="CAP-016", is_active=True)
        profile = CapacitorBankControlProfile(
            device_id=16,
            source="telemetry",
            snapshot_timestamp=datetime.now(),
        )
        mock_health.return_value = {"is_online": True}
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 88))
        session.exec.return_value.first.return_value = None

        with patch.object(CapacitorBankService, "get_control_profile", return_value=profile):
            result = CapacitorBankService.submit_control_profile_write(
                session,
                device,
                parameter_key="switch_on_power_factor",
                target_value=0.95,
                operator="admin",
                reason="联调验证",
            )

        added_log = session.add.call_args[0][0]
        self.assertIsInstance(added_log, DeviceControlLog)
        self.assertEqual(added_log.action, "write:switch_on_power_factor")
        self.assertEqual(added_log.command_source, "control-profile-api")
        self.assertEqual(added_log.result, "accepted")
        self.assertIn("联调验证", added_log.reason)
        mock_publish.assert_called_once_with(
            16,
            "switch_on_power_factor",
            95,
            device_code="CAP-016",
            command_id="88",
            reason="联调验证",
            register="0xD2",
            protocol_version="campus-control.v1",
            message_type="control_command",
            sent_at=unittest.mock.ANY,
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["command_id"], "88")

    def test_submit_control_profile_write_requires_real_readback(self):
        session = MagicMock()
        device = SimpleNamespace(id=16, sn="CAP-016", is_active=True)

        with patch(
            "app.services.devices.compensation.capacitor_bank.service.IngestionHealthService.get_device_health",
            return_value={"is_online": True},
        ):
            with patch.object(CapacitorBankService, "get_control_profile", return_value=None):
                with self.assertRaises(ControlProfileWritePreconditionError):
                    CapacitorBankService.submit_control_profile_write(
                        session,
                        device,
                        parameter_key="switch_on_power_factor",
                        target_value=95,
                        operator="admin",
                    )

    def test_submit_control_profile_write_rejects_offline_device(self):
        session = MagicMock()
        device = SimpleNamespace(id=16, sn="CAP-016", is_active=True)

        with patch(
            "app.services.devices.compensation.capacitor_bank.service.IngestionHealthService.get_device_health",
            return_value={"is_online": False},
        ):
            with self.assertRaises(ControlProfileWritePreconditionError):
                CapacitorBankService.submit_control_profile_write(
                    session,
                    device,
                    parameter_key="switch_on_power_factor",
                    target_value=95,
                    operator="admin",
                )

    @patch("app.services.devices.compensation.capacitor_bank.service.publish_control_payload_async")
    def test_submit_remote_control_command_rejects_unsupported_gateway_action(self, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, sn="CAP-016", is_active=True)
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 66))

        with self.assertRaises(ValueError) as ctx:
            CapacitorBankService.submit_remote_control_command(
                session,
                device,
                action="reset_alarm",
                operator="operator",
                reason="前端联调",
            )

        self.assertIn("真实网关暂未提供报警复位寄存器/功能码", str(ctx.exception))
        session.add.assert_not_called()
        mock_publish.assert_not_called()

    def test_apply_control_receipt_updates_control_log_result(self):
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
        session.add = MagicMock()
        session.flush = MagicMock()

        with patch(
            "app.services.devices.compensation.capacitor_bank.service.DeviceRepository.get_control_log_by_id",
            return_value=control_log,
        ):
            updated = CapacitorBankService.apply_control_receipt(
                session,
                device_id=16,
                command_id="91",
                result="success",
                detail="模拟器已执行报警复位",
            )

        self.assertEqual(updated.result, "success")
        self.assertIn("设备回执成功", updated.reason)
        self.assertIn("模拟器已执行报警复位", updated.reason)
        session.add.assert_called_once_with(control_log)
        session.flush.assert_called_once()

    def test_apply_control_receipt_forwards_control_log_event_notifier(self):
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
        notifier = MagicMock()
        session.add = MagicMock()
        session.flush = MagicMock()

        with patch(
            "app.services.devices.compensation.capacitor_bank.service.DeviceRepository.get_control_log_by_id",
            return_value=control_log,
        ):
            CapacitorBankService.apply_control_receipt(
                session,
                device_id=16,
                command_id="91",
                result="success",
                detail="模拟器已执行报警复位",
                control_event_notifier=notifier,
            )

        notifier.assert_called_once()
        self.assertEqual(notifier.call_args[0][0]["data"]["command_id"], "91")

    def test_expire_pending_control_logs_marks_timeout(self):
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

        logs = CapacitorBankService.expire_pending_control_logs(session, device_id=16)

        self.assertEqual(len(logs), 1)
        self.assertEqual(expired_log.result, "timeout")
        self.assertIn("设备回执超时", expired_log.reason)
        session.commit.assert_called_once()

    def test_apply_control_receipt_accepts_running_and_rejected(self):
        session = MagicMock()
        control_log = DeviceControlLog(
            id=92,
            device_id=16,
            action="manual_switch_test",
            target_status=True,
            previous_status=True,
            operator="admin",
            command_source="remote-control-api",
            result="accepted",
            reason="控制台手动投切测试",
        )
        session.add = MagicMock()
        session.flush = MagicMock()

        with patch(
            "app.services.devices.compensation.capacitor_bank.service.DeviceRepository.get_control_log_by_id",
            return_value=control_log,
        ):
            updated_running = CapacitorBankService.apply_control_receipt(
                session,
                device_id=16,
                command_id="92",
                result="running",
                detail="设备正在执行投切",
            )
            self.assertEqual(updated_running.result, "running")
            self.assertIn("设备执行中", updated_running.reason)
            updated_rejected = CapacitorBankService.apply_control_receipt(
                session,
                device_id=16,
                command_id="92",
                result="rejected",
                detail="设备处于就地模式",
            )

        self.assertEqual(updated_rejected.result, "rejected")
        self.assertIn("设备拒绝执行", updated_rejected.reason)

    def test_apply_control_receipt_maps_gateway_refused_alias_to_rejected(self):
        session = MagicMock()
        control_log = DeviceControlLog(
            id=96,
            device_id=16,
            action="manual_switch",
            target_status=True,
            previous_status=True,
            operator="admin",
            command_source="remote-control-api",
            result="accepted",
            reason="控制台手动投切",
        )
        session.add = MagicMock()
        session.flush = MagicMock()

        with patch(
            "app.services.devices.compensation.capacitor_bank.service.DeviceRepository.get_control_log_by_id",
            return_value=control_log,
        ):
            updated = CapacitorBankService.apply_control_receipt(
                session,
                device_id=16,
                command_id="96",
                result="refused",
                detail="设备处于就地模式",
            )

        self.assertEqual(updated.result, "rejected")
        self.assertIn("设备拒绝执行", updated.reason)

    def test_apply_control_receipt_keeps_terminal_result_when_late_different_receipt_arrives(self):
        session = MagicMock()
        control_log = DeviceControlLog(
            id=97,
            device_id=16,
            action="manual_switch",
            target_status=True,
            previous_status=True,
            operator="admin",
            command_source="remote-control-api",
            result="timeout",
            reason="设备回执超时：在约定等待时间内未收到回执",
        )
        session.add = MagicMock()
        session.flush = MagicMock()

        with patch(
            "app.services.devices.compensation.capacitor_bank.service.DeviceRepository.get_control_log_by_id",
            return_value=control_log,
        ):
            with self.assertLogs(
                "app.services.devices.compensation.capacitor_bank.control_command_service",
                level="WARNING",
            ) as captured:
                updated = CapacitorBankService.apply_control_receipt(
                    session,
                    device_id=16,
                    command_id="97",
                    result="success",
                    detail="迟到成功回执",
                )

        self.assertEqual(updated.result, "timeout")
        self.assertIn("迟到回执已忽略", updated.reason)
        self.assertTrue(any("late terminal receipt ignored" in line for line in captured.output))

    def test_apply_control_receipt_skips_duplicate_terminal_receipt(self):
        session = MagicMock()
        control_log = DeviceControlLog(
            id=98,
            device_id=16,
            action="manual_switch",
            target_status=True,
            previous_status=True,
            operator="admin",
            command_source="remote-control-api",
            result="success",
            reason="设备回执成功：已按协议手动投切",
        )
        session.add = MagicMock()
        session.flush = MagicMock()
        notifier = MagicMock()

        with patch(
            "app.services.devices.compensation.capacitor_bank.service.DeviceRepository.get_control_log_by_id",
            return_value=control_log,
        ):
            updated = CapacitorBankService.apply_control_receipt(
                session,
                device_id=16,
                command_id="98",
                result="success",
                detail="重复成功回执",
                control_event_notifier=notifier,
            )

        self.assertEqual(updated.result, "success")
        self.assertNotIn("重复成功回执", updated.reason)
        session.add.assert_not_called()
        session.flush.assert_not_called()
        notifier.assert_not_called()

    @patch("app.services.devices.compensation.capacitor_bank.service.publish_control_payload_async")
    def test_submit_manual_switch_command_publishes_native_jkwf_payload(self, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, sn="CAP-016", is_active=True)
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 93))

        result = CapacitorBankService.submit_remote_control_command(
            session,
            device,
            action="manual_switch",
            operator="operator",
            reason="协议联调",
            command_args={
                "manual_mode": "manual",
                "phase": "A",
                "switch_action": "on",
            },
        )

        mock_publish.assert_called_once_with(
            16,
            {
                "message_type": "control_command",
                "protocol_version": "campus-control.v1",
                "timestamp": unittest.mock.ANY,
                "device_id": 16,
                "device_code": "CAP-016",
                "command_id": "93",
                "command": "manual_switch",
                "reason": "协议联调",
                "manual_mode": "manual",
                "phase": "A",
                "switch_action": "on",
                "protocol_function_code": "0x44",
                "manual_mode_code": 1,
                "phase_code": 0,
                "switch_action_code": 17,
            },
            device_code="CAP-016",
            worker_name="mqtt-remote-manual_switch",
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["command_id"], "93")

    @patch("app.services.devices.compensation.capacitor_bank.service.publish_control_payload_async")
    def test_submit_switch_control_mode_bridges_to_manual_switch_protocol(self, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, sn="CAP-016", is_active=True)
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 94))

        result = CapacitorBankService.submit_remote_control_command(
            session,
            device,
            action="switch_control_mode",
            operator="operator",
            reason="控制台控制模式切换 -> 自动模式",
        )

        mock_publish.assert_called_once_with(
            16,
            {
                "message_type": "control_command",
                "protocol_version": "campus-control.v1",
                "timestamp": unittest.mock.ANY,
                "device_id": 16,
                "device_code": "CAP-016",
                "command_id": "94",
                "command": "manual_switch",
                "reason": "控制台控制模式切换 -> 自动模式",
                "manual_mode": "auto",
                "phase": "COMMON",
                "switch_action": "none",
                "protocol_function_code": "0x44",
                "manual_mode_code": 0,
                "phase_code": 3,
                "switch_action_code": 0,
            },
            device_code="CAP-016",
            worker_name="mqtt-remote-switch_control_mode",
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["command_id"], "94")


if __name__ == "__main__":
    unittest.main()
