import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.application.users import (
    change_my_password_use_case,
    change_user_password_use_case,
    create_user_use_case,
    list_users_use_case,
    revoke_user_sessions_use_case,
    set_force_password_reset_use_case,
    unlock_user_use_case,
    update_user_location_scope_use_case,
    update_user_role_use_case,
    update_user_status_use_case,
)


class TestUserApplicationUseCases(unittest.TestCase):
    @patch("app.application.users.audit_log")
    @patch("app.application.users.UserService.list_users")
    def test_list_users_use_case_audits_and_returns_rows(self, mock_list_users, mock_audit_log):
        session = MagicMock()
        current_user = SimpleNamespace(username="admin", role="admin")
        rows = [SimpleNamespace(username="alice")]
        mock_list_users.return_value = rows

        result = list_users_use_case(session, current_user)

        self.assertEqual(result, rows)
        mock_audit_log.assert_called_once_with("user.list", "admin", "user:*", role="admin")

    @patch("app.application.users.audit_log")
    @patch("app.application.users.UserService.create_user")
    def test_create_user_use_case_normalizes_scope_and_audits(self, mock_create_user, mock_audit_log):
        session = MagicMock()
        current_user = SimpleNamespace(username="admin", role="admin")
        user = SimpleNamespace(username="bob")
        mock_create_user.return_value = user

        result = create_user_use_case(
            session=session,
            current_user=current_user,
            username="bob",
            password="StrongPass123!",
            role="viewer",
            location_scope=" 1,2 ",
        )

        self.assertIs(result, user)
        self.assertEqual(mock_create_user.call_args.kwargs["location_scope"], "1,2")
        mock_audit_log.assert_called_once()

    @patch("app.application.users.audit_log")
    @patch("app.application.users.UserService.update_user_role")
    def test_update_user_role_use_case_delegates_with_acting_user(self, mock_update_role, mock_audit_log):
        session = MagicMock()
        current_user = SimpleNamespace(username="admin", role="admin")
        user = SimpleNamespace(username="alice")
        mock_update_role.return_value = user

        result = update_user_role_use_case(session, current_user, 9, "maintainer")

        self.assertIs(result, user)
        mock_update_role.assert_called_once_with(session=session, user_id=9, role="maintainer", acting_user=current_user)
        mock_audit_log.assert_called_once()

    @patch("app.application.users.audit_log")
    @patch("app.application.users.UserService.set_user_active")
    def test_update_user_status_use_case_audits(self, mock_set_active, mock_audit_log):
        session = MagicMock()
        current_user = SimpleNamespace(username="admin", role="admin")
        user = SimpleNamespace(username="alice")
        mock_set_active.return_value = user

        result = update_user_status_use_case(session, current_user, 7, False)

        self.assertIs(result, user)
        mock_set_active.assert_called_once_with(session=session, user_id=7, is_active=False, acting_user=current_user)
        mock_audit_log.assert_called_once()

    @patch("app.application.users.audit_log")
    @patch("app.application.users.UserService.update_location_scope")
    def test_update_user_location_scope_use_case_normalizes_empty_scope(self, mock_update_scope, mock_audit_log):
        session = MagicMock()
        current_user = SimpleNamespace(username="admin", role="admin")
        user = SimpleNamespace(username="alice")
        mock_update_scope.return_value = user

        result = update_user_location_scope_use_case(session, current_user, 6, "   ")

        self.assertIs(result, user)
        self.assertIsNone(mock_update_scope.call_args.kwargs["location_scope"])
        mock_audit_log.assert_called_once()

    @patch("app.application.users.audit_log")
    @patch("app.application.users.UserService.change_password")
    def test_change_user_password_use_case_returns_message(self, mock_change_password, mock_audit_log):
        session = MagicMock()
        current_user = SimpleNamespace(username="admin", role="admin")
        mock_change_password.return_value = SimpleNamespace(username="alice")

        result = change_user_password_use_case(session, current_user, 3, "NewPass123!")

        self.assertEqual(result.message, "用户 alice 密码已更新")
        mock_audit_log.assert_called_once()

    @patch("app.application.users.audit_log")
    @patch("app.application.users.UserService.revoke_user_tokens")
    def test_revoke_user_sessions_use_case_returns_message(self, mock_revoke_tokens, mock_audit_log):
        session = MagicMock()
        current_user = SimpleNamespace(username="admin", role="admin")
        mock_revoke_tokens.return_value = SimpleNamespace(username="alice")

        result = revoke_user_sessions_use_case(session, current_user, 8)

        self.assertEqual(result.message, "用户 alice 已被强制下线")
        mock_audit_log.assert_called_once()

    @patch("app.application.users.audit_log")
    @patch("app.application.users.UserService.set_force_password_reset")
    def test_set_force_password_reset_use_case_audits(self, mock_set_reset, mock_audit_log):
        session = MagicMock()
        current_user = SimpleNamespace(username="admin", role="admin")
        user = SimpleNamespace(username="alice")
        mock_set_reset.return_value = user

        result = set_force_password_reset_use_case(session, current_user, 8, True)

        self.assertIs(result, user)
        mock_audit_log.assert_called_once()

    @patch("app.application.users.audit_log")
    @patch("app.application.users.UserService.unlock_user")
    def test_unlock_user_use_case_audits(self, mock_unlock_user, mock_audit_log):
        session = MagicMock()
        current_user = SimpleNamespace(username="admin", role="admin")
        user = SimpleNamespace(username="alice")
        mock_unlock_user.return_value = user

        result = unlock_user_use_case(session, current_user, 4)

        self.assertIs(result, user)
        mock_unlock_user.assert_called_once_with(session=session, user_id=4)
        mock_audit_log.assert_called_once()

    @patch("app.application.users.audit_log")
    @patch("app.application.users.UserService.change_own_password")
    def test_change_my_password_use_case_returns_message(self, mock_change_own_password, mock_audit_log):
        session = MagicMock()
        current_user = SimpleNamespace(id=5, username="alice", role="viewer")

        result = change_my_password_use_case(session, current_user, "OldPass123!", "NewPass123!")

        self.assertEqual(result.message, "密码已更新")
        mock_change_own_password.assert_called_once_with(
            session=session,
            user_id=5,
            current_password="OldPass123!",
            new_password="NewPass123!",
        )
        mock_audit_log.assert_called_once()


if __name__ == "__main__":
    unittest.main()
