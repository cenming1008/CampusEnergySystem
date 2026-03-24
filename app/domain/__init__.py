"""
领域层
封装纯业务规则与字段规范化逻辑。
"""

from app.domain.device_payloads import (
    DeviceReportPayload,
    build_device_create_fields,
    get_device_type_config,
    normalize_device_report_payload,
)
from app.domain.energy_rules import (
    CARBON_FACTORS,
    ENERGY_PRICES,
    ENERGY_UNITS,
    build_carbon_fields,
    calculate_energy_cost,
    calculate_manual_carbon,
    get_electricity_price,
    parse_hour_ranges,
    summarize_carbon_by_energy_type,
    summarize_energy_statistics,
)

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
