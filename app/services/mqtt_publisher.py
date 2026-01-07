"""
MQTT 指令下发

用于向设备发布启停等控制命令。
"""

from __future__ import annotations

import json

import paho.mqtt.client as mqtt

from app.core.logger import logger
from app.core.settings import settings


def publish_control_command(device_id: int, action: str) -> bool:
    """发送反向控制指令给设备（成功返回 True）。"""
    try:
        client = mqtt.Client()
        if settings.mqtt_username and settings.mqtt_password:
            client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

        client.connect(settings.mqtt_broker, settings.mqtt_port, 60)

        topic = f"mine/control/{device_id}"
        payload = json.dumps({"command": action, "device_id": device_id})

        client.publish(topic, payload, qos=1)
        client.disconnect()

        logger.info(f"MQTT control published: device_id={device_id} action={action}")
        return True
    except Exception as e:
        logger.warning(f"MQTT control publish failed: device_id={device_id} action={action} err={e}")
        return False