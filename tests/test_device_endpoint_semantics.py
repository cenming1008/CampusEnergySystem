import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.devices import management


class TestDeviceEndpointSemantics(unittest.TestCase):
    @patch("app.api.endpoints.devices.management.DeviceService.get_device_types")
    def test_get_device_types_returns_semantic_profiles(self, mock_get_device_types):
        mock_get_device_types.return_value = [
            {
                "device_type": "water_meter",
                "object_role": "meter",
                "metering_role": "dedicated_meter",
                "point_kind": "meter_reading_point",
            }
        ]

        result = management.get_device_types()

        self.assertEqual(result["data"][0]["object_role"], "meter")
        self.assertEqual(result["data"][0]["point_kind"], "meter_reading_point")

    @patch("app.api.endpoints.devices.management.ensure_device_access")
    @patch("app.api.endpoints.devices.management.DeviceService.get_device_semantic_profile")
    def test_get_device_semantic_profile_endpoint_returns_profile(
        self,
        mock_get_profile,
        mock_ensure_access,
    ):
        session = object()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        mock_get_profile.return_value = {
            "device_id": 7,
            "device_type": "water_meter",
            "object_role": "meter",
        }

        result = management.get_device_semantic_profile(
            device_id=7,
            session=session,
            current_user=current_user,
        )

        mock_ensure_access.assert_called_once_with(session, current_user, 7)
        self.assertEqual(result["data"]["object_role"], "meter")

    @patch("app.api.endpoints.devices.management.ensure_device_access")
    @patch("app.api.endpoints.devices.management.DeviceService.get_device_for_read")
    def test_get_device_endpoint_uses_normalized_read_service(
        self,
        mock_get_device_for_read,
        mock_ensure_access,
    ):
        session = object()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        mock_get_device_for_read.return_value = SimpleNamespace(
            id=8,
            device_type="svg",
            device_category="compensation",
        )

        result = management.get_device(
            device_id=8,
            session=session,
            current_user=current_user,
        )

        mock_ensure_access.assert_called_once_with(session, current_user, 8)
        mock_get_device_for_read.assert_called_once_with(session, 8)
        self.assertEqual(result.device_category, "compensation")


if __name__ == "__main__":
    unittest.main()
