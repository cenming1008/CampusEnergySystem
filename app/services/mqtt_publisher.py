"""
MQTT 指令下发

用于向设备发布启停、参数写入等控制命令。
使用持久连接避免每次下发都重新建立 TCP/MQTT 握手。
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt

from app.core.logger import logger
from app.core.settings import settings
from app.services.mqtt_tls import apply_tls

_lock = threading.Lock()
_publisher_client: mqtt.Client | None = None


def _resolve_publisher_credentials() -> tuple[str | None, str | None]:
    """优先使用控制下发专用账号，缺省回退到 ingest worker 账号。"""
    user = settings.mqtt_control_username or settings.mqtt_username
    pwd = settings.mqtt_control_password or settings.mqtt_password
    return user, pwd


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
        user, pwd = _resolve_publisher_credentials()
        if user and pwd:
            c.username_pw_set(user, pwd)
        apply_tls(c)
        c.reconnect_delay_set(min_delay=1, max_delay=30)
        c.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
        c.loop_start()
        _publisher_client = c
        return c


def _resolve_control_route_key(device_code: str | None, device_id: int) -> str:
    normalized = (device_code or "").strip()
    return normalized or str(device_id)


def _publish_control_payload_sync(
    device_id: int,
    payload: dict[str, Any],
    *,
    device_code: str | None = None,
    wait_timeout: float = 5.0,
) -> bool:
    """同步发送控制指令 payload，并等待 MQTT publish ack。"""
    try:
        pub = _get_publisher()
        route_key = _resolve_control_route_key(device_code, device_id)
        topic = f"{settings.mqtt_control_topic_prefix}{route_key}"
        normalized_payload = dict(payload)
        normalized_payload.setdefault("device_id", device_id)
        if device_code:
            normalized_payload.setdefault("device_code", device_code)
        normalized_payload.setdefault("timestamp", datetime.now().isoformat())
        raw_payload = json.dumps(normalized_payload, ensure_ascii=False)
        info = pub.publish(topic, raw_payload, qos=1)
        info.wait_for_publish(timeout=wait_timeout)
        logger.info(
            f"MQTT control published: device_id={device_id} device_code={device_code or '-'} "
            f"topic={topic} payload={raw_payload}"
        )
        return True
    except Exception as e:
        logger.warning(
            f"MQTT control publish failed: device_id={device_id} device_code={device_code or '-'} "
            f"payload={payload} err={e}"
        )
        return False


def publish_control_command(device_id: int, action: str, *, device_code: str | None = None) -> bool:
    """发送反向控制指令给设备（成功返回 True）。"""
    return _publish_control_payload_sync(
        device_id,
        {"command": action, "device_id": device_id},
        device_code=device_code,
    )


def publish_control_command_async(device_id: int, action: str, *, device_code: str | None = None) -> None:
    """后台异步发送控制指令，避免阻塞 API 返回。"""

    def _worker() -> None:
        _publish_control_payload_sync(
            device_id,
            {"command": action, "device_id": device_id},
            device_code=device_code,
        )

    threading.Thread(
        target=_worker,
        daemon=True,
        name=f"mqtt-publish-{device_id}-{action}",
    ).start()


def publish_control_payload_async(
    device_id: int,
    payload: dict[str, Any],
    *,
    device_code: str | None = None,
    worker_name: str = "mqtt-publish",
) -> None:
    """后台异步发送结构化控制 payload。"""

    def _worker() -> None:
        _publish_control_payload_sync(device_id, payload, device_code=device_code)

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
    device_code: str | None = None,
    command_id: str | None = None,
    reason: str | None = None,
    register: str | None = None,
    protocol_version: str | None = None,
    message_type: str | None = None,
    sent_at: str | None = None,
) -> None:
    """后台异步发送参数写入命令。"""
    payload = {
        "command": "write_parameter",
        "device_id": device_id,
        "parameter_key": parameter_key,
        "target_value": target_value,
    }
    if command_id:
        payload["command_id"] = command_id
    if reason:
        payload["reason"] = reason
    if register:
        payload["register"] = register
    if protocol_version:
        payload["protocol_version"] = protocol_version
    if message_type:
        payload["message_type"] = message_type
    if sent_at:
        payload["timestamp"] = sent_at

    threading.Thread(
        target=lambda: _publish_control_payload_sync(device_id, payload, device_code=device_code),
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
