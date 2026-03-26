import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.websocket import authenticate_websocket_token


class WebSocketAuthTest(unittest.TestCase):
    def test_authenticate_websocket_token_supports_access_token(self):
        websocket = SimpleNamespace(query_params={"access_token": "token-a"})
        self.assertEqual(authenticate_websocket_token(websocket), "token-a")

    def test_authenticate_websocket_token_supports_legacy_token_key(self):
        websocket = SimpleNamespace(query_params={"token": "token-b"})
        self.assertEqual(authenticate_websocket_token(websocket), "token-b")


if __name__ == "__main__":
    unittest.main()
