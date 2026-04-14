import os
import unittest
from datetime import datetime
from fastapi import HTTPException
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.devices import compensation_capacitor_bank, compensation_svg
from app.api.endpoints.devices.compensation_schemas import SVGOperationsProfileUpdate
from app.models.tables import CapacitorBankControlProfile, CapacitorBankTelemetry, SVGAssetProfile, SVGTelemetry
from app.services.capacitor_bank_service import ControlProfileWritePreconditionError


def _make_user() -> SimpleNamespace:
    return SimpleNamespace(role="admin", id=1, username="tester", location_scope=None)


class TestCompensationNestedSvgApi(unittest.TestCase):
    def test_nested_svg_profile_returns_serialized_profile(self):
        user = _make_user()
        mock_session = object()
        profile = SVGAssetProfile(device_id=1, display_name="SVG-A")
        with patch.object(compensation_svg, "ensure_device_access") as mock_access:
            with patch.object(compensation_svg.SVGService, "get_operations_profile", return_value=profile) as mock_get:
                result = compensation_svg.get_device_svg_operations_profile(1, mock_session, user)
        mock_access.assert_called_once_with(mock_session, user, 1)
        mock_get.assert_called_once_with(mock_session, 1)
        self.assertEqual(result["device_id"], 1)
        self.assertEqual(result["display_name"], "SVG-A")

    def test_nested_svg_profile_update_upserts_profile(self):
        user = _make_user()
        mock_session = object()
        body = SVGOperationsProfileUpdate(display_name="SVG-B")
        profile = SVGAssetProfile(device_id=1, display_name="SVG-B")
        with patch.object(compensation_svg, "ensure_device_access") as mock_access:
            with patch.object(compensation_svg.SVGService, "upsert_operations_profile", return_value=profile) as mock_upsert:
                result = compensation_svg.upsert_device_svg_operations_profile(1, body, mock_session, user)
        mock_access.assert_called_once_with(mock_session, user, 1)
        mock_upsert.assert_called_once_with(
            mock_session,
            device_id=1,
            payload={"display_name": "SVG-B"},
        )
        self.assertEqual(result["display_name"], "SVG-B")

    def test_nested_svg_telemetry_latest_reads_directly(self):
        user = _make_user()
        telemetry = SVGTelemetry(device_id=1, timestamp=datetime.fromisoformat("2026-04-14T10:00:00"))
        mock_session = SimpleNamespace(
            exec=lambda q: SimpleNamespace(first=lambda: telemetry)
        )
        with patch.object(compensation_svg, "ensure_device_access") as mock_access:
            result = compensation_svg.get_device_svg_telemetry_latest(1, mock_session, user)
        mock_access.assert_called_once_with(mock_session, user, 1)
        self.assertEqual(result, telemetry)


