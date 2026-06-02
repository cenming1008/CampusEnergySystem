"""Pure compensation-device domain rules."""

from __future__ import annotations

from typing import Any, Optional

HEALTH_NOMINAL_VOLTAGE = 220.0


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


def clamp_health_score(value: float) -> int:
    return max(0, min(100, int(value + 0.5)))


def score_by_threshold(value: Optional[float], threshold: float) -> Optional[int]:
    if value is None:
        return 0
    ratio = float(value) / threshold
    if ratio <= 1:
        return clamp_health_score(100 - ratio * 20)
    return clamp_health_score(80 - (ratio - 1) * 40)


def max_defined_number(values: tuple[Optional[float], ...]) -> Optional[float]:
    defined = [float(value) for value in values if value is not None]
    return max(defined) if defined else None


def comm_health_score(ingestion_status: Optional[str], is_realtime_fresh: bool) -> Optional[int]:
    if ingestion_status == "online":
        return 100 if is_realtime_fresh else 70
    if ingestion_status == "degraded":
        return 55
    if ingestion_status == "offline":
        return 15
    return 0


def voltage_stability_score(
    voltage: Optional[float],
    nominal_voltage: float = HEALTH_NOMINAL_VOLTAGE,
) -> Optional[int]:
    if voltage is None:
        return 0
    deviation_pct = (abs(float(voltage) - nominal_voltage) / nominal_voltage) * 100
    return clamp_health_score(100 - deviation_pct * 4)


def switching_health_score(flags: tuple[Optional[bool], ...]) -> Optional[int]:
    if all(flag is None for flag in flags):
        return 0
    active_count = sum(1 for flag in flags if flag is True)
    return clamp_health_score(100 - active_count * 18)


def health_rating(score: Optional[int]) -> dict[str, str]:
    if score is None:
        return {"rating": "暂无评级", "ratingTone": "neutral"}
    if score >= 85:
        return {"rating": "优秀", "ratingTone": "success"}
    if score >= 70:
        return {"rating": "良好", "ratingTone": "success"}
    if score >= 50:
        return {"rating": "关注", "ratingTone": "warning"}
    return {"rating": "异常", "ratingTone": "danger"}
