"""Pure campus EMS aggregation rules."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

ENERGY_CATEGORY_LABELS = {
    "electricity": "电",
    "water": "水",
    "gas": "气",
    "cooling": "冷",
    "heat": "热",
    "steam": "蒸汽",
}

SUB_ITEM_LABELS = {
    "load": "动力/普通负荷",
    "solar": "光伏",
    "wind": "风电",
    "water_meter": "给排水计量",
    "gas_meter": "燃气计量",
    "heat_meter": "供热计量",
    "cooling_meter": "供冷计量",
    "storage": "储能",
    "charger": "充电桩",
}


def build_energy_category_summary(summaries: Iterable[Any]) -> list[dict]:
    """Aggregate period energy summaries by energy category."""
    totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {"consumption": 0.0, "load": 0.0, "load_count": 0.0}
    )
    total_consumption = 0.0
    for summary in summaries:
        consumption = float(getattr(summary, "total_consumption", 0.0) or 0.0)
        energy_type = getattr(summary, "energy_type")
        item = totals[energy_type]
        item["consumption"] += consumption
        item["load"] += float(getattr(summary, "load_sum", 0.0) or 0.0)
        item["load_count"] += float(getattr(summary, "load_count", 0) or 0)
        total_consumption += consumption

    items = []
    for energy_type, value in sorted(
        totals.items(),
        key=lambda item: item[1]["consumption"],
        reverse=True,
    ):
        consumption = round(value["consumption"], 3)
        ratio = round((consumption / total_consumption) if total_consumption else 0.0, 4)
        load_count = max(int(value["load_count"]), 1)
        items.append(
            {
                "energy_category": energy_type,
                "label": ENERGY_CATEGORY_LABELS.get(energy_type, energy_type),
                "total_consumption": consumption,
                "avg_load": round(value["load"] / load_count, 3),
                "ratio": ratio,
                "estimated_carbon": round(consumption * 0.785, 3)
                if energy_type == "electricity"
                else 0.0,
            }
        )
    return items


def build_subitem_statistics(summaries: Iterable[Any], device_by_id: dict[int, Any]) -> list[dict]:
    """Aggregate period energy summaries by device category or type."""
    items: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "consumption": 0.0,
            "load": 0.0,
            "load_count": 0,
            "device_ids": set(),
            "energy_categories": set(),
        }
    )
    for summary in summaries:
        device = device_by_id.get(getattr(summary, "device_id"))
        if not device:
            continue
        sub_item = getattr(device, "device_category", None) or getattr(device, "device_type", None) or "device"
        item = items[sub_item]
        item["consumption"] += float(getattr(summary, "total_consumption", 0.0) or 0.0)
        item["load"] += float(getattr(summary, "load_sum", 0.0) or 0.0)
        item["load_count"] += int(getattr(summary, "load_count", 0) or 0)
        item["device_ids"].add(getattr(device, "id"))
        item["energy_categories"].add(getattr(summary, "energy_type"))

    result = []
    for sub_item, value in sorted(items.items(), key=lambda item: item[1]["consumption"], reverse=True):
        result.append(
            {
                "sub_item": sub_item,
                "label": SUB_ITEM_LABELS.get(sub_item, sub_item),
                "total_consumption": round(float(value["consumption"]), 3),
                "avg_load": round(float(value["load"]) / max(int(value["load_count"]), 1), 3),
                "device_count": len(value["device_ids"]),
                "energy_categories": sorted(value["energy_categories"]),
            }
        )
    return result
