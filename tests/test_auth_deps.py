import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.deps import ensure_password_change_completed
from app.core.exceptions import PermissionDeniedException


class TestAuthDeps(unittest.TestCase):
    def test_password_change_guard_allows_whitelisted_path(self):
        request = SimpleNamespace(
            url=SimpleNamespace(path="/users/me/password"),
            state=SimpleNamespace(
                current_user=SimpleNamespace(must_change_password=True)
            ),
        )

        ensure_password_change_completed(request)

    def test_password_change_guard_blocks_other_paths(self):
        request = SimpleNamespace(
            url=SimpleNamespace(path="/devices"),
            state=SimpleNamespace(
                current_user=SimpleNamespace(must_change_password=True)
            ),
        )

        with self.assertRaises(PermissionDeniedException):
            ensure_password_change_completed(request)


if __name__ == "__main__":
    unittest.main()
