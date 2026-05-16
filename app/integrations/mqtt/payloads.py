"""
MQTT payload 规范化工具。

本模块只处理字段别名、时间戳、数值和通用遥测入库 payload 构建。
设备专属遥测扩展应放在 device_extensions.py 或对应设备族 service。
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.core.logger import logger
from app.core.settings import settings
from app.integrations.mqtt.compensation import apply_compensation_field_aliases


FIELD_ALIASES = {
    "device_sn": "device_code",
    "sn": "device_code",
    "meter_code": "device_code",
    "ts": "timestamp",
    "time": "timestamp",
    "collect_time": "timestamp",
    "active_power": "power",
    "kw": "power",
    "total_energy": "energy",
    "meter_reading": "consumption",
    "cum_value": "consumption",
    "pf": "power_factor",
    "temp": "temperature",
}

MEANINGFUL_FIELDS = (
    "consumption",
    "energy",
    "flow_rate",
    "power",
    "heat_flow",
    "voltage",
    "current",
    "pressure",
    "temperature",
    "reactive_power",
)


def apply_field_aliases(data: dict[str, Any]) -> dict[str, Any]:
    """兼容常见字段别名，保持原字段优先。"""
    normalized = dict(data)
    for alias, canonical in FIELD_ALIASES.items():
        if canonical not in normalized and alias in normalized:
            normalized[canonical] = normalized[alias]
    return apply_compensation_field_aliases(normalized)


def parse_numeric(value: Any, field_name: str, default: Optional[float] = None) -> float:
    """解析数值字段，并拒绝 NaN/inf。"""
    if value is None:
        if default is None:
            raise ValueError(f"{field_name} 字段缺失")
        return default

    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{field_name} 字段不是有效数值")
    return parsed


def parse_timestamp(data: dict[str, Any]) -> datetime:
    """解析时间戳，缺失或非法时回退到当前时间。始终返回 naive datetime。"""
    timestamp = data.get("timestamp")
    if timestamp is None:
        return datetime.now()

    try:
        if isinstance(timestamp, str):
            normalized = timestamp.strip()
            if normalized.endswith("Z"):
                normalized = normalized[:-1] + "+00:00"
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is not None:
                dt = dt.astimezone(tz=None).replace(tzinfo=None)
            return dt

        return datetime.fromtimestamp(parse_numeric(timestamp, "timestamp"), tz=timezone.utc).replace(tzinfo=None)
    except Exception:
        logger.warning(f"MQTT timestamp parse failed, fallback to now: {timestamp!r}")
        return datetime.now()


def validate_timestamp(timestamp: datetime) -> datetime:
    """校验设备时间戳是否在可接受范围内。"""
    now = datetime.now()
    max_future_seconds = max(0, int(settings.mqtt_max_future_seconds))
    stale_data_days = max(0, int(settings.mqtt_stale_data_days))

    if timestamp > now and (timestamp - now).total_seconds() > max_future_seconds:
        raise ValueError("设备时间戳超前过多")

    if stale_data_days and timestamp < now - timedelta(days=stale_data_days):
        raise ValueError("设备时间戳过旧")

    return timestamp


def validate_payload_content(data: dict[str, Any]) -> None:
    """确保消息至少包含一项有效测点。"""
    if not any(data.get(field) is not None for field in MEANINGFUL_FIELDS):
        raise ValueError("MQTT payload 缺少有效测点")


def normalize_metrics(data: dict[str, Any]) -> tuple[float, float, float, float]:
    """标准化电压、电流、功率和能耗字段。"""
    voltage = parse_numeric(data.get("voltage"), "voltage", default=380.0)
    current = parse_numeric(data.get("current"), "current", default=0.0)

    if "power" in data and data["power"] is not None:
        power = parse_numeric(data["power"], "power")
    else:
        power = voltage * current / 1000.0

    energy = parse_numeric(data.get("energy"), "energy", default=0.0)
    return voltage, current, power, energy


def build_data_dict(data: dict[str, Any], voltage: float, current: float, power: float, energy: float) -> dict[str, Any]:
    """构建统一入库数据，保留 0 值并过滤 None。"""
    consumption = energy if energy > 0 else data.get("consumption", data.get("energy", 0.0))

    reactive_power_raw = data.get("reactive_power")
    reactive_power: Optional[float] = None
    if reactive_power_raw is not None:
        try:
            reactive_power = parse_numeric(reactive_power_raw, "reactive_power")
        except ValueError:
            reactive_power = None

    payload = {
        "consumption": parse_numeric(consumption, "consumption", default=0.0),
        "power": power,
        "voltage": voltage,
        "current": current,
        "power_factor": data.get("power_factor"),
        "reactive_power": reactive_power,
        "pressure": data.get("pressure"),
        "temperature": data.get("temperature"),
        "flow_rate": data.get("flow_rate"),
        "supply_temp": data.get("supply_temp", data.get("supply_temperature")),
        "return_temp": data.get("return_temp", data.get("return_temperature")),
        "heat_flow": data.get("heat_flow"),
        "heat_power": data.get("heat_power"),
        "cooling_power": data.get("cooling_power"),
    }

    return {key: value for key, value in payload.items() if value is not None}


__all__ = [
    "FIELD_ALIASES",
    "MEANINGFUL_FIELDS",
    "apply_field_aliases",
    "build_data_dict",
    "normalize_metrics",
    "parse_numeric",
    "parse_timestamp",
    "validate_payload_content",
    "validate_timestamp",
]
