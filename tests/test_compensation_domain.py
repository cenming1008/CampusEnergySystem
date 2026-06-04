from datetime import datetime, timedelta

from app.domain import compensation_rules
from app.domain.compensation_rules import (
    build_svg_monitor_payload_parts,
    build_pq_reference_line,
    clamp_health_score,
    comm_health_score,
    health_rating,
    max_defined_number,
    normalize_power_factor,
    score_by_threshold,
    resolve_capacitor_bank_control_log_mode,
    resolve_svg_control_mode,
    switching_health_score,
    voltage_stability_score,
)


def test_normalize_power_factor_accepts_percent_and_ratio_values():
    assert normalize_power_factor(95) == 0.95
    assert normalize_power_factor(0.92) == 0.92
    assert normalize_power_factor("98") == 0.98
    assert normalize_power_factor(0) is None
    assert normalize_power_factor("bad") is None


def test_build_pq_reference_line_preserves_existing_payload_shape():
    assert build_pq_reference_line(0.9, role="threshold") == {
        "powerFactor": 0.9,
        "label": "PF 0.90",
        "role": "threshold",
    }


def test_health_score_primitives_preserve_monitor_threshold_behavior():
    assert clamp_health_score(99.6) == 100
    assert clamp_health_score(-4) == 0
    assert score_by_threshold(2.5, 5.0) == 90
    assert score_by_threshold(6.0, 5.0) == 72
    assert score_by_threshold(None, 5.0) == 0
    assert max_defined_number((None, 3.2, 5.1, None)) == 5.1
    assert max_defined_number((None, None)) is None


def test_health_status_primitives_preserve_monitor_payload_values():
    assert comm_health_score("online", True) == 100
    assert comm_health_score("online", False) == 70
    assert comm_health_score("degraded", True) == 55
    assert comm_health_score("offline", True) == 15
    assert comm_health_score(None, True) == 0
    assert voltage_stability_score(220.0) == 100
    assert voltage_stability_score(None) == 0
    assert switching_health_score((True, False, None)) == 82
    assert switching_health_score((None, None)) == 0
    assert health_rating(92) == {"rating": "优秀", "ratingTone": "success"}
    assert health_rating(55) == {"rating": "关注", "ratingTone": "warning"}
    assert health_rating(15) == {"rating": "异常", "ratingTone": "danger"}


def test_build_capacitor_bank_circuit_summary_prefers_telemetry_count():
    summary = compensation_rules.build_capacitor_bank_circuit_summary(
        telemetry_running_count=6,
        telemetry_bitmasks=(None, None, None, None, None, None),
        explicit_total_counts=(None, None, None, None, None, None),
        configured_output_counts=(18, 6),
        profile_running_count=None,
        profile_running_values=(None, None, None, None, None, None),
    )

    assert summary == {
        "running_count": 6,
        "total_count": 24,
        "has_realtime_state": True,
        "source": "telemetry",
        "state": "live",
    }


def test_build_capacitor_bank_circuit_summary_counts_bitmask_and_profile_fallbacks():
    bitmask_summary = compensation_rules.build_capacitor_bank_circuit_summary(
        telemetry_running_count=None,
        telemetry_bitmasks=(0b1011, None, 0b1000, None, None, None),
        explicit_total_counts=(4, 4, 4, None, None, None),
        configured_output_counts=(0, 0),
        profile_running_count=None,
        profile_running_values=(None, None, None, None, None, None),
    )
    profile_summary = compensation_rules.build_capacitor_bank_circuit_summary(
        telemetry_running_count=None,
        telemetry_bitmasks=(None, None, None, None, None, None),
        explicit_total_counts=(None, None, None, None, None, None),
        configured_output_counts=(18, 6),
        profile_running_count=None,
        profile_running_values=(3, 2, None, 1, None, None),
    )
    fallback_summary = compensation_rules.build_capacitor_bank_circuit_summary(
        telemetry_running_count=None,
        telemetry_bitmasks=(None, None, None, None, None, None),
        explicit_total_counts=(None, None, None, None, None, None),
        configured_output_counts=(0, 0),
        profile_running_count=None,
        profile_running_values=(None, None, None, None, None, None),
    )

    assert bitmask_summary["running_count"] == 4
    assert bitmask_summary["total_count"] == 12
    assert bitmask_summary["source"] == "telemetry"
    assert profile_summary == {
        "running_count": 6,
        "total_count": 24,
        "has_realtime_state": True,
        "source": "profile",
        "state": "live",
    }
    assert fallback_summary == {
        "running_count": 0,
        "total_count": 24,
        "has_realtime_state": False,
        "source": "configured_fallback",
        "state": "mock",
    }


