"""
MQTT worker 与 API 之间的 Redis 实时事件桥接与健康状态同步。
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from datetime import datetime
from typing import Any, Optional

import redis

from app.core.logger import logger
from app.core.redis import RedisClient
from app.core.runtime_state import runtime_state
from app.core.settings import settings


class WorkerHealthReporter:
    """在 worker 进程中定期把健康状态写入 Redis。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._status = "starting"
        self._detail = "booting"
        self._meta: dict[str, Any] = {}
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def set_status(
        self,
        status: str,
        detail: Optional[str] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> None:
        with self._lock:
            self._status = status
            self._detail = detail
            if meta:
                self._meta.update(meta)
        _write_worker_health(status=status, detail=detail, meta=self._snapshot_meta())

    def record_event(self, **meta: Any) -> None:
        with self._lock:
            self._meta.update({k: v for k, v in meta.items() if v is not None})
            status = self._status
            detail = self._detail
            payload_meta = self._snapshot_meta()
        _write_worker_health(status=status, detail=detail, meta=payload_meta)

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="mqtt-worker-health-heartbeat",
        )
        self._thread.start()

    def stop(self, final_status: str = "stopped", detail: Optional[str] = "shutdown") -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        self.set_status(final_status, detail)

    def _heartbeat_loop(self) -> None:
        interval = max(1, int(settings.mqtt_worker_health_heartbeat_seconds))
        while not self._stop_event.wait(interval):
            with self._lock:
                status = self._status
                detail = self._detail
                payload_meta = self._snapshot_meta()
            _write_worker_health(status=status, detail=detail, meta=payload_meta)

    def _snapshot_meta(self) -> dict[str, Any]:
        return dict(self._meta)


def _get_sync_redis() -> redis.Redis:
    connection_kwargs: dict[str, Any] = {"encoding": "utf-8", "decode_responses": True}
    if settings.redis_password:
        connection_kwargs["password"] = settings.redis_password
    return redis.Redis.from_url(settings.redis_url, **connection_kwargs)


def publish_realtime_event(message: dict[str, Any]) -> None:
    """由 worker 调用，把实时事件发布到 Redis 频道。"""
    client = _get_sync_redis()
    try:
        client.publish(settings.mqtt_realtime_bridge_channel, json.dumps(message, ensure_ascii=True))
        runtime_state.increment("mqtt_bridge_publish_total")
    finally:
        try:
            client.close()
        except Exception:
            pass


def _write_worker_health(
    status: str,
    detail: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> None:
    client = _get_sync_redis()
    payload = {
        "status": status,
        "detail": detail,
        "updated_at": datetime.now().isoformat(),
        "pid": os.getpid(),
    }
    if meta:
        payload["meta"] = meta
    try:
        client.set(
            settings.mqtt_worker_health_key,
            json.dumps(payload, ensure_ascii=True),
            ex=max(5, int(settings.mqtt_worker_health_ttl_seconds)),
        )
    finally:
        try:
            client.close()
        except Exception:
            pass


async def load_worker_health() -> dict[str, Any]:
    """由 API 读取 worker 健康状态，用于汇总健康口径。"""
    redis_client = RedisClient.get_client()
    payload = await redis_client.get(settings.mqtt_worker_health_key)
    if not payload:
        return {
            "status": "unhealthy",
            "detail": "worker heartbeat missing",
            "updated_at": None,
        }

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return {
            "status": "unhealthy",
            "detail": "worker heartbeat invalid json",
            "updated_at": None,
        }

    return data


async def bridge_loop(stop_event: asyncio.Event, broadcast_callback) -> None:
    """
    API 进程内 Redis 订阅桥。

    worker 负责 publish，API 负责订阅后广播到 WebSocket。
    """
    while not stop_event.is_set():
        pubsub = None
        try:
            redis_client = RedisClient.get_client()
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(settings.mqtt_realtime_bridge_channel)
            runtime_state.mark_service(
                "mqtt_bridge",
                "healthy",
                "redis bridge subscribed",
                meta={
                    "channel": settings.mqtt_realtime_bridge_channel,
                    "last_subscribed_at": datetime.now().isoformat(),
                },
            )
            runtime_state.mark_service("api_realtime", "healthy", "broadcast idle")
            logger.info(f"✅ Redis 实时桥接已订阅频道: {settings.mqtt_realtime_bridge_channel}")

            while not stop_event.is_set():
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if not message:
                    await asyncio.sleep(0.1)
                    continue
                raw_data = message.get("data")
                if not raw_data:
                    continue
                try:
                    payload = json.loads(raw_data)
                except json.JSONDecodeError:
                    logger.warning("⚠️ Redis 实时桥接收到非法 JSON，已跳过")
                    continue
                runtime_state.increment("mqtt_bridge_messages_total")
                bridge_meta = {
                    "channel": settings.mqtt_realtime_bridge_channel,
                    "last_event_at": datetime.now().isoformat(),
                    "last_event_type": payload.get("type"),
                }
                runtime_state.mark_service("mqtt_bridge", "healthy", "redis event received", meta=bridge_meta)
                try:
                    await broadcast_callback(payload)
                    runtime_state.increment("mqtt_api_broadcast_total")
                    runtime_state.mark_service(
                        "api_realtime",
                        "healthy",
                        "broadcast delivered",
                        meta={
                            "last_broadcast_at": datetime.now().isoformat(),
                            "last_event_type": payload.get("type"),
                        },
                    )
                except Exception as exc:
                    runtime_state.increment("mqtt_api_broadcast_failures_total")
                    runtime_state.mark_service(
                        "api_realtime",
                        "unhealthy",
                        str(exc),
                        meta={
                            "last_broadcast_error_at": datetime.now().isoformat(),
                            "last_event_type": payload.get("type"),
                        },
                    )
                    raise
        except Exception as exc:
            runtime_state.mark_service("mqtt_bridge", "unhealthy", str(exc))
            logger.warning(f"⚠️ Redis 实时桥接异常，1s 后重试: {exc}")
            await asyncio.sleep(1)
        finally:
            if pubsub is not None:
                try:
                    await pubsub.unsubscribe(settings.mqtt_realtime_bridge_channel)
                    await pubsub.close()
                except Exception:
                    pass

    runtime_state.mark_service("mqtt_bridge", "stopped", "bridge stopped")
    runtime_state.mark_service("api_realtime", "stopped", "broadcast loop stopped")
