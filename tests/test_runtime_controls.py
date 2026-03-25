import os
import unittest

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from fastapi import HTTPException

from app.core.rate_limit import InMemoryRateLimiter
from app.core.runtime_state import RuntimeState


class TestInMemoryRateLimiter(unittest.TestCase):
    def test_rate_limiter_allows_within_window(self):
        limiter = InMemoryRateLimiter()

        limiter.check(bucket="auth", key="127.0.0.1", max_calls=2, window_seconds=60)
        limiter.check(bucket="auth", key="127.0.0.1", max_calls=2, window_seconds=60)

    def test_rate_limiter_rejects_when_limit_exceeded(self):
        limiter = InMemoryRateLimiter()

        limiter.check(bucket="auth", key="127.0.0.1", max_calls=1, window_seconds=60)

        with self.assertRaises(HTTPException) as ctx:
            limiter.check(bucket="auth", key="127.0.0.1", max_calls=1, window_seconds=60)

        self.assertEqual(ctx.exception.status_code, 429)


class TestRuntimeState(unittest.TestCase):
    def test_runtime_state_tracks_service_and_counters(self):
        state = RuntimeState()

        state.mark_service("mqtt", "healthy", "connected")
        state.increment("mqtt_messages_total")
        state.increment("mqtt_messages_total", amount=2)

        snapshot = state.snapshot()

        self.assertEqual(snapshot["services"]["mqtt"]["status"], "healthy")
        self.assertEqual(snapshot["counters"]["mqtt_messages_total"], 3)

    def test_runtime_state_snapshot_is_copy(self):
        state = RuntimeState()

        snapshot = state.snapshot()
        snapshot["counters"]["mqtt_messages_total"] = 999

        self.assertNotEqual(state.snapshot()["counters"]["mqtt_messages_total"], 999)


if __name__ == "__main__":
    unittest.main()
