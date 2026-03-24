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
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    supply_temp: Optional[float] = None
    return_temp: Optional[float] = None
    heat_flow: Optional[float] = None


class CarbonSummaryResponse(BaseModel):
    """碳排放汇总响应"""

    total_carbon: float
    by_energy_type: dict


class EnergyStatisticsResponse(BaseModel):
    """能源统计响应"""

    total_consumption: float
    avg_consumption: float
    avg_flow_rate: float
    peak_flow_rate: float
    data_count: int


ENERGY_DATA_OPTIONAL_FIELDS = (
    "voltage",
    "current",
    "power_factor",
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
