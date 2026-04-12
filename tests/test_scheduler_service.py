import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.core.runtime_state import runtime_state
from app.services import scheduler_service


class _FakeTask:
    def __init__(self):
        self._done = False

    def cancel(self):
        self._done = True

    def done(self):
        return self._done

    def __await__(self):
        async def _noop():
            return None

        return _noop().__await__()


class SchedulerServiceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        runtime_state.mark_service("scheduler", "unknown", None)
        scheduler_service._scheduler = None
        scheduler_service._lease_owner_token = None
        scheduler_service._lease_renew_task = None

    @staticmethod
    def _capture_task(fake_task):
        def _factory(coro):
            coro.close()
            return fake_task

        return _factory

    async def test_start_scheduler_becomes_owner_when_redis_lease_acquired(self):
        fake_task = _FakeTask()
        with patch.object(scheduler_service.settings, "scheduler_enabled", True), \
            patch.object(scheduler_service.settings, "scheduler_mode", "redis_owner"), \
            patch.object(scheduler_service.RedisClient, "acquire_lease", AsyncMock(return_value=True)), \
            patch.object(scheduler_service, "_start_scheduler_process") as mock_start_process, \
            patch.object(scheduler_service.asyncio, "create_task", side_effect=self._capture_task(fake_task)):
            result = await scheduler_service.start_scheduler()

        self.assertEqual(result["status"], "owner")
        self.assertTrue(result["owner"])
        mock_start_process.assert_called_once()
        snapshot = runtime_state.get_service("scheduler")
        self.assertEqual(snapshot["status"], "healthy")
        self.assertEqual(snapshot["meta"]["scheduler_state"], "owner")
        self.assertTrue(snapshot["meta"]["owner"])

    async def test_start_scheduler_marks_non_owner_instance_standby(self):
        with patch.object(scheduler_service.settings, "scheduler_enabled", True), \
            patch.object(scheduler_service.settings, "scheduler_mode", "redis_owner"), \
            patch.object(scheduler_service.RedisClient, "acquire_lease", AsyncMock(return_value=False)), \
            patch.object(scheduler_service.RedisClient, "get_value", AsyncMock(return_value="peer-instance")), \
            patch.object(scheduler_service, "_start_scheduler_process") as mock_start_process:
            result = await scheduler_service.start_scheduler()

        self.assertEqual(result["status"], "standby")
        self.assertFalse(result["owner"])
        mock_start_process.assert_not_called()
        snapshot = runtime_state.get_service("scheduler")
        self.assertEqual(snapshot["status"], "healthy")
        self.assertEqual(snapshot["meta"]["scheduler_state"], "standby")
        self.assertEqual(snapshot["meta"]["lease_holder"], "peer-instance")

    async def test_start_scheduler_fail_closed_when_redis_unavailable(self):
        with patch.object(scheduler_service.settings, "scheduler_enabled", True), \
            patch.object(scheduler_service.settings, "scheduler_mode", "redis_owner"), \
            patch.object(
                scheduler_service.RedisClient,
                "acquire_lease",
                AsyncMock(side_effect=RuntimeError("redis unavailable")),
            ), \
            patch.object(scheduler_service, "_start_scheduler_process") as mock_start_process:
            result = await scheduler_service.start_scheduler()

        self.assertEqual(result["status"], "failed-closed")
        self.assertFalse(result["owner"])
        mock_start_process.assert_not_called()
        snapshot = runtime_state.get_service("scheduler")
        self.assertEqual(snapshot["status"], "unhealthy")
        self.assertEqual(snapshot["meta"]["scheduler_state"], "failed-closed")

    async def test_stop_scheduler_releases_owner_lease(self):
        fake_task = _FakeTask()
        with patch.object(scheduler_service.settings, "scheduler_enabled", True), \
            patch.object(scheduler_service.settings, "scheduler_mode", "redis_owner"), \
            patch.object(scheduler_service.RedisClient, "acquire_lease", AsyncMock(return_value=True)), \
            patch.object(scheduler_service.RedisClient, "release_lease", AsyncMock(return_value=True)) as mock_release, \
            patch.object(scheduler_service, "_start_scheduler_process"), \
            patch.object(scheduler_service, "_stop_scheduler_process") as mock_stop_process, \
            patch.object(scheduler_service.asyncio, "create_task", side_effect=self._capture_task(fake_task)):
            await scheduler_service.start_scheduler()
            result = await scheduler_service.stop_scheduler()

        self.assertEqual(result["status"], "stopped")
        self.assertTrue(result["lease_released"])
        mock_stop_process.assert_called_once()
        mock_release.assert_awaited_once_with(
            scheduler_service.settings.scheduler_lease_key,
            scheduler_service._instance_id,
        )


if __name__ == "__main__":
    unittest.main()
