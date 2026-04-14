import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.devices import compensation_capacitor_bank, compensation_svg
from app.api.endpoints.devices.compensation_schemas import SVGOperationsProfileUpdate
from app.models.tables import CapacitorBankTelemetry, SVGAssetProfile, SVGTelemetry


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


if __name__ == "__main__":
    unittest.main()