class TestCompensationNestedCapBankApi(unittest.TestCase):
    def test_nested_cap_bank_latest_reads_directly(self):
        user = _make_user()
        mock_session = SimpleNamespace(
            exec=lambda q: SimpleNamespace(first=lambda: CapacitorBankTelemetry(device_id=1, timestamp=datetime.fromisoformat("2026-04-14T10:00:00")))
        )
        with patch.object(compensation_capacitor_bank, "ensure_device_access") as mock_access:
            result = compensation_capacitor_bank.get_device_capacitor_bank_telemetry_latest(1, mock_session, user)
        mock_access.assert_called_once_with(mock_session, user, 1)
        self.assertEqual(result.device_id, 1)

    def test_nested_cap_bank_history_reads_directly(self):
        user = _make_user()
        expected = CapacitorBankTelemetry(device_id=1, timestamp=datetime.fromisoformat("2026-04-14T10:00:00"))
        mock_session = SimpleNamespace(
            exec=lambda q: SimpleNamespace(all=lambda: [expected])
        )
        with patch.object(compensation_capacitor_bank, "ensure_device_access") as mock_access:
            result = compensation_capacitor_bank.get_device_capacitor_bank_telemetry_history(
                1,
                None,
                None,
                200,
                mock_session,
                user,
            )
        mock_access.assert_called_once_with(mock_session, user, 1)
        self.assertEqual(result, [expected])

    def test_nested_cap_bank_control_profile_returns_capabilities_and_values(self):
        user = _make_user()
        mock_session = object()
        device = SimpleNamespace(device_type="compensation", device_subtype="capacitor_bank_controller")
        profile = CapacitorBankControlProfile(device_id=1, switch_on_power_factor=95, baud_rate=9600, source="telemetry")
        with patch.object(compensation_capacitor_bank, "ensure_device_access", return_value=device) as mock_access:
            with patch.object(compensation_capacitor_bank.CapacitorBankService, "get_control_profile", return_value=profile) as mock_get:
                with patch.object(compensation_capacitor_bank.CapacitorBankService, "get_profile_source_status", return_value="fresh"):
                    result = compensation_capacitor_bank.get_device_capacitor_bank_control_profile(1, mock_session, user)
        mock_access.assert_called_once_with(mock_session, user, 1)
        mock_get.assert_called_once_with(mock_session, 1)
        self.assertEqual(result["device_id"], 1)
        self.assertEqual(result["switch_on_power_factor"], 95)
        self.assertTrue(result["capabilities"]["supports_read"])
        self.assertTrue(result["capabilities"]["supports_write"])
        self.assertTrue(result["capabilities"]["supports_remote_control"])
        self.assertEqual(result["source_status"], "fresh")

    def test_nested_cap_bank_control_profile_write_returns_accepted_result(self):
        user = _make_user()
        mock_session = object()
        device = SimpleNamespace(device_type="compensation", device_subtype="capacitor_bank_controller")
        body = compensation_capacitor_bank.CapacitorBankControlWriteRequest(parameter_key="switch_on_power_factor", target_value="95")
        expected = {
            "accepted": True,
            "status": "accepted",
            "message": "参数写入指令已入队",
            "command_id": "42",
        }
        with patch.object(compensation_capacitor_bank, "ensure_device_access", return_value=device):
            with patch.object(compensation_capacitor_bank.CapacitorBankService, "submit_control_profile_write", return_value=expected) as mock_submit:
                with patch.object(compensation_capacitor_bank, "audit_log") as mock_audit:
                    result = compensation_capacitor_bank.write_device_capacitor_bank_control_profile(1, body, mock_session, user)
        mock_submit.assert_called_once_with(
            mock_session,
            device,
            parameter_key="switch_on_power_factor",
            target_value="95",
            operator="tester",
            reason=None,
        )
        mock_audit.assert_called_once()
        self.assertTrue(result["accepted"])
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["command_id"], "42")

    def test_nested_cap_bank_control_profile_write_returns_bad_request(self):
        user = _make_user()
        mock_session = object()
        device = SimpleNamespace(device_type="compensation", device_subtype="capacitor_bank_controller")
        body = compensation_capacitor_bank.CapacitorBankControlWriteRequest(parameter_key="switch_on_power_factor", target_value="bad")
        with patch.object(compensation_capacitor_bank, "ensure_device_access", return_value=device):
            with patch.object(
                compensation_capacitor_bank.CapacitorBankService,
                "submit_control_profile_write",
                side_effect=ValueError("参数值非法"),
            ):
                with self.assertRaises(HTTPException) as ctx:
                    compensation_capacitor_bank.write_device_capacitor_bank_control_profile(1, body, mock_session, user)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "参数值非法")

    def test_nested_cap_bank_control_profile_write_returns_conflict(self):
        user = _make_user()
        mock_session = object()
        device = SimpleNamespace(device_type="compensation", device_subtype="capacitor_bank_controller")
        body = compensation_capacitor_bank.CapacitorBankControlWriteRequest(parameter_key="switch_on_power_factor", target_value="95")
        with patch.object(compensation_capacitor_bank, "ensure_device_access", return_value=device):
            with patch.object(
                compensation_capacitor_bank.CapacitorBankService,
                "submit_control_profile_write",
                side_effect=ControlProfileWritePreconditionError("当前设备尚未完成真实参数回读"),
            ):
                with self.assertRaises(HTTPException) as ctx:
                    compensation_capacitor_bank.write_device_capacitor_bank_control_profile(1, body, mock_session, user)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "当前设备尚未完成真实参数回读")

    def test_nested_cap_bank_remote_command_returns_accepted_result(self):
        user = _make_user()
        mock_session = object()
        device = SimpleNamespace(device_type="compensation", device_subtype="capacitor_bank_controller")
        body = compensation_capacitor_bank.CapacitorBankRemoteCommandRequest(action="reset_alarm")
        expected = {
            "accepted": True,
            "status": "accepted",
            "message": "报警复位指令已入队",
            "command_id": "52",
        }
        with patch.object(compensation_capacitor_bank, "ensure_device_access", return_value=device):
            with patch.object(
                compensation_capacitor_bank.CapacitorBankService,
                "submit_remote_control_command",
                return_value=expected,
            ) as mock_submit:
                with patch.object(compensation_capacitor_bank, "audit_log") as mock_audit:
                    result = compensation_capacitor_bank.send_device_capacitor_bank_remote_command(1, body, mock_session, user)
        mock_submit.assert_called_once_with(
            mock_session,
            device,
            action="reset_alarm",
            operator="tester",
            reason=None,
        )
        mock_audit.assert_called_once_with(
            "device.capacitor_bank.remote_command",
            "tester",
            "device:1",
            remote_command="reset_alarm",
            command_id="52",
            role="admin",
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["command_id"], "52")


if __name__ == "__main__":
    unittest.main()
