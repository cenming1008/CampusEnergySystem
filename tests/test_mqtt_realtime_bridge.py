import asyncio
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.core.runtime_state import runtime_state
from app.services import mqtt_realtime_bridge


class _FakePubSub:
    def __init__(self, stop_event: asyncio.Event):
        self.stop_event = stop_event
        self.subscribed = []
        self.unsubscribed = []
        self.closed = False
        self._sent = False

    async def subscribe(self, channel: str):
        self.subscribed.append(channel)

    async def get_message(self, ignore_subscribe_messages: bool = True, timeout: float = 1.0):
        if self._sent:
            await asyncio.sleep(0)
            return None
        self._sent = True
        self.stop_event.set()
        return {"data": '{"type":"telemetry_update","data":{"device_id":9}}'}

    async def unsubscribe(self, channel: str):
        self.unsubscribed.append(channel)

    async def close(self):
        self.closed = True


class _FakeRedisClient:
    def __init__(self, pubsub):
        self._pubsub = pubsub

    def pubsub(self):
        return self._pubsub


class _FakeAsyncRedis:
    def __init__(self, payload):
        self.payload = payload

    async def get(self, _key: str):
        return self.payload


class MqttRealtimeBridgeTest(unittest.IsolatedAsyncioTestCase):
    async def test_bridge_loop_consumes_redis_messages_and_broadcasts(self):
        runtime_state.mark_service("mqtt_bridge", "unknown", None)
        stop_event = asyncio.Event()
        fake_pubsub = _FakePubSub(stop_event)
        fake_client = _FakeRedisClient(fake_pubsub)
        received = []

        async def fake_broadcast(message):
            received.append(message)

        with patch.object(mqtt_realtime_bridge.RedisClient, "get_client", return_value=fake_client):
            await mqtt_realtime_bridge.bridge_loop(stop_event, fake_broadcast)

        self.assertEqual(
            received,
            [{"type": "telemetry_update", "data": {"device_id": 9}}],
        )
        self.assertEqual(fake_pubsub.subscribed, [mqtt_realtime_bridge.settings.mqtt_realtime_bridge_channel])
        self.assertEqual(fake_pubsub.unsubscribed, [mqtt_realtime_bridge.settings.mqtt_realtime_bridge_channel])
        self.assertTrue(fake_pubsub.closed)
        snapshot = runtime_state.snapshot()
        self.assertEqual(snapshot["services"]["mqtt_bridge"]["status"], "stopped")
        self.assertEqual(snapshot["services"]["api_realtime"]["status"], "stopped")

    async def test_load_worker_health_returns_unhealthy_when_missing(self):
        with patch.object(
            mqtt_realtime_bridge.RedisClient,
            "get_client",
            return_value=_FakeAsyncRedis(None),
        ):
            payload = await mqtt_realtime_bridge.load_worker_health()

        self.assertEqual(payload["status"], "unhealthy")
        self.assertIn("heartbeat missing", payload["detail"])


if __name__ == "__main__":
    unittest.main()
