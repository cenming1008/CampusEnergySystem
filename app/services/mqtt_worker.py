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
from app.core.device_registry import device_registry
from app.models.tables import Device
from app.services.device_service import DeviceService
from app.services.alarm_service import AlarmService


client = mqtt.Client()


def get_device_id_by_code(device_code: str, session: Session) -> Optional[int]:
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


def _infer_device_type(data: dict[str, Any]) -> str:
    """根据遥测数据推断设备类型，用于自动创建设备。"""
    if data.get("flow_rate") is not None or (data.get("consumption") is not None and data.get("voltage") is None and data.get("current") is None):
        if data.get("heat_flow") is not None or data.get("heat_power") is not None or data.get("supply_temp") is not None:
            return "heat_meter"
        if data.get("cooling_power") is not None:
            return "cooling_meter"
        return "water_meter"
    return "load"


def _ensure_device_for_code(device_code: str, data: dict[str, Any]) -> Optional[int]:
    """
    若设备不存在且开启自动创建，则创建设备并返回 device_id；
    否则返回 None。
    """
    if not getattr(settings, "mqtt_auto_create_device", True):
        return None
    with Session(engine) as session:
        device_id = get_device_id_by_code(device_code, session)
        if device_id is not None:
            return device_id
        device_type = data.get("device_type") or _infer_device_type(data)
        if not device_registry.get(device_type):
            device_type = "load"
        name = data.get("device_name") or data.get("name") or f"设备-{device_code}"
        try:
            device = DeviceService.create_device_smart(
                session=session,
                name=name,
                sn=device_code,
                device_type=device_type,
            )
            logger.info(f"MQTT 自动创建设备: sn={device_code}, name={name}, type={device_type}, id={device.id}")
            return device.id
        except Exception as e:
            logger.warning(f"MQTT 自动创建设备失败: device_code={device_code}, err={e}")
            return None


def _resolve_device_id(data: dict[str, Any], topic: Optional[str]) -> Optional[int]:
    if "device_id" in data:
        try:
            did = int(data["device_id"])
            with Session(engine) as session:
                dev = session.get(Device, did)
            return did if dev else None
        except Exception:
            return None

    device_code = _extract_device_code(data, topic)
    if not device_code:
        return None

    with Session(engine) as session:
        device_id = get_device_id_by_code(device_code, session)
    if device_id is not None:
        return device_id
    return _ensure_device_for_code(device_code, data)


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


def process_data(payload_str: str, topic: Optional[str] = None, broadcast_callback: Optional[Callable[[dict[str, Any]], Any]] = None):
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
        # 构造数据字典，包含所有可能的字段
        data_dict = {
            # 通用字段
            "consumption": energy if energy > 0 else data.get("consumption", 0.0),
            "power": power,  # 保留 power 值（包括 0），电力设备的必需字段
            
            # 电力专用字段
            "voltage": voltage,
            "current": current,
            "power_factor": data.get("power_factor"),
            
            # 水/气专用字段
            "pressure": data.get("pressure"),
            "temperature": data.get("temperature"),
            "flow_rate": data.get("flow_rate"),  # 直接获取 flow_rate，字段映射在 device_service 中处理
            
            # 热/冷专用字段
            "supply_temp": data.get("supply_temp", data.get("supply_temperature")),
            "return_temp": data.get("return_temp", data.get("return_temperature")),
            "heat_flow": data.get("heat_flow"),  # 直接获取 heat_flow
            "heat_power": data.get("heat_power"),  # 保留原始 heat_power，映射在 device_service 中处理
            "cooling_power": data.get("cooling_power"),
        }
        
        # 过滤掉 None 值（但保留 0 值，因为 0 是有效的测量值）
        data_dict = {k: v for k, v in data_dict.items() if v is not None}
        
        record = DeviceService.report_device_data(
            session=session,
            device_id=device_id,
            data=data_dict,
            timestamp=ts
        )
        
        # 检查并创建报警
        AlarmService.check_and_create_alarm(
            session=session,
            device_id=device_id,
            data=data_dict,
            timestamp=ts
        )
        
        # 在 session 内提取需要的数据
        ws_data = {
            "device_id": device_id,
            "voltage": record.voltage,
            "current": record.current,
            "power": record.flow_rate,  # 瞬时功率/流量
            "energy": record.consumption,  # 累计消耗量
            "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }

    # 在 session 外发送 WebSocket 消息
    if broadcast_callback:
        ws_msg = {
            "type": "telemetry_update",
            "data": ws_data,
        }
        broadcast_callback(ws_msg)

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