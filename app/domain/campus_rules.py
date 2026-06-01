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
