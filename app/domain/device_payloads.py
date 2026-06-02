"""
设备领域规则：设备类型配置与上报数据规范化
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.core.device_registry import DeviceTypeConfig, device_registry
from app.models.tables import DeviceCategory

DEVICE_TYPE_ALIASES = {
    "reactive_power_compensator": "capacitor_bank_controller",
    "compensation": "capacitor_bank_controller",
}

COMPENSATION_DEVICE_SUBTYPES = {"svg", "capacitor_bank_controller"}
PLANNED_COMPENSATION_DEVICE_SUBTYPES = {"apf", "hybrid_compensation"}


def normalize_device_type_alias(device_type: Optional[str]) -> str:
    """将历史或泛化设备类型口径归一到当前注册表类型。"""
    normalized = (device_type or "").strip()
    if not normalized:
        return normalized
    return DEVICE_TYPE_ALIASES.get(normalized, normalized)


def normalize_device_subtype_alias(device_subtype: Optional[str]) -> Optional[str]:
    normalized = normalize_device_type_alias(device_subtype)
    return normalized or None


def resolve_compensation_subtype(
    device_type: Optional[str],
    device_subtype: Optional[str] = None,
) -> Optional[str]:
    """返回补偿类设备的规范子类型；非补偿类返回 None。"""
    normalized_subtype = normalize_device_subtype_alias(device_subtype)
    if normalized_subtype in COMPENSATION_DEVICE_SUBTYPES:
        return normalized_subtype

    normalized_type = normalize_device_type_alias(device_type)
    if normalized_type in COMPENSATION_DEVICE_SUBTYPES:
        return normalized_type

    return None


def is_compensation_device(
    device_type: Optional[str],
    device_subtype: Optional[str] = None,
    device_category: Optional[str] = None,
) -> bool:
    """判断设备是否属于补偿类主模型。"""
    if (device_category or "").strip() == DeviceCategory.COMPENSATION.value:
        return True
    return resolve_compensation_subtype(device_type, device_subtype) is not None


def resolve_device_identity(device_type: str, device_subtype: Optional[str] = None) -> dict[str, Optional[str]]:
    """将请求中的业务类型/子类型口径归一到当前存储结构。"""
    normalized_type = normalize_device_type_alias(device_type)
    normalized_subtype = resolve_compensation_subtype(device_type, device_subtype) or normalize_device_subtype_alias(device_subtype)

    if normalized_subtype:
        config = get_device_type_config(normalized_subtype)
        resolved_subtype = normalized_subtype if config.category.value == DeviceCategory.COMPENSATION.value else None
        return {
            "device_type": normalized_subtype,
            "device_subtype": resolved_subtype,
            "device_category": config.category.value,
            "energy_type": config.energy_type.value,
        }

    config = get_device_type_config(normalized_type)
    resolved_subtype = normalized_type if config.category.value == DeviceCategory.COMPENSATION.value else None
    return {
        "device_type": normalized_type,
        "device_subtype": resolved_subtype,
        "device_category": config.category.value,
        "energy_type": config.energy_type.value,
    }


OPTIONAL_REPORT_FIELDS = (
    "voltage",
    "current",
    "power_factor",
    "reactive_power",
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
    normalized_type = normalize_device_type_alias(device_type)
    config = device_registry.get(normalized_type)
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
    device_subtype: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    rated_capacity: Optional[float] = None,
    **extra_fields: Any,
) -> dict[str, Any]:
    """根据设备类型构建设备创建字段。"""
    resolved_identity = resolve_device_identity(device_type, device_subtype)
    config = get_device_type_config(resolved_identity["device_type"] or device_type)
    return {
        "name": name,
        "sn": sn,
        "device_type": resolved_identity["device_type"],
        "device_subtype": resolved_identity["device_subtype"],
        "device_category": resolved_identity["device_category"] or config.category.value,
        "energy_type": resolved_identity["energy_type"] or config.energy_type.value,
        "location": location,
        "description": description or f"{config.name_zh}设备",
        "rated_capacity": rated_capacity or config.default_capacity,
        "unit": config.unit,
        "is_active": True,
        **extra_fields,
    }


def build_device_registry_default_patch(
    device_type: Optional[str],
    device_subtype: Optional[str] = None,
    device_category: Optional[str] = None,
    energy_type: Optional[str] = None,
    unit: Optional[str] = None,
    rated_capacity: Optional[float] = None,
) -> dict[str, Any]:
    """Build missing legacy Device fields from registry defaults."""
    effective_subtype = resolve_compensation_subtype(device_type, device_subtype)
    effective_type = effective_subtype or normalize_device_type_alias(device_type)
    if not effective_type:
        return {}

    config = device_registry.get(effective_type)
    if not config:
        return {}

    patch: dict[str, Any] = {}
    normalized_category = normalize_device_category(
        effective_type,
        device_subtype,
        device_category,
    )
    if normalized_category:
        patch["device_category"] = normalized_category
    elif not device_category:
        patch["device_category"] = config.category.value

    if not energy_type:
        patch["energy_type"] = config.energy_type.value
    if not unit:
        patch["unit"] = config.unit
    if not rated_capacity and config.default_capacity:
        patch["rated_capacity"] = config.default_capacity

    compensation_subtype = (
        resolve_compensation_subtype(device_type, device_subtype)
        or resolve_compensation_subtype(effective_type)
    )
    if compensation_subtype and not device_subtype:
        patch["device_subtype"] = compensation_subtype

    return patch


def normalize_device_category(
    device_type: Optional[str],
    device_subtype: Optional[str],
    current_category: Optional[str],
) -> Optional[str]:
    """Normalize legacy compensation devices to the public compensation category."""
    if not is_compensation_device(device_type, device_subtype, current_category):
        return current_category
    if current_category == DeviceCategory.COMPENSATION.value:
        return current_category
    if current_category in (None, "", DeviceCategory.LOAD.value):
        return DeviceCategory.COMPENSATION.value
    return current_category


def describe_device_type_semantics(device_type: str) -> dict[str, Any]:
    """返回设备类型的第一批对象语义。"""
    config = get_device_type_config(device_type)
    return config.to_semantic_dict()


def describe_energy_data_fields(device_type: str) -> dict[str, Any]:
    """返回当前设备类型对应的 EnergyData 公共层 / 专属层语义。"""
    config = get_device_type_config(device_type)
    return {
        "device_type": config.device_type,
        "energy_type": config.energy_type.value,
        "public_fields": list(config.public_data_fields),
        "specialized_fields": list(config.specialized_fields),
        "required_fields": list(config.required_fields),
        "optional_fields": list(config.optional_fields),
        "compatible_aliases": dict(config.compatible_aliases),
        "null_field_rule": "nullable_specialized_field_means_not_applicable_or_not_reported",
        "point_kind": config.point_kind,
        "measurement_subject": config.measurement_subject,
        "consumption_unit": config.consumption_unit,
        "flow_unit": config.flow_unit,
        "supported_subtypes": sorted(COMPENSATION_DEVICE_SUBTYPES) if config.category.value == DeviceCategory.COMPENSATION.value else [],
        "planned_subtypes": sorted(PLANNED_COMPENSATION_DEVICE_SUBTYPES) if config.category.value == DeviceCategory.COMPENSATION.value else [],
    }


def normalize_device_report_payload(device_type: str, data: dict[str, Any]) -> DeviceReportPayload:
    """将设备上报数据规范化成统一入库结构。"""
    config = get_device_type_config(device_type)
    normalized = dict(data)

    for source_field, target_field in config.compatible_aliases.items():
        if target_field not in normalized and source_field in normalized:
            normalized[target_field] = normalized[source_field]

    if "flow_rate" not in normalized and "power" in normalized:
        normalized["flow_rate"] = normalized["power"]

    if "heat_flow" not in normalized and "heat_power" in normalized:
        normalized["heat_flow"] = normalized["heat_power"]

    if "flow_rate" not in normalized and "heat_flow" in normalized:
        normalized["flow_rate"] = normalized["heat_flow"]

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
