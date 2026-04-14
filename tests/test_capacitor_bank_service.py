import os
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.tables import CapacitorBankControlProfile, DeviceControlLog
from app.services.capacitor_bank_service import (
    CONTROL_RECEIPT_TIMEOUT,
    CapacitorBankService,
    ControlProfileWritePreconditionError,
)


class TestCapacitorBankService(unittest.TestCase):
    def test_normalize_write_value_accepts_decimal_pf(self):
        result = CapacitorBankService.normalize_write_value("switch_on_power_factor", 0.95)
        self.assertEqual(result, 95)

    def test_normalize_write_value_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            CapacitorBankService.normalize_write_value("temperature_upper_limit", 120)

    @patch("app.services.capacitor_bank_service.publish_parameter_write_async")
    @patch("app.services.capacitor_bank_service.IngestionHealthService.get_device_health")
    def test_submit_control_profile_write_records_log_and_publishes(self, mock_health, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, is_active=True)
        profile = CapacitorBankControlProfile(
            device_id=16,
            source="telemetry",
            snapshot_timestamp=datetime.now(),
        )
        mock_health.return_value = {"is_online": True}
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 88))

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
        device = SimpleNamespace(id=16, is_active=True)

        with patch("app.services.capacitor_bank_service.IngestionHealthService.get_device_health", return_value={"is_online": True}):
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
        device = SimpleNamespace(id=16, is_active=True)

        with patch("app.services.capacitor_bank_service.IngestionHealthService.get_device_health", return_value={"is_online": False}):
            with self.assertRaises(ControlProfileWritePreconditionError):
                CapacitorBankService.submit_control_profile_write(
                    session,
                    device,
                    parameter_key="switch_on_power_factor",
                    target_value=95,
                    operator="admin",
                )

    @patch("app.services.capacitor_bank_service.publish_control_payload_async")
    def test_submit_remote_control_command_records_log_and_publishes(self, mock_publish):
        session = MagicMock()
        device = SimpleNamespace(id=16, is_active=True)
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 66))

        result = CapacitorBankService.submit_remote_control_command(
            session,
            device,
            action="reset_alarm",
            operator="operator",
            reason="前端联调",
        )

        added_log = session.add.call_args[0][0]
        self.assertIsInstance(added_log, DeviceControlLog)
        self.assertEqual(added_log.action, "reset_alarm")
        self.assertEqual(added_log.command_source, "remote-control-api")
        self.assertEqual(added_log.result, "accepted")
        mock_publish.assert_called_once_with(
            16,
            {
                "message_type": "control_command",
                "protocol_version": "campus-control.v1",
                "timestamp": unittest.mock.ANY,
                "command": "reset_alarm",
                "command_id": "66",
                "device_id": 16,
                "reason": "前端联调",
            },
            worker_name="mqtt-remote-reset_alarm",
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["command_id"], "66")

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

        with patch("app.services.capacitor_bank_service.DeviceRepository.get_control_log_by_id", return_value=control_log):
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

        with patch("app.services.capacitor_bank_service.DeviceRepository.get_control_log_by_id", return_value=control_log):
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


if __name__ == "__main__":
    unittest.main()
