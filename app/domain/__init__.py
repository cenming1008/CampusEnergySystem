"""
领域层
封装纯业务规则与字段规范化逻辑。
"""

from importlib import import_module

__all__ = [
    "CARBON_FACTORS",
    "ENERGY_PRICES",
    "ENERGY_UNITS",
    "DeviceReportPayload",
    "build_carbon_fields",
    "build_device_create_fields",
    "calculate_energy_cost",
    "calculate_manual_carbon",
    "get_device_type_config",
    "get_electricity_price",
    "normalize_device_report_payload",
    "parse_hour_ranges",
    "summarize_carbon_by_energy_type",
    "summarize_energy_statistics",
]

_EXPORT_MODULES = {
    "CARBON_FACTORS": "app.domain.energy_rules",
    "ENERGY_PRICES": "app.domain.energy_rules",
    "ENERGY_UNITS": "app.domain.energy_rules",
    "DeviceReportPayload": "app.domain.device_payloads",
    "build_carbon_fields": "app.domain.energy_rules",
    "build_device_create_fields": "app.domain.device_payloads",
    "calculate_energy_cost": "app.domain.energy_rules",
    "calculate_manual_carbon": "app.domain.energy_rules",
    "get_device_type_config": "app.domain.device_payloads",
    "get_electricity_price": "app.domain.energy_rules",
    "normalize_device_report_payload": "app.domain.device_payloads",
    "parse_hour_ranges": "app.domain.energy_rules",
    "summarize_carbon_by_energy_type": "app.domain.energy_rules",
    "summarize_energy_statistics": "app.domain.energy_rules",
}


def __getattr__(name):
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
