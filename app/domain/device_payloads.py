"""
设备领域规则：设备类型配置与上报数据规范化
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.core.device_registry import DeviceTypeConfig, device_registry


OPTIONAL_REPORT_FIELDS = (
    "voltage",
    "current",
    "power_factor",
    "pressure",
    "temperature",
    "supply_temp",
    "return_temp",
    "heat_flow",
    "quality_index",
)


@dataclass(frozen=True)
class DeviceReportPayload:
    consumption: float
    flow_rate: Optional[float]
    optional_fields: dict[str, Any]


def get_device_type_config(device_type: str) -> DeviceTypeConfig:
    """获取设备类型配置，不存在时抛出友好异常。"""
    config = device_registry.get(device_type)
    if config:
        return config

    available_types = device_registry.list_device_types()
    raise ValueError(
        f"不支持的设备类型: {device_type}。"
        f"支持的类型: {', '.join(available_types)}"
    )


def build_device_create_fields(
    name: str,
    sn: str,
    device_type: str,
    location: Optional[str] = None,
    description: Optional[str] = None,
    rated_capacity: Optional[float] = None,
    **extra_fields: Any,
) -> dict[str, Any]:
    """根据设备类型构建设备创建字段。"""
    config = get_device_type_config(device_type)
    return {
        "name": name,
        "sn": sn,
        "device_type": device_type,
        "device_category": config.category.value,
        "energy_type": config.energy_type.value,
        "location": location,
        "description": description or f"{config.name_zh}设备",
        "rated_capacity": rated_capacity or config.default_capacity,
        "unit": config.unit,
        "is_active": True,
        **extra_fields,
    }


def normalize_device_report_payload(device_type: str, data: dict[str, Any]) -> DeviceReportPayload:
    """将设备上报数据规范化成统一入库结构。"""
    config = get_device_type_config(device_type)
    normalized = dict(data)

    if "flow_rate" not in normalized and "power" in normalized:
        normalized["flow_rate"] = normalized["power"]

    if "heat_flow" not in normalized and "heat_power" in normalized:
        normalized["heat_flow"] = normalized["heat_power"]

    if "flow_rate" not in normalized and "cooling_power" in normalized:
        normalized["flow_rate"] = normalized["cooling_power"]

    for field in config.required_fields:
        if field not in normalized or normalized[field] is None:
            raise ValueError(f"缺少必需字段: {field}")

    consumption = normalized.get("consumption")
    if consumption is None:
        raise ValueError("consumption 字段是必需的")

    optional_fields = {
        field: normalized[field]
        for field in OPTIONAL_REPORT_FIELDS
        if field in normalized and normalized[field] is not None
    }

    return DeviceReportPayload(
        consumption=consumption,
        flow_rate=normalized.get("flow_rate"),
        optional_fields=optional_fields,
    )
