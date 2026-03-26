import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from starlette.requests import Request

from app.main import request_observability_middleware


class RequestObservabilityMiddlewareTest(unittest.IsolatedAsyncioTestCase):
    async def test_exception_path_records_metrics_without_unboundlocal(self):
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/boom",
                "headers": [],
                "client": ("127.0.0.1", 12345),
                "scheme": "http",
                "server": ("testserver", 80),
                "query_string": b"",
            }
        )

        async def call_next(_request):
            raise RuntimeError("boom")

        with patch("app.main.set_audit_request_context", return_value="token") as mock_set_context:
            with patch("app.main.reset_audit_request_context") as mock_reset_context:
                with patch("app.main.observe_http_request") as mock_observe:
                    with self.assertRaises(RuntimeError):
                        await request_observability_middleware(request, call_next)

        mock_set_context.assert_called_once()
        mock_reset_context.assert_called_once_with("token")
        mock_observe.assert_called_once()
        self.assertEqual(mock_observe.call_args.kwargs["status_code"], 500)
