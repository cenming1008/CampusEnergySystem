"""MQTT 客户端 TLS 配置辅助。

放在独立模块避免 mqtt_worker 与 mqtt_publisher 之间的循环依赖。
"""

from __future__ import annotations

import paho.mqtt.client as mqtt

from app.core.settings import settings


def apply_tls(client: mqtt.Client) -> None:
    """按 settings.mqtt_tls_* 配置为客户端启用 TLS。"""
    if not settings.mqtt_tls_enabled:
        return
    if not settings.mqtt_tls_ca_path:
        raise RuntimeError(
            "MQTT_TLS_ENABLED=True 但未设置 MQTT_TLS_CA_PATH，无法启动 TLS 连接"
        )
    client.tls_set(
        ca_certs=settings.mqtt_tls_ca_path,
        certfile=settings.mqtt_tls_certfile,
        keyfile=settings.mqtt_tls_keyfile,
    )
    if settings.mqtt_tls_insecure:
        client.tls_insecure_set(True)
