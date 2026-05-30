"""
能源接口兼容导出

新代码应优先从 schemas.py、constants.py 或 serializers.py 导入。
"""

from __future__ import annotations

from .constants import ENERGY_DATA_OPTIONAL_FIELDS, ENERGY_TYPE_OPTIONS
from .schemas import (
    CarbonSummaryResponse,
    EnergyDataCreate,
    EnergyOverviewResponse,
    EnergyStatisticsResponse,
)
from .serializers import extract_optional_energy_fields

__all__ = [
    "CarbonSummaryResponse",
    "ENERGY_DATA_OPTIONAL_FIELDS",
    "ENERGY_TYPE_OPTIONS",
    "EnergyDataCreate",
    "EnergyOverviewResponse",
    "EnergyStatisticsResponse",
    "extract_optional_energy_fields",
]
