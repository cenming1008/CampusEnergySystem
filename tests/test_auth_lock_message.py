import os
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.auth import login
from app.core.exceptions import AuthenticationException


class TestAuthLockMessage(unittest.TestCase):
    @patch("app.application.auth.audit_log")
    @patch("app.application.auth.UserService.register_login_failure")
    @patch("app.application.auth.verify_password", return_value=False)
    def test_fifth_failed_login_tells_user_when_lock_expires(
        self,
        _mock_verify_password,
        mock_register_login_failure,
        _mock_audit_log,
    ):
        locked_until = datetime.now() + timedelta(minutes=15)
        user = SimpleNamespace(
            username="alice",
            hashed_password="hashed-password",
            locked_until=None,
        )
        mock_register_login_failure.return_value = SimpleNamespace(
            username="alice",
            failed_login_attempts=5,
            locked_until=locked_until,
        )
        query_result = MagicMock()
        query_result.first.return_value = user
        session = MagicMock()
        session.exec.return_value = query_result

        with self.assertRaises(AuthenticationException) as raised:
            login(
                request=SimpleNamespace(client=None, headers={}),
                form_data=SimpleNamespace(username="alice", password="wrong-password"),
                session=session,
            )

        self.assertIn("连续登录失败 5 次", raised.exception.message)
        self.assertIn(locked_until.strftime("%Y-%m-%d %H:%M:%S"), raised.exception.message)

    @patch("app.application.auth.audit_log")
    @patch("app.api.endpoints.auth._enforce_auth_login_rate_limit")
    def test_locked_login_tells_user_when_lock_expires_before_rate_limit(
        self,
        mock_enforce_rate_limit,
        _mock_audit_log,
    ):
        locked_until = datetime.now() + timedelta(minutes=15)
        user = SimpleNamespace(
            username="alice",
            hashed_password="hashed-password",
            locked_until=locked_until,
        )
        query_result = MagicMock()
        query_result.first.return_value = user
        session = MagicMock()
        session.exec.return_value = query_result

        with self.assertRaises(AuthenticationException) as raised:
            login(
                request=SimpleNamespace(client=None, headers={}),
                form_data=SimpleNamespace(username="alice", password="wrong-password"),
                session=session,
            )

        mock_enforce_rate_limit.assert_not_called()
        self.assertIn("连续登录失败 5 次", raised.exception.message)
        self.assertIn(locked_until.strftime("%Y-%m-%d %H:%M:%S"), raised.exception.message)


if __name__ == "__main__":
    unittest.main()
