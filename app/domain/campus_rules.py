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


def build_realtime_load_trend(rows: Iterable[Any]) -> list[dict]:
    """Aggregate row-like realtime readings into timestamp buckets."""
    buckets: dict[Any, dict[str, float]] = defaultdict(lambda: {"load": 0.0, "consumption": 0.0})
    grouped_rows: dict[tuple[Any, Any], list[Any]] = defaultdict(list)
    for row in rows:
        grouped_rows[(getattr(row, "device_id"), getattr(row, "energy_type"))].append(row)

    for group_rows in grouped_rows.values():
        ordered_rows = sorted(group_rows, key=lambda row: getattr(row, "timestamp"))
        previous_consumption = None
        for row in ordered_rows:
            timestamp = getattr(row, "timestamp")
            bucket = buckets[timestamp]
            bucket["load"] += float(getattr(row, "flow_rate", 0.0) or 0.0)
            current_consumption = float(getattr(row, "consumption", 0.0) or 0.0)
            if previous_consumption is not None:
                bucket["consumption"] += max(0.0, current_consumption - previous_consumption)
            previous_consumption = current_consumption

    return [
        {
            "timestamp": timestamp,
            "total_load": round(values["load"], 3),
            "total_consumption": round(values["consumption"], 3),
        }
        for timestamp, values in sorted(buckets.items(), key=lambda item: item[0])
    ]


def build_location_rankings(
    summaries: Iterable[Any],
    device_by_id: dict[int, Any],
    locations_by_id: dict[int, Any],
    target_types: set[str],
    top_n: int,
    find_ancestor: Any,
) -> list[dict]:
    """Aggregate period summaries into ranked target locations."""
    aggregates: dict[int, dict[str, Any]] = defaultdict(
        lambda: {
            "consumption": 0.0,
            "load": 0.0,
            "load_count": 0,
            "energy_breakdown": defaultdict(float),
        }
    )

    for summary in summaries:
        device = device_by_id.get(getattr(summary, "device_id"))
        location_id = getattr(device, "location_id", None) if device else None
        if location_id is None:
            continue
        target = find_ancestor(locations_by_id, location_id, target_types)
        if not target:
            continue
        item = aggregates[getattr(target, "id")]
        consumption = float(getattr(summary, "total_consumption", 0.0) or 0.0)
        item["consumption"] += consumption
        item["load"] += float(getattr(summary, "load_sum", 0.0) or 0.0)
        item["load_count"] += int(getattr(summary, "load_count", 0) or 0)
        item["energy_breakdown"][getattr(summary, "energy_type")] += consumption

    ranked_items = []
    for location_id, value in aggregates.items():
        location = locations_by_id.get(location_id)
        if not location:
            continue
        ranked_items.append(
            {
                "location_id": getattr(location, "id"),
                "name": getattr(location, "name"),
                "location_type": getattr(location, "location_type"),
                "full_path": getattr(location, "full_path"),
                "total_consumption": round(float(value["consumption"]), 3),
                "avg_load": round(float(value["load"]) / max(int(value["load_count"]), 1), 3),
                "energy_breakdown": {
                    energy_type: round(amount, 3)
                    for energy_type, amount in sorted(
                        value["energy_breakdown"].items(),
                        key=lambda item: item[1],
                        reverse=True,
                    )
                },
            }
        )

    ranked_items.sort(key=lambda item: item["total_consumption"], reverse=True)
    return ranked_items[:top_n]
