"""
MQTT 设备解析

负责从 MQTT 消息中提取 device_id / device_code，并在需要时自动创建设备。
"""

from __future__ import annotations

from typing import Any, Optional

from sqlmodel import Session, select

from app.core.database import engine
from app.core.device_registry import device_registry
from app.core.logger import logger
from app.core.settings import settings
from app.models.tables import Device
from app.services.device_service import DeviceService


def get_device_id_by_code(device_code: str, session: Session) -> Optional[int]:
    """根据设备编码（sn）查找设备主键 ID。"""
    device = session.exec(select(Device).where(Device.sn == device_code)).first()
    return device.id if device else None


def extract_device_code(data: dict[str, Any], topic: Optional[str]) -> Optional[str]:
    """优先从消息体获取 device_code，不存在时再从 topic 提取。"""
    device_code = data.get("device_code")
    if device_code is not None:
        normalized = str(device_code).strip()
        return normalized or None

    if not topic:
        return None

    parts = topic.split("/")
    if len(parts) >= 3 and parts[1] == "device":
        normalized = parts[2].strip()
        return normalized or None
    return None


def infer_device_type(data: dict[str, Any]) -> str:
    """根据遥测字段推断设备类型，用于未知设备自动注册。"""
    if data.get("flow_rate") is not None or (
        data.get("consumption") is not None
        and data.get("voltage") is None
        and data.get("current") is None
    ):
        if (
            data.get("heat_flow") is not None
            or data.get("heat_power") is not None
            or data.get("supply_temp") is not None
        ):
            return "heat_meter"
        if data.get("cooling_power") is not None:
            return "cooling_meter"
        return "water_meter"
    return "load"


def ensure_device_for_code(device_code: str, data: dict[str, Any]) -> Optional[int]:
    """
    若设备不存在且启用了自动创建，则创建设备并返回 device_id。
    """
    if not getattr(settings, "mqtt_auto_create_device", True):
        return None

    with Session(engine) as session:
        device_id = get_device_id_by_code(device_code, session)
        if device_id is not None:
            return device_id

        device_type = data.get("device_type") or infer_device_type(data)
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
            logger.info(
                f"MQTT 自动创建设备: sn={device_code}, name={name}, type={device_type}, id={device.id}"
            )
            return device.id
        except Exception as exc:
            logger.warning(f"MQTT 自动创建设备失败: device_code={device_code}, err={exc}")
            return None


def resolve_device_id(data: dict[str, Any], topic: Optional[str]) -> Optional[int]:
    """根据 payload 或 topic 解析 device_id，不存在时尝试自动创建设备。"""
    if "device_id" in data:
        try:
            device_id = int(str(data["device_id"]).strip())
            with Session(engine) as session:
                device = session.get(Device, device_id)
            return device_id if device else None
        except Exception as exc:
            logger.warning(f"MQTT resolve_device_id failed: raw={data.get('device_id')!r}, err={exc}")
            return None

    device_code = extract_device_code(data, topic)
    if not device_code:
        return None

    with Session(engine) as session:
        device_id = get_device_id_by_code(device_code, session)

    if device_id is not None:
        return device_id

    return ensure_device_for_code(device_code, data)
