import asyncio
import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.core.error_handlers import app_exception_handler
from app.core.audit import (
    _serialize_audit_value,
    audit_log,
    get_audit_request_context,
    reset_audit_request_context,
    set_audit_request_context,
)
from app.core.exceptions import PermissionDeniedException
from app.api.endpoints.audit import _to_response
from app.models.tables import AuditEvent
from app.models.tables import UserRole


class TestAudit(unittest.TestCase):
    def test_serialize_audit_value_handles_enum_datetime_and_set(self):
        value = {
            "role": UserRole.ADMIN,
            "at": datetime(2026, 3, 25, 12, 30, 0),
            "ids": {3, 1},
        }

        serialized = _serialize_audit_value(value)

        self.assertEqual(serialized["role"], "admin")
        self.assertEqual(serialized["at"], "2026-03-25T12:30:00")
        self.assertEqual(serialized["ids"], [1, 3])

    def test_request_context_round_trip(self):
        token = set_audit_request_context(
            request_id="req-1",
            client_ip="10.0.0.5",
            method="POST",
            path="/users",
        )
        try:
            context = get_audit_request_context()
            self.assertEqual(context["request_id"], "req-1")
            self.assertEqual(context["client_ip"], "10.0.0.5")
            self.assertEqual(context["method"], "POST")
            self.assertEqual(context["path"], "/users")
        finally:
            reset_audit_request_context(token)

    def test_audit_event_response_parses_json_details(self):
        event = AuditEvent(
            id=7,
            action="device.toggle",
            actor="operator",
            target="device:12",
            outcome="success",
            actor_role="operator",
            details='{"request_id":"req-77","path":"/devices/12/toggle"}',
            created_at=datetime(2026, 3, 25, 13, 0, 0),
        )

        payload = _to_response(event)

        self.assertEqual(payload.id, 7)
        self.assertEqual(payload.details["request_id"], "req-77")
        self.assertEqual(payload.details["path"], "/devices/12/toggle")

    @patch("app.core.audit.logger")
    @patch("app.core.audit.Session")
    def test_audit_log_persists_event_when_database_available(self, mock_session_cls, mock_logger):
        session = MagicMock()
        context = MagicMock()
        context.__enter__.return_value = session
        context.__exit__.return_value = None
        mock_session_cls.return_value = context

        token = set_audit_request_context(
            request_id="req-2",
            client_ip="127.0.0.1",
            user_agent="pytest",
            method="POST",
            path="/users",
        )
        try:
            audit_log("user.create", "admin", "user:alice", role=UserRole.ADMIN, location_scope="1,2")
        finally:
            reset_audit_request_context(token)

        session.add.assert_called_once()
        session.commit.assert_called_once()
        mock_logger.warning.assert_called()
        event = session.add.call_args.args[0]
        self.assertIn("req-2", event.details)
        self.assertIn("/users", event.details)

    @patch("app.core.audit.logger")
    @patch("app.core.audit.Session")
    def test_audit_log_does_not_raise_when_persistence_fails(self, mock_session_cls, mock_logger):
        context = MagicMock()
        context.__enter__.side_effect = RuntimeError("db unavailable")
        mock_session_cls.return_value = context

        audit_log("auth.login", "alice", "auth", outcome="failed")

        self.assertGreaterEqual(mock_logger.warning.call_count, 2)

    @patch("app.core.error_handlers.audit_log")
    def test_permission_denied_handler_writes_access_denied_audit(self, mock_audit_log):
        request = SimpleNamespace(
            method="GET",
            url=SimpleNamespace(path="/devices/99"),
            state=SimpleNamespace(
                current_user=SimpleNamespace(username="viewer1", role=UserRole.VIEWER)
            ),
        )

        response = asyncio.run(
            app_exception_handler(request, PermissionDeniedException("当前用户无权访问该设备"))
        )

        self.assertEqual(response.status_code, 403)
        mock_audit_log.assert_called_once()
        call = mock_audit_log.call_args
        self.assertEqual(call.args[0], "access.denied")
        self.assertEqual(call.args[1], "viewer1")
        self.assertEqual(call.args[2], "/devices/99")


if __name__ == "__main__":
    unittest.main()
