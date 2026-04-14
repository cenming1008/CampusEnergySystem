"""
MQTT 指令下发

用于向设备发布启停、参数写入等控制命令。
使用持久连接避免每次下发都重新建立 TCP/MQTT 握手。
"""

from __future__ import annotations

import json
import threading
from typing import Any

import paho.mqtt.client as mqtt

from app.core.logger import logger
from app.core.settings import settings

_lock = threading.Lock()
_publisher_client: mqtt.Client | None = None


def _get_publisher() -> mqtt.Client:
    """获取或创建持久 MQTT 发布客户端。"""
    global _publisher_client
    if _publisher_client is not None and _publisher_client.is_connected():
        return _publisher_client

    with _lock:
        if _publisher_client is not None and _publisher_client.is_connected():
            return _publisher_client

        if _publisher_client is not None:
            try:
                _publisher_client.loop_stop()
                _publisher_client.disconnect()
            except Exception:
                pass

        c = mqtt.Client()
        if settings.mqtt_username and settings.mqtt_password:
            c.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        c.reconnect_delay_set(min_delay=1, max_delay=30)
        c.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
        c.loop_start()
        _publisher_client = c
        return c


def _publish_control_payload_sync(device_id: int, payload: dict[str, Any], wait_timeout: float = 5.0) -> bool:
    """同步发送控制指令 payload，并等待 MQTT publish ack。"""
    try:
        pub = _get_publisher()
        topic = f"{settings.mqtt_control_topic_prefix}{device_id}"
        raw_payload = json.dumps(payload, ensure_ascii=False)
        info = pub.publish(topic, raw_payload, qos=1)
        info.wait_for_publish(timeout=wait_timeout)
        logger.info(f"MQTT control published: device_id={device_id} payload={raw_payload}")
        return True
    except Exception as e:
        logger.warning(f"MQTT control publish failed: device_id={device_id} payload={payload} err={e}")
        return False


def publish_control_command(device_id: int, action: str) -> bool:
    """发送反向控制指令给设备（成功返回 True）。"""
    return _publish_control_payload_sync(device_id, {"command": action, "device_id": device_id})


def publish_control_command_async(device_id: int, action: str) -> None:
    """后台异步发送控制指令，避免阻塞 API 返回。"""

    def _worker() -> None:
        _publish_control_payload_sync(device_id, {"command": action, "device_id": device_id})

    threading.Thread(
        target=_worker,
        daemon=True,
        name=f"mqtt-publish-{device_id}-{action}",
    ).start()


def publish_control_payload_async(device_id: int, payload: dict[str, Any], worker_name: str = "mqtt-publish") -> None:
    """后台异步发送结构化控制 payload。"""

    def _worker() -> None:
        _publish_control_payload_sync(device_id, payload)

    threading.Thread(
        target=_worker,
        daemon=True,
        name=f"{worker_name}-{device_id}",
    ).start()


def publish_parameter_write_async(
    device_id: int,
    parameter_key: str,
    target_value: Any,
    *,
    reason: str | None = None,
    register: str | None = None,
) -> None:
    """后台异步发送参数写入命令。"""
    payload = {
        "command": "write_parameter",
        "device_id": device_id,
        "parameter_key": parameter_key,
        "target_value": target_value,
    }
    if reason:
        payload["reason"] = reason
    if register:
        payload["register"] = register

    threading.Thread(
        target=lambda: _publish_control_payload_sync(device_id, payload),
        daemon=True,
        name=f"mqtt-write-{device_id}-{parameter_key}",
    ).start()


def stop_publisher() -> None:
    """优雅关闭发布客户端，由 lifecycle shutdown 调用。"""
    global _publisher_client
    with _lock:
        if _publisher_client is not None:
            try:
                _publisher_client.loop_stop()
                _publisher_client.disconnect()
            except Exception as exc:
                logger.warning(f"MQTT publisher stop error: {exc}")
            finally:
                _publisher_client = None
