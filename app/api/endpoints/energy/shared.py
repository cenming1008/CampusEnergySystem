"""
能源接口共享模型与常量
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EnergyDataCreate(BaseModel):
    """能源数据创建模型"""

    device_id: int
    energy_type: str
    consumption: float
    flow_rate: Optional[float] = None
    timestamp: Optional[datetime] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_factor: Optional[float] = None
    reactive_power: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    supply_temp: Optional[float] = None
    return_temp: Optional[float] = None
    heat_flow: Optional[float] = None


class CarbonSummaryResponse(BaseModel):
    """碳排放汇总响应"""

    total_carbon: float
    by_energy_type: dict
    boundary: Optional[str] = None
    calculation_method: Optional[str] = None
    is_accounting_grade: Optional[bool] = None
    note: Optional[str] = None
    summary_basis: Optional[str] = None


class EnergyStatisticsResponse(BaseModel):
    """能源统计响应"""

    total_consumption: float
    avg_consumption: float
    avg_flow_rate: float
    peak_flow_rate: float
    data_count: int
    consumption_unit: Optional[str] = None
    flow_unit: Optional[str] = None
    consumption_semantics: Optional[str] = None
    consumption_stat_basis: Optional[str] = None
    flow_semantics: Optional[str] = None
    flow_stat_basis: Optional[str] = None
    meter_reset_suspected: Optional[bool] = None
    data_object_kind: Optional[str] = None
    point_kind: Optional[str] = None
    public_fields: Optional[list[str]] = None
    specialized_fields: Optional[list[str]] = None
    null_field_rule: Optional[str] = None


class EnergyOverviewResponse(BaseModel):
    """多能源管理聚合响应。"""

    statistics: dict
    carbon_summary: CarbonSummaryResponse
    overview_boundary: Optional[str] = None
    unit_rule: Optional[str] = None
    cross_energy_mix_allowed: Optional[bool] = None
    field_boundary_rule: Optional[str] = None
    energy_profiles: Optional[dict] = None
    # 合并自原 /analysis/overview 的分析字段；当 include_analysis=False 时为 None
    time_window: Optional[dict] = None
    scope: Optional[dict] = None
    summary: Optional[dict] = None
    trend: Optional[dict] = None
    comparison: Optional[dict] = None
    ranking: Optional[dict] = None
    anomaly: Optional[dict] = None
    insights: Optional[list] = None


ENERGY_TYPE_OPTIONS = [
    {"value": "electricity", "label": "电力", "unit": "kWh", "flow_unit": "kW"},
    {"value": "water", "label": "水", "unit": "m³", "flow_unit": "m³/h"},
    {"value": "gas", "label": "燃气", "unit": "m³", "flow_unit": "m³/h"},
    {"value": "heat", "label": "热力", "unit": "GJ", "flow_unit": "GJ/h"},
    {"value": "cooling", "label": "冷气", "unit": "kWh", "flow_unit": "kW"},
    {"value": "steam", "label": "蒸汽", "unit": "t", "flow_unit": "t/h"},
]


ENERGY_DATA_OPTIONAL_FIELDS = (
    "voltage",
    "current",
    "power_factor",
    "reactive_power",
    "pressure",
    "temperature",
    "supply_temp",
    "return_temp",
    "heat_flow",
)


def extract_optional_energy_fields(data: EnergyDataCreate) -> dict:
    return {
        field: value
        for field in ENERGY_DATA_OPTIONAL_FIELDS
        if (value := getattr(data, field)) is not None
    }
