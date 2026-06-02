"""Pure compensation-device domain rules."""

from __future__ import annotations

from typing import Any, Optional


def optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_power_factor(value: Any) -> Optional[float]:
    numeric = optional_float(value)
    if numeric is None:
        return None
    if numeric > 2:
        numeric = numeric / 100.0
    if numeric <= 0:
        return None
    return min(0.999, numeric)


def build_pq_reference_line(power_factor: float, *, role: str) -> dict[str, Any]:
    normalized = round(power_factor, 3)
    return {
        "powerFactor": normalized,
        "label": f"PF {normalized:.2f}",
        "role": role,
    }
