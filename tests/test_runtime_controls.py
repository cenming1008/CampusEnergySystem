import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from fastapi import HTTPException
from redis.exceptions import RedisError

from app.core.rate_limit import InMemoryRateLimiter, RateLimiterFactory, RedisRateLimiter, SafeRateLimiter
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


class FakeRedisPipeline:
    def __init__(self, store):
        self.store = store
        self.key = None
        self.cutoff = None
        self.member = None
        self.score = None
        self.expiry = None

    def zremrangebyscore(self, key, _min_score, cutoff):
        self.key = key
        self.cutoff = cutoff
        return self

    def zcard(self, key):
        self.key = key
        return self

    def zadd(self, key, mapping):
        self.key = key
        self.member, self.score = next(iter(mapping.items()))
        return self

    def expire(self, key, seconds):
        self.key = key
        self.expiry = seconds
        return self

    def execute(self):
        entries = self.store.setdefault(self.key, [])
        entries[:] = [(member, score) for member, score in entries if score > self.cutoff]
        current_count = len(entries)
        entries.append((self.member, self.score))
        return (0, current_count, 1, True)


class FakeRedis:
    def __init__(self):
        self.store = {}

    def pipeline(self):
        return FakeRedisPipeline(self.store)

    def zrem(self, key, member):
        entries = self.store.get(key, [])
        self.store[key] = [(existing_member, score) for existing_member, score in entries if existing_member != member]


class ExplodingRateLimiter:
    def check(self, **_kwargs):
        raise RedisError("redis unavailable")


class TestRedisRateLimiter(unittest.TestCase):
    def test_redis_rate_limiter_rejects_when_limit_exceeded(self):
        limiter = RedisRateLimiter(FakeRedis(), key_prefix="test")

        limiter.check(bucket="auth", key="127.0.0.1", max_calls=1, window_seconds=60)

        with self.assertRaises(HTTPException) as ctx:
            limiter.check(bucket="auth", key="127.0.0.1", max_calls=1, window_seconds=60)

        self.assertEqual(ctx.exception.status_code, 429)

    def test_safe_rate_limiter_falls_back_to_memory(self):
        limiter = SafeRateLimiter(
            ExplodingRateLimiter(),
            fallback=InMemoryRateLimiter(),
            fail_open=False,
        )

        limiter.check(bucket="auth", key="127.0.0.1", max_calls=1, window_seconds=60)
        with self.assertRaises(HTTPException):
            limiter.check(bucket="auth", key="127.0.0.1", max_calls=1, window_seconds=60)


class TestRateLimiterFactory(unittest.TestCase):
    def tearDown(self):
        RateLimiterFactory.reset()

    def test_factory_uses_memory_backend_in_development_auto_mode(self):
        with patch("app.core.rate_limit.settings") as mock_settings:
            mock_settings.rate_limit_backend = "auto"
            mock_settings.is_production = False
            limiter = RateLimiterFactory.get()

        self.assertIsInstance(limiter, InMemoryRateLimiter)


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
