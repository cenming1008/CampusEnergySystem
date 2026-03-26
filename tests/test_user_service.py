import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.core.exceptions import ValidationException
from app.models.tables import UserRole
from app.services.user_service import UserService


class TestUserService(unittest.TestCase):
    @patch("app.services.user_service.UserRepository.get_by_username", return_value=None)
    @patch("app.services.user_service.UserRepository.save")
    @patch("app.services.user_service.get_password_hash", return_value="hashed-password")
    @patch("app.services.user_service.validate_password_strength", return_value="StrongPass123!")
    def test_create_user_saves_hashed_password(
        self,
        _mock_validate_password_strength,
        mock_get_password_hash,
        mock_save,
        _mock_get_by_username,
    ):
        session = MagicMock()
        mock_save.return_value = SimpleNamespace(username="alice", role=UserRole.VIEWER, is_active=True)

        result = UserService.create_user(
            session=session,
            username="alice",
            password="StrongPass123!",
            role=UserRole.VIEWER,
        )

        self.assertEqual(result.username, "alice")
        mock_get_password_hash.assert_called_once_with("StrongPass123!")
        mock_save.assert_called_once()
        saved_user = mock_save.call_args.args[1]
        self.assertTrue(saved_user.must_change_password)

    @patch("app.services.user_service.UserService.get_user_by_id")
    def test_update_user_role_blocks_self_demotion(self, mock_get_user_by_id):
        session = MagicMock()
        acting_user = SimpleNamespace(username="admin", role=UserRole.ADMIN)
        mock_get_user_by_id.return_value = SimpleNamespace(username="admin", role=UserRole.ADMIN)

        with self.assertRaises(ValidationException):
            UserService.update_user_role(
                session=session,
                user_id=1,
                role=UserRole.VIEWER,
                acting_user=acting_user,
            )

    @patch("app.services.user_service.UserService.get_user_by_id")
    def test_set_user_active_blocks_self_disable(self, mock_get_user_by_id):
        session = MagicMock()
        acting_user = SimpleNamespace(username="admin", role=UserRole.ADMIN)
        mock_get_user_by_id.return_value = SimpleNamespace(username="admin", is_active=True)

        with self.assertRaises(ValidationException):
            UserService.set_user_active(
                session=session,
                user_id=1,
                is_active=False,
                acting_user=acting_user,
            )

    @patch("app.services.user_service.UserRepository.get_by_username")
    @patch("app.services.user_service.UserRepository.save")
    def test_register_login_failure_locks_user_after_threshold(self, mock_save, mock_get_by_username):
        session = MagicMock()
        user = SimpleNamespace(username="alice", failed_login_attempts=4, locked_until=None)
        mock_get_by_username.return_value = user
        mock_save.return_value = user

        result = UserService.register_login_failure(session, "alice")

        self.assertEqual(result.failed_login_attempts, 5)
        self.assertIsNotNone(result.locked_until)
        self.assertGreater(result.locked_until, datetime.now())

    @patch("app.services.user_service.UserService.get_user_by_id")
    @patch("app.services.user_service.UserRepository.save")
    def test_revoke_user_tokens_increments_token_version(self, mock_save, mock_get_user_by_id):
        session = MagicMock()
        user = SimpleNamespace(username="alice", token_version=2)
        mock_get_user_by_id.return_value = user
        mock_save.return_value = user

        result = UserService.revoke_user_tokens(session, 1)

        self.assertEqual(result.token_version, 3)

    @patch("app.services.user_service.UserService.get_user_by_id")
    @patch("app.services.user_service.UserRepository.save")
    def test_rotate_refresh_session_increments_token_version(self, mock_save, mock_get_user_by_id):
        session = MagicMock()
        user = SimpleNamespace(username="alice", token_version=4, last_login_at=None)
        mock_get_user_by_id.return_value = user
        mock_save.return_value = user

        result = UserService.rotate_refresh_session(session, 1)

        self.assertEqual(result.token_version, 5)
        self.assertIsNotNone(result.last_login_at)

    @patch("app.services.user_service.UserRepository.save")
    def test_register_login_success_clears_lock_state(self, mock_save):
        session = MagicMock()
        user = SimpleNamespace(
            username="alice",
            failed_login_attempts=3,
            locked_until=datetime(2026, 3, 25, 12, 0, 0),
            last_login_at=None,
        )
        mock_save.return_value = user

        result = UserService.register_login_success(session, user)

        self.assertEqual(result.failed_login_attempts, 0)
        self.assertIsNone(result.locked_until)
        self.assertIsNotNone(result.last_login_at)

    @patch("app.services.user_service.UserService.get_user_by_id")
    @patch("app.services.user_service.UserRepository.save")
    def test_unlock_user_resets_failure_state(self, mock_save, mock_get_user_by_id):
        session = MagicMock()
        user = SimpleNamespace(
            username="alice",
            failed_login_attempts=5,
            locked_until=datetime(2026, 3, 25, 12, 0, 0),
        )
        mock_get_user_by_id.return_value = user
        mock_save.return_value = user

        result = UserService.unlock_user(session, 1)

        self.assertEqual(result.failed_login_attempts, 0)
        self.assertIsNone(result.locked_until)

    @patch("app.services.user_service.UserService.get_user_by_id")
    @patch("app.services.user_service.UserRepository.save")
    def test_change_own_password_clears_force_reset_and_rotates_tokens(self, mock_save, mock_get_user_by_id):
        session = MagicMock()
        user = SimpleNamespace(
            id=1,
            username="alice",
            hashed_password="hashed",
            must_change_password=True,
            failed_login_attempts=2,
            locked_until=datetime(2026, 3, 25, 12, 0, 0),
            token_version=7,
            last_password_changed_at=None,
        )
        mock_get_user_by_id.return_value = user
        mock_save.return_value = user

        with patch("app.services.user_service.verify_password", return_value=True), \
             patch("app.services.user_service.validate_password_strength", return_value="StrongPass123!"), \
             patch("app.services.user_service.get_password_hash", return_value="new-hash"):
            result = UserService.change_own_password(session, 1, "OldPass123!@", "StrongPass123!")

        self.assertFalse(result.must_change_password)
        self.assertEqual(result.failed_login_attempts, 0)
        self.assertIsNone(result.locked_until)
        self.assertEqual(result.token_version, 8)
        self.assertEqual(result.hashed_password, "new-hash")


if __name__ == "__main__":
    unittest.main()