def test_build_capacitor_bank_temperature_health_preserves_alarm_and_missing_states():
    assert compensation_rules.build_capacitor_bank_temperature_health(
        temp_alarm=True,
        threshold=55.0,
        cabinet_temperature=42.0,
        warning_margin=3.0,
    ) == {"value": "温度告警", "source": "telemetry", "state": "live"}
    assert compensation_rules.build_capacitor_bank_temperature_health(
        temp_alarm=None,
        threshold=55.0,
        cabinet_temperature=None,
        warning_margin=3.0,
    ) == {"value": "待判断", "source": "missing", "state": "missing"}
    assert compensation_rules.build_capacitor_bank_temperature_health(
        temp_alarm=False,
        threshold=None,
        cabinet_temperature=42.0,
        warning_margin=3.0,
    ) == {"value": "正常", "source": "telemetry", "state": "live"}


def test_build_capacitor_bank_temperature_health_uses_threshold_and_warning_margin():
    assert compensation_rules.build_capacitor_bank_temperature_health(
        temp_alarm=False,
        threshold=55.0,
        cabinet_temperature=56.0,
        warning_margin=3.0,
    ) == {"value": "超过上限", "source": "profile", "state": "live"}
    assert compensation_rules.build_capacitor_bank_temperature_health(
        temp_alarm=False,
        threshold=55.0,
        cabinet_temperature=54.0,
        warning_margin=3.0,
    ) == {"value": "接近上限", "source": "profile", "state": "live"}
    assert compensation_rules.build_capacitor_bank_temperature_health(
        temp_alarm=False,
        threshold=55.0,
        cabinet_temperature=54.0,
        warning_margin=0.5,
    ) == {"value": "正常", "source": "profile", "state": "live"}


def test_resolve_capacitor_bank_control_mode_prefers_newer_control_log_over_telemetry():
    telemetry_timestamp = datetime(2026, 6, 2, 10, 0, 0)
    control_log_timestamp = telemetry_timestamp + timedelta(minutes=2)

    assert compensation_rules.resolve_capacitor_bank_control_mode(
        telemetry_mode="auto",
        telemetry_timestamp=telemetry_timestamp,
        profile_mode=None,
        profile_scheme=None,
        profile_timestamp=None,
        latest_log_mode="手动",
        latest_log_created_at=control_log_timestamp,
        is_device_active=True,
    ) == {"value": "手动", "source": "control_log", "state": "live"}


def test_resolve_capacitor_bank_control_mode_uses_profile_then_placeholder():
    profile_timestamp = datetime(2026, 6, 2, 10, 0, 0)

    assert compensation_rules.resolve_capacitor_bank_control_mode(
        telemetry_mode=None,
        telemetry_timestamp=None,
        profile_mode="manual",
        profile_scheme=None,
        profile_timestamp=profile_timestamp,
        latest_log_mode="自动",
        latest_log_created_at=profile_timestamp - timedelta(minutes=1),
        is_device_active=True,
    ) == {"value": "手动", "source": "profile", "state": "live"}

    assert compensation_rules.resolve_capacitor_bank_control_mode(
        telemetry_mode=None,
        telemetry_timestamp=None,
        profile_mode=None,
        profile_scheme=None,
        profile_timestamp=None,
        latest_log_mode="",
        latest_log_created_at=None,
        is_device_active=False,
    ) == {"value": "待确认", "source": "placeholder", "state": "mock"}


