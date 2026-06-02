from app.domain.compensation_rules import (
    build_pq_reference_line,
    clamp_health_score,
    comm_health_score,
    health_rating,
    max_defined_number,
    normalize_power_factor,
    score_by_threshold,
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
