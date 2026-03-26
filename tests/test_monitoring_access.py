import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from fastapi import HTTPException

from app.api.deps import is_private_network_ip, require_monitoring_access


class MonitoringAccessTest(unittest.TestCase):
    def test_private_network_ip_detection(self):
        self.assertTrue(is_private_network_ip("127.0.0.1"))
        self.assertTrue(is_private_network_ip("10.0.0.9"))
        self.assertFalse(is_private_network_ip("8.8.8.8"))

    def test_internal_or_jwt_allows_private_network(self):
        request = SimpleNamespace(
            headers={},
            client=SimpleNamespace(host="127.0.0.1"),
        )
        with patch("app.api.deps.settings") as mock_settings:
            mock_settings.monitoring_access_mode = "internal_or_jwt"
            mock_settings.monitoring_access_roles = ["admin", "maintainer"]
            require_monitoring_access(request=request, current_user=None)

    def test_internal_or_jwt_rejects_public_without_token(self):
        request = SimpleNamespace(
            headers={"x-forwarded-for": "8.8.8.8"},
            client=SimpleNamespace(host="172.20.0.10"),
        )
        with patch("app.api.deps.settings") as mock_settings:
            mock_settings.monitoring_access_mode = "internal_or_jwt"
            mock_settings.monitoring_access_roles = ["admin", "maintainer"]
            with self.assertRaises(HTTPException) as ctx:
                require_monitoring_access(request=request, current_user=None)

        self.assertEqual(ctx.exception.status_code, 403)

    def test_internal_or_jwt_allows_authorized_role(self):
        request = SimpleNamespace(
            headers={"x-forwarded-for": "8.8.8.8"},
            client=SimpleNamespace(host="172.20.0.10"),
        )
        current_user = SimpleNamespace(role="admin")
        with patch("app.api.deps.settings") as mock_settings:
            mock_settings.monitoring_access_mode = "internal_or_jwt"
            mock_settings.monitoring_access_roles = ["admin", "maintainer"]
            require_monitoring_access(request=request, current_user=current_user)


if __name__ == "__main__":
    unittest.main()
