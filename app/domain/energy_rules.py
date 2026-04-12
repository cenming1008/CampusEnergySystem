"""
能源领域规则：电价、统计、单位与展示级碳排估算。
"""

from __future__ import annotations

from datetime import datetime
from collections import defaultdict
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

ENERGY_DISPLAY_LABELS = {
    EnergyType.ELECTRICITY: "电",
    EnergyType.WATER: "水",
    EnergyType.GAS: "气",
    EnergyType.HEAT: "热",
    EnergyType.COOLING: "冷",
    EnergyType.STEAM: "蒸汽",
}

ENERGY_FLOW_UNITS = {
    EnergyType.ELECTRICITY: "kW",
    EnergyType.WATER: "m³/h",
    EnergyType.GAS: "m³/h",
    EnergyType.HEAT: "GJ/h",
    EnergyType.COOLING: "kW",
    EnergyType.STEAM: "t/h",
}

ENERGY_SEMANTICS = {
    EnergyType.ELECTRICITY: {
        "label": "电",
        "category": "electricity",
        "consumption_label": "累计电量",
        "consumption_semantics": "cumulative_meter_reading",
        "consumption_stat_basis": "period_delta_from_cumulative_reading",
        "flow_label": "实时有功功率",
        "flow_semantics": "instantaneous_power",
        "flow_stat_basis": "average_and_peak_of_instantaneous_samples",
        "supports_electrical_quality": True,
        "carbon_scope": 2,
        # 无功功率扩展字段语义
        "reactive_power_label": "无功功率",
        "reactive_power_unit": "kVAR",
        "reactive_power_semantics": "instantaneous_reactive_power",
        "reactive_power_sign_convention": "正值=感性负载吸收，负值=容性补偿输出",
    },
    EnergyType.WATER: {
        "label": "水",
        "category": "water",
        "consumption_label": "累计水量",
        "consumption_semantics": "cumulative_meter_reading",
        "consumption_stat_basis": "period_delta_from_cumulative_reading",
        "flow_label": "实时流量",
        "flow_semantics": "instantaneous_flow",
        "flow_stat_basis": "average_and_peak_of_instantaneous_samples",
        "supports_electrical_quality": False,
        "carbon_scope": 2,
    },
    EnergyType.GAS: {
        "label": "气",
        "category": "gas",
        "consumption_label": "累计气量",
        "consumption_semantics": "cumulative_meter_reading",
        "consumption_stat_basis": "period_delta_from_cumulative_reading",
        "flow_label": "实时流量",
        "flow_semantics": "instantaneous_flow",
        "flow_stat_basis": "average_and_peak_of_instantaneous_samples",
        "supports_electrical_quality": False,
        "carbon_scope": 1,
    },
    EnergyType.HEAT: {
        "label": "热",
        "category": "heat",
        "consumption_label": "累计热量",
        "consumption_semantics": "cumulative_meter_reading",
        "consumption_stat_basis": "period_delta_from_cumulative_reading",
        "flow_label": "瞬时热负荷",
        "flow_semantics": "instantaneous_heat_load",
        "flow_stat_basis": "average_and_peak_of_instantaneous_samples",
        "supports_electrical_quality": False,
        "carbon_scope": 1,
    },
    EnergyType.COOLING: {
        "label": "冷",
        "category": "cooling",
        "consumption_label": "累计冷量",
        "consumption_semantics": "cumulative_meter_reading",
        "consumption_stat_basis": "period_delta_from_cumulative_reading",
        "flow_label": "瞬时冷负荷",
        "flow_semantics": "instantaneous_cooling_load",
        "flow_stat_basis": "average_and_peak_of_instantaneous_samples",
        "supports_electrical_quality": False,
        "carbon_scope": 2,
    },
    EnergyType.STEAM: {
        "label": "蒸汽",
        "category": "steam",
        "consumption_label": "累计蒸汽量",
        "consumption_semantics": "cumulative_meter_reading",
        "consumption_stat_basis": "period_delta_from_cumulative_reading",
        "flow_label": "瞬时蒸汽流量",
        "flow_semantics": "instantaneous_flow",
        "flow_stat_basis": "average_and_peak_of_instantaneous_samples",
        "supports_electrical_quality": False,
        "carbon_scope": 1,
    },
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


def get_energy_semantics(energy_type: str) -> dict[str, object]:
    """返回第一批多能源语义定义。"""
    normalized = EnergyType(energy_type) if energy_type in EnergyType._value2member_map_ else energy_type
    semantics = dict(
        ENERGY_SEMANTICS.get(
            normalized,
            {
                "label": normalized,
                "category": normalized,
                "consumption_label": "累计量",
                "consumption_semantics": "cumulative_meter_reading",
                "consumption_stat_basis": "period_delta_from_cumulative_reading",
                "flow_label": "瞬时值",
                "flow_semantics": "instantaneous_value",
                "flow_stat_basis": "average_and_peak_of_instantaneous_samples",
                "supports_electrical_quality": False,
                "carbon_scope": 2,
            },
        )
    )
    semantics["energy_type"] = str(normalized)
    semantics["consumption_unit"] = ENERGY_UNITS.get(normalized, "")
    semantics["flow_unit"] = ENERGY_FLOW_UNITS.get(normalized, "")
    semantics["internal_standard_unit"] = ENERGY_UNITS.get(normalized, "")
    semantics["display_unit"] = ENERGY_UNITS.get(normalized, "")
    semantics["carbon_factor"] = CARBON_FACTORS.get(normalized, 0)
    return semantics


def build_carbon_fields(energy_type: str, consumption: float) -> dict[str, float | int | str]:
    """构建碳排放相关字段。"""
    semantics = get_energy_semantics(energy_type)
    carbon_factor = CARBON_FACTORS.get(energy_type, 0)
    return {
        "energy_type": energy_type,
        "energy_consumption": consumption,
        "consumption_unit": ENERGY_UNITS.get(energy_type, ""),
        "carbon_factor": carbon_factor,
        "carbon_emission": consumption * carbon_factor,
        "scope": int(semantics["carbon_scope"]),
        "calculation_method": "display_factor_snapshot",
    }


def calculate_period_delta(rows: Iterable) -> tuple[float, bool]:
    """按累计读数计算时段差值。"""
    ordered_rows = sorted(rows, key=lambda row: row.timestamp)
    if len(ordered_rows) < 2:
        return 0.0, False

    raw_delta = float(ordered_rows[-1].consumption or 0) - float(ordered_rows[0].consumption or 0)
    if raw_delta < 0:
        return 0.0, True
    return raw_delta, False


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

    energy_type = rows[0].energy_type
    semantics = get_energy_semantics(energy_type)
    flow_rates = [row.flow_rate for row in rows if row.flow_rate is not None]
    total_consumption, meter_reset_suspected = calculate_period_delta(rows)
    return {
        "total_consumption": round(total_consumption, 4),
        "avg_consumption": round(total_consumption / len(rows), 4) if rows else 0,
        "avg_flow_rate": sum(flow_rates) / len(flow_rates) if flow_rates else 0,
        "peak_flow_rate": max(flow_rates) if flow_rates else 0,
        "data_count": len(rows),
        "consumption_unit": semantics["consumption_unit"],
        "flow_unit": semantics["flow_unit"],
        "consumption_semantics": semantics["consumption_semantics"],
        "consumption_stat_basis": semantics["consumption_stat_basis"],
        "flow_semantics": semantics["flow_semantics"],
        "flow_stat_basis": semantics["flow_stat_basis"],
        "meter_reset_suspected": meter_reset_suspected,
    }


def summarize_carbon_by_energy_type(results: Iterable[tuple[str, float, float]]) -> dict[str, object]:
    """汇总按能源类型分组的碳排放结果。"""
    total_carbon = 0.0
    by_energy_type: dict[str, dict[str, object]] = {}

    for energy_type, emission, consumption in results:
        total_carbon += emission
        semantics = get_energy_semantics(energy_type)
        by_energy_type[energy_type] = {
            "carbon_emission": round(emission, 2),
            "energy_consumption": round(consumption, 2),
            "unit": ENERGY_UNITS.get(energy_type, ""),
            "carbon_factor": semantics["carbon_factor"],
            "scope": semantics["carbon_scope"],
            "boundary": "display_estimate",
            "calculation_method": "period_delta_x_factor",
        }

    return {
        "total_carbon": round(total_carbon, 2),
        "by_energy_type": by_energy_type,
        "boundary": "display_estimate",
        "calculation_method": "period_delta_x_factor",
        "is_accounting_grade": False,
        "note": "当前碳排结果用于展示和趋势试算，不作为正式碳核算结论。",
    }


def calculate_manual_carbon(energy_type: str, consumption: float) -> dict[str, object]:
    """手动计算碳排放展示结果。"""
    semantics = get_energy_semantics(energy_type)
    carbon_factor = CARBON_FACTORS.get(energy_type, 0)
    return {
        "energy_type": energy_type,
        "energy_label": semantics["label"],
        "consumption": consumption,
        "consumption_unit": ENERGY_UNITS.get(energy_type, ""),
        "carbon_factor": carbon_factor,
        "carbon_emission": round(consumption * carbon_factor, 2),
        "emission_unit": "kg CO2",
        "scope": semantics["carbon_scope"],
        "boundary": "display_estimate",
        "calculation_method": "period_delta_x_factor",
        "is_accounting_grade": False,
    }


def summarize_multi_energy_statistics(rows: Iterable) -> dict[str, dict[str, object]]:
    """按能源类型对累计量与瞬时量进行分组汇总。"""
    grouped: dict[str, list] = defaultdict(list)
    for row in rows:
        grouped[str(row.energy_type)].append(row)
    return {
        energy_type: summarize_energy_statistics(group_rows)
        for energy_type, group_rows in grouped.items()
    }