def test_resolve_capacitor_bank_control_log_mode_accepts_only_successful_mode_logs():
    assert resolve_capacitor_bank_control_log_mode(
        normalized_result="success",
        action="manual_switch",
        reason="控制台控制模式切换 -> 自动模式 | 设备回执已处理: 已切回自动模式",
    ) == "自动"
    assert resolve_capacitor_bank_control_log_mode(
        normalized_result="success",
        action="switch_control_mode",
        reason="控制台控制模式切换 -> 手动模式",
    ) == "手动"
    assert resolve_capacitor_bank_control_log_mode(
        normalized_result="failed",
        action="manual_switch",
        reason="控制台控制模式切换 -> 自动模式",
    ) == ""
    assert resolve_capacitor_bank_control_log_mode(
        normalized_result="success",
        action="manual_switch_test",
        reason="控制台控制模式切换 -> 自动模式",
    ) == ""
    assert resolve_capacitor_bank_control_log_mode(
        normalized_result="success",
        action="manual_switch",
        reason="手动投切回执",
    ) == ""


def test_resolve_svg_control_mode_preserves_telemetry_and_placeholder_payloads():
    assert resolve_svg_control_mode(True) == {"value": "自动", "source": "telemetry", "state": "live"}
    assert resolve_svg_control_mode(False) == {"value": "手动", "source": "telemetry", "state": "live"}
    assert resolve_svg_control_mode(None) == {"value": "待确认", "source": "placeholder", "state": "mock"}


def test_build_svg_monitor_payload_parts_uses_telemetry_and_profile_counts():
    parts = build_svg_monitor_payload_parts(
        capacity_utilization=40.0,
        profile_module_count=10,
        rated_capacity=150.0,
        reactive_power=30.0,
        cabinet_temperature=36.5,
        realtime_temperature=32.0,
    )

    assert parts["capacity_utilization_metric"] == {
        "value": 40.0,
        "source": "telemetry",
        "state": "live",
    }
    assert parts["circuit_summary"] == {
        "running_count": 4,
        "total_count": 10,
        "has_realtime_state": True,
        "source": "telemetry",
        "state": "live",
    }
    assert parts["compensation_level_metric"] == {
        "value": 4,
        "source": "telemetry",
        "state": "live",
    }
    assert parts["cabinet_temperature_metric"] == {
        "value": 36.5,
        "source": "telemetry",
        "state": "live",
    }


def test_build_svg_monitor_payload_parts_estimates_capacity_from_reactive_power():
    parts = build_svg_monitor_payload_parts(
        capacity_utilization=None,
        profile_module_count=8,
        rated_capacity=200.0,
        reactive_power=-50.0,
        cabinet_temperature=None,
        realtime_temperature=31.2,
    )

    assert parts["capacity_utilization_metric"] == {
        "value": 25.0,
        "source": "estimated",
        "state": "mock",
    }
    assert parts["circuit_summary"] == {
        "running_count": 2,
        "total_count": 8,
        "has_realtime_state": True,
        "source": "estimated",
        "state": "mock",
    }
    assert parts["cabinet_temperature_metric"] == {
        "value": 31.2,
        "source": "realtime",
        "state": "live",
    }


def test_build_svg_monitor_payload_parts_marks_missing_capacity_and_temperature():
    parts = build_svg_monitor_payload_parts(
        capacity_utilization=None,
        profile_module_count=0,
        rated_capacity=0.0,
        reactive_power=None,
        cabinet_temperature=None,
        realtime_temperature=None,
    )

    assert parts["capacity_utilization_metric"] == {
        "value": None,
        "source": "missing",
        "state": "missing",
    }
    assert parts["circuit_summary"] == {
        "running_count": None,
        "total_count": None,
        "has_realtime_state": False,
        "source": "missing",
        "state": "missing",
    }
    assert parts["compensation_level_metric"] == {
        "value": None,
        "source": "missing",
        "state": "missing",
    }
    assert parts["cabinet_temperature_metric"] == {
        "value": None,
        "source": "missing",
        "state": "missing",
    }
