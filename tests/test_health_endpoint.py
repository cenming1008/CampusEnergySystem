import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints import health
from app.core.runtime_state import runtime_state


class _FakeResult:
    def first(self):
        return 1


class _FakeSession:
    def exec(self, _statement):
        return _FakeResult()


class _FakeRedis:
    async def ping(self):
        return True


class HealthEndpointTest(unittest.IsolatedAsyncioTestCase):
    async def test_health_check_aggregates_bridge_and_worker_status(self):
        runtime_state.mark_service("mqtt_bridge", "healthy", "redis bridge subscribed")
        runtime_state.mark_service("api_realtime", "healthy", "broadcast delivered", meta={"last_event_type": "telemetry_update"})
        runtime_state.mark_service("scheduler", "healthy", "running")

        with patch.object(health.RedisClient, "get_client", return_value=_FakeRedis()):
            with patch.object(
                health,
                "load_worker_health",
                AsyncMock(return_value={"status": "healthy", "detail": "worker consuming", "updated_at": "2026-04-02T10:00:00"}),
            ):
                payload = await health.health_check(_=None, session=_FakeSession())

        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(payload["services"]["mqtt_bridge"], "healthy")
        self.assertEqual(payload["services"]["mqtt_worker"], "healthy")
        self.assertEqual(payload["services"]["api_realtime"], "healthy")
        self.assertEqual(payload["mqtt_worker"]["detail"], "worker consuming")
        self.assertEqual(payload["api_realtime"]["meta"]["last_event_type"], "telemetry_update")
        self.assertEqual(payload["semantics"]["readiness"], "/health/ready 只表达技术 readiness，不等于完整业务就绪")
        self.assertIn("replay", payload["business_signals"])

    async def test_health_check_marks_missing_worker_heartbeat_unhealthy(self):
        runtime_state.mark_service("mqtt_bridge", "healthy", "redis bridge subscribed")
        runtime_state.mark_service("api_realtime", "healthy", "broadcast delivered")
        runtime_state.mark_service("scheduler", "healthy", "running")

        with patch.object(health.RedisClient, "get_client", return_value=_FakeRedis()):
            with patch.object(
                health,
                "load_worker_health",
                AsyncMock(return_value={"status": "unhealthy", "detail": "worker heartbeat missing", "updated_at": None}),
            ):
                payload = await health.health_check(_=None, session=_FakeSession())

        self.assertEqual(payload["status"], "unhealthy")
        self.assertEqual(payload["services"]["mqtt_worker"], "unhealthy")

    async def test_readiness_check_requires_database_redis_worker_and_bridge(self):
        runtime_state.mark_service("mqtt_bridge", "healthy", "redis bridge subscribed")
        worker_health = {
            "status": "healthy",
            "detail": "worker consuming",
            "updated_at": datetime.now().isoformat(),
        }

        with patch.object(health.RedisClient, "get_client", return_value=_FakeRedis()):
            with patch.object(health, "load_worker_health", AsyncMock(return_value=worker_health)):
                payload = await health.readiness_check(_=None, session=_FakeSession())

        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["checks"]["database"], "ready")
        self.assertEqual(payload["checks"]["redis"], "ready")
        self.assertEqual(payload["checks"]["mqtt_worker_heartbeat"], "ready")
        self.assertEqual(payload["checks"]["mqtt_bridge"], "ready")
        self.assertEqual(payload["semantics"], "technical_readiness_only")
        self.assertIn("replay_summary", payload["diagnostics"]["excluded_signals"])

    async def test_readiness_check_rejects_stale_worker_heartbeat(self):
        runtime_state.mark_service("mqtt_bridge", "healthy", "redis bridge subscribed")
        stale_time = datetime.now() - timedelta(seconds=max(40, health.settings.mqtt_worker_health_ttl_seconds + 5))
        worker_health = {
            "status": "healthy",
            "detail": "worker consuming",
            "updated_at": stale_time.isoformat(),
        }

        with patch.object(health.RedisClient, "get_client", return_value=_FakeRedis()):
            with patch.object(health, "load_worker_health", AsyncMock(return_value=worker_health)):
                payload = await health.readiness_check(_=None, session=_FakeSession())

        self.assertEqual(payload["status"], "not_ready")
        self.assertEqual(payload["checks"]["mqtt_worker_heartbeat"], "not_ready")

    async def test_readiness_check_rejects_unhealthy_bridge(self):
        runtime_state.mark_service("mqtt_bridge", "unhealthy", "bridge down")
        worker_health = {
            "status": "healthy",
            "detail": "worker consuming",
            "updated_at": datetime.now().isoformat(),
        }

        with patch.object(health.RedisClient, "get_client", return_value=_FakeRedis()):
            with patch.object(health, "load_worker_health", AsyncMock(return_value=worker_health)):
                payload = await health.readiness_check(_=None, session=_FakeSession())

        self.assertEqual(payload["status"], "not_ready")
        self.assertEqual(payload["checks"]["mqtt_bridge"], "not_ready")


if __name__ == "__main__":
    unittest.main()
