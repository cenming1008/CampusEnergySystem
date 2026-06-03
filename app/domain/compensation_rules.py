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


def count_active_bits(value: Optional[int]) -> int:
    if not isinstance(value, int):
        return 0
    count = 0
    for bit in range(16):
        if value & (1 << bit):
            count += 1
    return count


def resolve_capacitor_bank_circuit_total(
    explicit_total_counts: tuple[Optional[int], ...],
    configured_output_counts: tuple[Optional[int], ...],
) -> int:
    if any(value is not None for value in explicit_total_counts):
        return sum(max(0, int(value or 0)) for value in explicit_total_counts)

    configured_total = sum(max(0, int(value or 0)) for value in configured_output_counts)
    return configured_total or 24


def build_capacitor_bank_circuit_summary(
    *,
    telemetry_running_count: Optional[int],
    telemetry_bitmasks: tuple[Optional[int], ...],
    explicit_total_counts: tuple[Optional[int], ...],
    configured_output_counts: tuple[Optional[int], ...],
    profile_running_count: Optional[int],
    profile_running_values: tuple[Optional[int], ...],
) -> dict[str, Any]:
    total_count = max(1, resolve_capacitor_bank_circuit_total(explicit_total_counts, configured_output_counts))
    if telemetry_running_count is not None:
        return {
            "running_count": int(telemetry_running_count),
            "total_count": total_count,
            "has_realtime_state": True,
            "source": "telemetry",
            "state": "live",
        }

    if any(value is not None for value in telemetry_bitmasks):
        return {
            "running_count": sum(count_active_bits(value) for value in telemetry_bitmasks),
            "total_count": total_count,
            "has_realtime_state": True,
            "source": "telemetry",
            "state": "live",
        }

    resolved_profile_running_count = profile_running_count
    if resolved_profile_running_count is None and any(value is not None for value in profile_running_values):
        resolved_profile_running_count = sum(max(0, int(value or 0)) for value in profile_running_values)

    if resolved_profile_running_count is not None:
        return {
            "running_count": max(0, min(total_count, int(resolved_profile_running_count))),
            "total_count": total_count,
            "has_realtime_state": True,
            "source": "profile",
            "state": "live",
        }

    return {
        "running_count": 0,
        "total_count": total_count,
        "has_realtime_state": False,
        "source": "configured_fallback",
        "state": "mock",
    }


def build_capacitor_bank_temperature_health(
    *,
    temp_alarm: Optional[bool],
    threshold: Optional[float],
    cabinet_temperature: Optional[float],
    warning_margin: float,
) -> dict[str, Any]:
    if temp_alarm is True:
        return {"value": "温度告警", "source": "telemetry", "state": "live"}

    if cabinet_temperature is None:
        return {"value": "待判断", "source": "missing", "state": "missing"}

    if threshold is not None:
        current = float(cabinet_temperature)
        upper_limit = float(threshold)
        normalized_warning_margin = max(0.0, float(warning_margin or 0.0))
        if current >= upper_limit:
            return {"value": "超过上限", "source": "profile", "state": "live"}
        if current >= upper_limit - normalized_warning_margin:
            return {"value": "接近上限", "source": "profile", "state": "live"}
        return {"value": "正常", "source": "profile", "state": "live"}

    if temp_alarm is False:
        return {"value": "正常", "source": "telemetry", "state": "live"}

    return {"value": "待判断", "source": "missing", "state": "missing"}


def resolve_capacitor_bank_control_log_mode(
    *,
    normalized_result: Optional[str],
    action: Optional[str],
    reason: Optional[str],
) -> str:
    if normalized_result != "success":
        return ""
    if action not in {"switch_control_mode", "manual_switch"}:
        return ""
    normalized_reason = str(reason or "").strip()
    if "控制模式切换" not in normalized_reason:
        return ""
    if "手动模式" in normalized_reason:
        return "手动"
    if "自动模式" in normalized_reason:
        return "自动"
    return ""


def resolve_capacitor_bank_control_mode(
    *,
    telemetry_mode: Optional[str],
    telemetry_timestamp: Any,
    profile_mode: Optional[str],
    profile_scheme: Optional[str],
    profile_timestamp: Any,
    latest_log_mode: str,
    latest_log_created_at: Any,
    is_device_active: bool,
) -> dict[str, str]:
    def log_is_newer_than(evidence_timestamp: Any) -> bool:
        return (
            bool(latest_log_mode)
            and latest_log_created_at is not None
            and evidence_timestamp is not None
            and latest_log_created_at > evidence_timestamp
        )

    normalized_telemetry_mode = str(telemetry_mode or "").strip().lower()
    if normalized_telemetry_mode == "manual":
        if log_is_newer_than(telemetry_timestamp):
            return {"value": latest_log_mode, "source": "control_log", "state": "live"}
        return {"value": "手动", "source": "telemetry", "state": "live"}
    if normalized_telemetry_mode == "auto":
        if log_is_newer_than(telemetry_timestamp):
            return {"value": latest_log_mode, "source": "control_log", "state": "live"}
        return {"value": "自动", "source": "telemetry", "state": "live"}

    normalized_profile_mode = str(profile_mode or "").strip().lower()
    if normalized_profile_mode in {"manual", "手动"}:
        if log_is_newer_than(profile_timestamp):
            return {"value": latest_log_mode, "source": "control_log", "state": "live"}
        return {"value": "手动", "source": "profile", "state": "live"}
    if normalized_profile_mode in {"auto", "自动"}:
        if log_is_newer_than(profile_timestamp):
            return {"value": latest_log_mode, "source": "control_log", "state": "live"}
        return {"value": "自动", "source": "profile", "state": "live"}

    normalized_profile_scheme = str(profile_scheme or "").strip()
    if "手动" in normalized_profile_scheme:
        if log_is_newer_than(profile_timestamp):
            return {"value": latest_log_mode, "source": "control_log", "state": "live"}
        return {"value": "手动", "source": "profile", "state": "live"}
    if "自动" in normalized_profile_scheme:
        if log_is_newer_than(profile_timestamp):
            return {"value": latest_log_mode, "source": "control_log", "state": "live"}
        return {"value": "自动", "source": "profile", "state": "live"}

    if latest_log_mode:
        return {"value": latest_log_mode, "source": "control_log", "state": "live"}

    return {
        "value": "自动" if is_device_active else "待确认",
        "source": "placeholder",
        "state": "mock",
    }
