"""
MQTT 指令下发

用于向设备发布启停等控制命令。
使用持久连接避免每次下发都重新建立 TCP/MQTT 握手。
"""

from __future__ import annotations

import json
import threading

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


def publish_control_command(device_id: int, action: str) -> bool:
    """发送反向控制指令给设备（成功返回 True）。"""
    try:
        pub = _get_publisher()
        topic = f"mine/control/{device_id}"
        payload = json.dumps({"command": action, "device_id": device_id})
        info = pub.publish(topic, payload, qos=1)
        info.wait_for_publish(timeout=5)
        logger.info(f"MQTT control published: device_id={device_id} action={action}")
        return True
    except Exception as e:
        logger.warning(f"MQTT control publish failed: device_id={device_id} action={action} err={e}")
        return False


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