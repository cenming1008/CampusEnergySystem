"""
MQTT Worker

职责：
- 订阅设备遥测主题
- 解析消息并写入数据库（调用 `process_device_data`）
- 可选通过回调将消息转发给 WebSocket 等上层模块

对外函数：
- `start_mqtt_background(on_message_callback)`：启动后台监听
- `process_data(payload_str, topic=None, broadcast_callback=None)`：处理单条消息（便于测试/复用）
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable, Optional

import paho.mqtt.client as mqtt
from sqlmodel import Session, select

from app.core.database import engine
from app.core.logger import logger
from app.core.settings import settings
from app.models.tables import Device
from app.services.data_processor import process_device_data


client = mqtt.Client()


def get_device_id_by_code(device_code: str, session: Session) -> int | None:
    """根据设备编码（sn）查找设备主键 ID。"""
    device = session.exec(select(Device).where(Device.sn == device_code)).first()
    return device.id if device else None


def _extract_device_code(data: dict[str, Any], topic: Optional[str]) -> Optional[str]:
    device_code = data.get("device_code")
    if device_code:
        return str(device_code)

    if topic:
        parts = topic.split("/")
        # mine/device/{code}/telemetry
        if len(parts) >= 3 and parts[1] == "device":
            return parts[2]
    return None


def _resolve_device_id(data: dict[str, Any], topic: Optional[str]) -> Optional[int]:
    if "device_id" in data:
        try:
            return int(data["device_id"])
        except Exception:
            return None

    device_code = _extract_device_code(data, topic)
    if not device_code:
        return None

    with Session(engine) as session:
        device_id = get_device_id_by_code(device_code, session)
    return device_id


def _parse_timestamp(data: dict[str, Any]) -> datetime:
    ts = data.get("timestamp")
    if ts is None:
        return datetime.now()
    try:
        # epoch seconds
        return datetime.fromtimestamp(float(ts))
    except Exception:
        return datetime.now()


def _normalize_metrics(data: dict[str, Any]) -> tuple[float, float, float, float]:
    voltage = float(data.get("voltage", 380.0))
    current = float(data.get("current", 0.0))

    if "power" in data and data["power"] is not None:
        power = float(data["power"])
    else:
        power = voltage * current / 1000.0

    energy = float(data.get("energy", 0.0))
    return voltage, current, power, energy


def process_data(payload_str: str, topic: str | None = None, broadcast_callback: Callable[[dict[str, Any]], Any] | None = None):
    """处理一条 MQTT 消息：入库 +（可选）回调广播。"""
    try:
        data = json.loads(payload_str)
        if not isinstance(data, dict):
            logger.warning("MQTT payload is not a JSON object, skipped")
            return None
    except json.JSONDecodeError:
        logger.warning("MQTT payload JSON decode failed, skipped")
        return None

    device_id = _resolve_device_id(data, topic)
    if not device_id:
        logger.warning("MQTT payload missing device_id/device_code, skipped")
        return None

    ts = _parse_timestamp(data)
    voltage, current, power, energy = _normalize_metrics(data)

    with Session(engine) as session:
        record = process_device_data(
            session=session,
            device_id=device_id,
            voltage=voltage,
            current=current,
            power=power,
            energy=energy,
            timestamp=ts,
        )

    if broadcast_callback:
        ws_msg = {
            "type": "telemetry_update",
            "data": {
                "device_id": device_id,
                "voltage": record.voltage,
                "current": record.current,
                "power": record.power,
                "energy": record.energy,
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }
        broadcast_callback(ws_msg)

    return record


def start_mqtt_background(on_message_callback: Callable[[dict[str, Any]], Any]) -> None:
    """启动 MQTT 后台监听线程（非阻塞）。"""

    def on_connect_internal(_client, _userdata, _flags, rc):
        logger.info(f"MQTT connected rc={rc}")
        _client.subscribe(settings.mqtt_topic)
        _client.subscribe(settings.mqtt_topic_wildcard)
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