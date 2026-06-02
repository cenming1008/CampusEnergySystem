from app.domain.compensation_rules import build_pq_reference_line, normalize_power_factor


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
