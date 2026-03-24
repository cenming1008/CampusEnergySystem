"""
能源领域规则：电价、碳排放、统计计算
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from app.core.settings import settings
from app.models.tables import EnergyType


CARBON_FACTORS = {
    EnergyType.ELECTRICITY: 0.5839,
    EnergyType.GAS: 2.162,
    EnergyType.HEAT: 0.11,
    EnergyType.WATER: 0.167,
    EnergyType.COOLING: 0.13,
    EnergyType.STEAM: 0.12,
}

ENERGY_UNITS = {
    EnergyType.ELECTRICITY: "kWh",
    EnergyType.WATER: "m³",
    EnergyType.GAS: "m³",
    EnergyType.HEAT: "GJ",
    EnergyType.COOLING: "kWh",
    EnergyType.STEAM: "t",
}

ENERGY_PRICES = {
    EnergyType.WATER: 3.5,
    EnergyType.GAS: 2.8,
    EnergyType.HEAT: 25.0,
    EnergyType.COOLING: 0.6,
    EnergyType.STEAM: 180.0,
}


def parse_hour_ranges(ranges_str: str) -> list[tuple[int, int]]:
    """解析时段配置字符串为 (start, end) 列表，左闭右开。"""
    result: list[tuple[int, int]] = []
    for part in ranges_str.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            start_str, end_str = part.split("-", 1)
            start, end = int(start_str.strip()), int(end_str.strip())
            if 0 <= start <= 24 and 0 <= end <= 24 and start < end:
                result.append((start, end))
        except (ValueError, AttributeError):
            continue
    return result


def is_hour_in_ranges(hour: int, ranges: Iterable[tuple[int, int]]) -> bool:
    """判断 hour (0-23) 是否落在任意区间 [start, end) 内。"""
    for start, end in ranges:
        if start <= hour < end:
            return True
    return False


def get_electricity_price(hour: int) -> float:
    """根据峰谷平时段获取电价。"""
    hour = max(0, min(23, int(hour)))
    peak_ranges = parse_hour_ranges(settings.electricity_peak_hours)
    flat_ranges = parse_hour_ranges(settings.electricity_flat_hours)
    if is_hour_in_ranges(hour, peak_ranges):
        return settings.peak_price
    if is_hour_in_ranges(hour, flat_ranges):
        return settings.flat_price
    return settings.valley_price


def calculate_energy_cost(energy_type: str, consumption: float, timestamp: datetime) -> float:
    """计算指定时间点的能源成本。"""
    if energy_type == EnergyType.ELECTRICITY:
        price = get_electricity_price(timestamp.hour)
    else:
        price = ENERGY_PRICES.get(energy_type, 0)
    return consumption * price


def build_carbon_fields(energy_type: str, consumption: float) -> dict[str, float | int | str]:
    """构建碳排放相关字段。"""
    carbon_factor = CARBON_FACTORS.get(energy_type, 0)
    return {
        "energy_type": energy_type,
        "energy_consumption": consumption,
        "consumption_unit": ENERGY_UNITS.get(energy_type, ""),
        "carbon_factor": carbon_factor,
        "carbon_emission": consumption * carbon_factor,
        "scope": 1 if energy_type in [EnergyType.GAS, EnergyType.HEAT] else 2,
    }


def summarize_energy_statistics(results: Iterable) -> dict[str, float | int]:
    """根据时序记录计算统计结果。"""
    rows = list(results)
    if not rows:
        return {
            "total_consumption": 0,
            "avg_consumption": 0,
            "avg_flow_rate": 0,
            "peak_flow_rate": 0,
            "data_count": 0,
        }

    consumptions = [row.consumption for row in rows]
    flow_rates = [row.flow_rate for row in rows if row.flow_rate is not None]
    return {
        "total_consumption": sum(consumptions),
        "avg_consumption": sum(consumptions) / len(consumptions),
        "avg_flow_rate": sum(flow_rates) / len(flow_rates) if flow_rates else 0,
        "peak_flow_rate": max(flow_rates) if flow_rates else 0,
        "data_count": len(rows),
    }


def summarize_carbon_by_energy_type(results: Iterable[tuple[str, float, float]]) -> dict[str, object]:
    """汇总按能源类型分组的碳排放结果。"""
    total_carbon = 0.0
    by_energy_type: dict[str, dict[str, object]] = {}

    for energy_type, emission, consumption in results:
        total_carbon += emission
        by_energy_type[energy_type] = {
            "carbon_emission": round(emission, 2),
            "energy_consumption": round(consumption, 2),
            "unit": ENERGY_UNITS.get(energy_type, ""),
        }

    return {
        "total_carbon": round(total_carbon, 2),
        "by_energy_type": by_energy_type,
    }


def calculate_manual_carbon(energy_type: str, consumption: float) -> dict[str, object]:
    """手动计算碳排放展示结果。"""
    carbon_factor = CARBON_FACTORS.get(energy_type, 0)
    return {
        "energy_type": energy_type,
        "consumption": consumption,
        "consumption_unit": ENERGY_UNITS.get(energy_type, ""),
        "carbon_factor": carbon_factor,
        "carbon_emission": round(consumption * carbon_factor, 2),
        "emission_unit": "kg CO2",
    }
