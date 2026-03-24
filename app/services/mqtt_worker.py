"""MQTT Worker。"""

from typing import Any, Callable, Optional

import paho.mqtt.client as mqtt

from app.core.logger import logger
from app.core.settings import settings
from app.integrations.mqtt import process_payload


client = mqtt.Client()


def process_data(payload_str: str, topic: Optional[str] = None, broadcast_callback: Optional[Callable[[dict[str, Any]], Any]] = None):
    """处理一条 MQTT 消息：入库 +（可选）回调广播。"""
    ws_message = process_payload(payload_str, topic=topic)
    if broadcast_callback and ws_message:
        broadcast_callback(ws_message)

    return None  # record 已经不在 session 中，返回 None


def start_mqtt_background(on_message_callback: Callable[[dict[str, Any]], Any]) -> None:
    """启动 MQTT 后台监听线程（非阻塞）。"""

    def on_connect_internal(_client, _userdata, _flags, rc):
        logger.info(f"MQTT connected rc={rc}")
        # 订阅两个主题（默认: mine/telemetry, mine/device/+/telemetry），设备发到任一个都会被 process_data 处理
        _client.subscribe(settings.mqtt_topic)           # 主题一，如 mine/telemetry
        _client.subscribe(settings.mqtt_topic_wildcard) # 主题二，如 mine/device/+/telemetry
        logger.info(f"MQTT subscribed: {settings.mqtt_topic}, {settings.mqtt_topic_wildcard}")

    def on_message_internal(_client, _userdata, msg):
        payload = msg.payload.decode(errors="ignore")
        process_data(payload, topic=getattr(msg, "topic", None), broadcast_callback=on_message_callback)

    client.on_connect = on_connect_internal
    client.on_message = on_message_internal

    try:
        if settings.mqtt_username and settings.mqtt_password:
            client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

        client.connect(settings.mqtt_broker, settings.mqtt_port, 60)
        client.loop_start()
        logger.info("MQTT loop started in background")
    except Exception as e:
        logger.error(f"MQTT connect failed: {e}")


if __name__ == "__main__":
    def dummy_cb(msg: dict[str, Any]):
        logger.info(f"Dummy broadcast: {msg}")

    start_mqtt_background(dummy_cb)
    client.loop_forever()
