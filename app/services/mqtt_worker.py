"""
MQTT Worker — 后台订阅与遥测数据处理。

支持断线自动重连、首次连接失败后台重试、指数退避。
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Optional

import paho.mqtt.client as mqtt

from app.core.logger import logger
from app.core.notifications import notification_service
from app.core.runtime_state import runtime_state
from app.core.settings import settings
from app.integrations.mqtt import process_payload

_RECONNECT_BASE_DELAY = 2
_RECONNECT_MAX_DELAY = 60
_INITIAL_RETRY_MAX_ATTEMPTS = 30

client: mqtt.Client | None = None
_shutdown_event = threading.Event()
_retry_thread: threading.Thread | None = None


def process_data(
    payload_str: str,
    topic: Optional[str] = None,
    broadcast_callback: Optional[Callable[[dict[str, Any]], Any]] = None,
):
    """处理一条 MQTT 消息：入库 +（可选）回调广播。"""
    ws_message = process_payload(payload_str, topic=topic)
    if broadcast_callback and ws_message:
        broadcast_callback(ws_message)
    return None


def _create_client() -> mqtt.Client:
    """创建并配置 MQTT 客户端实例。"""
    c = mqtt.Client()
    if settings.mqtt_username and settings.mqtt_password:
        c.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    c.reconnect_delay_set(min_delay=_RECONNECT_BASE_DELAY, max_delay=_RECONNECT_MAX_DELAY)
    return c


def _initial_connect_loop(c: mqtt.Client) -> bool:
    """首次连接重试循环，在后台线程运行直到成功或被要求关闭。"""
    delay = _RECONNECT_BASE_DELAY
    attempt = 0
    while not _shutdown_event.is_set() and attempt < _INITIAL_RETRY_MAX_ATTEMPTS:
        attempt += 1
        try:
            c.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
            c.loop_start()
            runtime_state.mark_service("mqtt", "healthy", "background loop started")
            logger.info(f"MQTT connected after {attempt} attempt(s)")
            return True
        except Exception as e:
            runtime_state.mark_service("mqtt", "unhealthy", str(e))
            logger.warning(f"MQTT connect attempt {attempt} failed: {e}, retrying in {delay}s")
            _shutdown_event.wait(delay)
            delay = min(delay * 2, _RECONNECT_MAX_DELAY)

    logger.error("MQTT initial connect exhausted all retries")
    notification_service.notify(
        event_key="mqtt.connect_failed",
        severity="critical",
        title="MQTT connection failed",
        message="MQTT 后台连接失败（重试次数已耗尽）",
        details={"broker": settings.mqtt_broker, "port": settings.mqtt_port},
    )
    return False


def start_mqtt_background(on_message_callback: Callable[[dict[str, Any]], Any]) -> bool:
    """启动 MQTT 后台监听线程（非阻塞）。"""
    global client, _retry_thread

    _shutdown_event.clear()
    c = _create_client()
    client = c

    def on_connect_internal(_client: mqtt.Client, _userdata: Any, _flags: dict, rc: int):
        if rc != 0:
            logger.warning(f"MQTT on_connect with non-zero rc={rc}")
            runtime_state.mark_service("mqtt", "unhealthy", f"connect rc={rc}")
            return
        logger.info(f"MQTT connected rc={rc}")
        runtime_state.mark_service("mqtt", "healthy", f"connected rc={rc}")
        _client.subscribe(settings.mqtt_topic)
        _client.subscribe(settings.mqtt_topic_wildcard)
        logger.info(f"MQTT subscribed: {settings.mqtt_topic}, {settings.mqtt_topic_wildcard}")

    def on_disconnect_internal(_client: mqtt.Client, _userdata: Any, rc: int):
        if _shutdown_event.is_set():
            logger.info("MQTT disconnected (shutdown requested)")
            return
        runtime_state.mark_service("mqtt", "unhealthy", f"disconnected rc={rc}")
        if rc != 0:
            logger.warning(f"MQTT unexpected disconnect rc={rc}, paho will auto-reconnect")
        else:
            logger.info("MQTT disconnected cleanly")

    def on_message_internal(_client: mqtt.Client, _userdata: Any, msg: mqtt.MQTTMessage):
        payload = msg.payload.decode(errors="ignore")
        process_data(payload, topic=getattr(msg, "topic", None), broadcast_callback=on_message_callback)

    c.on_connect = on_connect_internal
    c.on_disconnect = on_disconnect_internal
    c.on_message = on_message_internal

    try:
        c.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
        c.loop_start()
        runtime_state.mark_service("mqtt", "healthy", "background loop started")
        logger.info("MQTT loop started in background")
        return True
    except Exception as e:
        logger.warning(f"MQTT initial connect failed: {e}, starting background retry thread")
        runtime_state.mark_service("mqtt", "unhealthy", str(e))
        _retry_thread = threading.Thread(
            target=_initial_connect_loop, args=(c,), daemon=True, name="mqtt-retry"
        )
        _retry_thread.start()
        return False


def stop_mqtt() -> None:
    """优雅停止 MQTT 客户端和重试线程。"""
    global client, _retry_thread
    _shutdown_event.set()

    if _retry_thread and _retry_thread.is_alive():
        _retry_thread.join(timeout=5)
        _retry_thread = None

    if client is not None:
        try:
            client.loop_stop()
            client.disconnect()
        except Exception as exc:
            logger.warning(f"MQTT stop error: {exc}")
        finally:
            client = None

    runtime_state.mark_service("mqtt", "stopped", "graceful shutdown")
    logger.info("MQTT client stopped")


if __name__ == "__main__":
    def dummy_cb(msg: dict[str, Any]):
        logger.info(f"Dummy broadcast: {msg}")

    start_mqtt_background(dummy_cb)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_mqtt()
