import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.core.access_control import (
    ensure_device_access,
    filter_devices_by_scope,
    get_accessible_route_ids,
    get_allowed_device_ids,
    parse_location_scope,
)
from app.core.exceptions import PermissionDeniedException
from app.models.tables import UserRole


class TestAccessControl(unittest.TestCase):
    def test_parse_location_scope_returns_none_for_admin(self):
        user = SimpleNamespace(role=UserRole.ADMIN, location_scope="1,2,3")
        self.assertIsNone(parse_location_scope(user))

    def test_parse_location_scope_parses_csv(self):
        user = SimpleNamespace(role=UserRole.VIEWER, location_scope="1, 2,3")
        self.assertEqual(parse_location_scope(user), {1, 2, 3})

    def test_filter_devices_by_scope_keeps_only_allowed_locations(self):
        user = SimpleNamespace(role=UserRole.VIEWER, location_scope="2")
        devices = [
            SimpleNamespace(id=1, location_id=1),
            SimpleNamespace(id=2, location_id=2),
        ]

        filtered = filter_devices_by_scope(devices, user)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, 2)

    def test_ensure_device_access_rejects_disallowed_location(self):
        session = MagicMock()
        session.get.return_value = SimpleNamespace(id=10, location_id=99)
        user = SimpleNamespace(role=UserRole.VIEWER, location_scope="2")

        with self.assertRaises(PermissionDeniedException):
            ensure_device_access(session, user, 10)

    def test_get_allowed_device_ids_uses_location_scope(self):
        session = MagicMock()
        exec_result = MagicMock()
        exec_result.all.return_value = [11, 12]
        session.exec.return_value = exec_result
        user = SimpleNamespace(role=UserRole.VIEWER, location_scope="3,4")

        allowed_ids = get_allowed_device_ids(session, user)

        self.assertEqual(allowed_ids, {11, 12})
        session.exec.assert_called_once()

    def test_get_accessible_route_ids_uses_location_scope(self):
        session = MagicMock()
        exec_result = MagicMock()
        exec_result.all.return_value = [21, 22]
        session.exec.return_value = exec_result
        user = SimpleNamespace(role=UserRole.OPERATOR, location_scope="5")

        route_ids = get_accessible_route_ids(session, user)

        self.assertEqual(route_ids, {21, 22})
        session.exec.assert_called_once()


if __name__ == "__main__":
    unittest.main()
