"""
能源接口轻量转换函数
"""

from __future__ import annotations

from .constants import ENERGY_DATA_OPTIONAL_FIELDS
from .schemas import EnergyDataCreate


def extract_optional_energy_fields(data: EnergyDataCreate) -> dict:
    return {
        field: value
        for field in ENERGY_DATA_OPTIONAL_FIELDS
        if (value := getattr(data, field)) is not None
    }
