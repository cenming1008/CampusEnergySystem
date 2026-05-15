from __future__ import annotations

import json

from app.integrations.mqtt.processor import (
    apply_field_aliases,
    extract_capacitor_bank_telemetry,
    normalize_compensation_measurements,
)
from scripts.python.send_capacitor_bank_harmonic_uat_payloads import (
    build_harmonic_uat_payloads,
    iter_publish_messages,
)


def test_builds_harmonic_uat_payloads_for_acceptance_scenarios():
    payloads = build_harmonic_uat_payloads(timestamp="2026-05-15T14:44:21+08:00")

    assert set(payloads) == {
        "a_phase_voltage_5th_over_threshold",
        "b_phase_current_missing",
        "legacy_cap001_without_spectrum",
        "invalid_spectrum_items_ignored",
    }

    over_limit = payloads["a_phase_voltage_5th_over_threshold"]
    assert over_limit["device_code"] == "CAP-001"
    assert over_limit["device_category"] == "compensation"
    assert over_limit["device_subtype"] == "capacitor_bank_controller"
    assert over_limit["voltage_harmonic_threshold"] == 5.0
    assert {"order": 5, "value": 6.4} in over_limit["voltage_harmonics_a"]
    assert len(over_limit["voltage_harmonics_a"]) == 30

    missing_current_b = payloads["b_phase_current_missing"]
    assert "current_harmonics_a" in missing_current_b
    assert "current_harmonics_b" not in missing_current_b

    legacy = payloads["legacy_cap001_without_spectrum"]
    assert "voltage_harmonics_a" not in legacy
    assert "current_harmonics_a" not in legacy
    assert legacy["voltage_thd_a"] == 2.4
    assert legacy["current_harmonic_a"] == 1.0


def test_publish_messages_use_device_telemetry_topic_and_json_payload():
    payloads = build_harmonic_uat_payloads(timestamp="2026-05-15T14:44:21+08:00")

    messages = list(iter_publish_messages(payloads))

    assert len(messages) == 4
    topic, payload_json = messages[0]
    assert topic == "campus/device/CAP-001/telemetry"
    decoded = json.loads(payload_json)
    assert decoded["device_code"] == "CAP-001"
    assert decoded["timestamp"] == "2026-05-15T14:44:21+08:00"


def test_uat_payloads_match_ingestion_sanitization_contract():
    payloads = build_harmonic_uat_payloads(timestamp="2026-05-15T14:44:21+08:00")

    over_limit = normalize_compensation_measurements(
        apply_field_aliases(payloads["a_phase_voltage_5th_over_threshold"])
    )
    over_limit_telemetry = extract_capacitor_bank_telemetry(over_limit)
    assert over_limit_telemetry is not None
    assert {"order": 5, "value": 6.4} in over_limit_telemetry["voltage_harmonics_a"]
    assert len(over_limit_telemetry["voltage_harmonics_a"]) == 30

    missing_current_b = normalize_compensation_measurements(
        apply_field_aliases(payloads["b_phase_current_missing"])
    )
    missing_telemetry = extract_capacitor_bank_telemetry(missing_current_b)
    assert missing_telemetry is not None
    assert "current_harmonics_a" in missing_telemetry
    assert "current_harmonics_b" not in missing_telemetry

    invalid = normalize_compensation_measurements(
        apply_field_aliases(payloads["invalid_spectrum_items_ignored"])
    )
    invalid_telemetry = extract_capacitor_bank_telemetry(invalid)
    assert invalid_telemetry is not None
    assert invalid_telemetry["voltage_harmonics_a"] == [{"order": 5, "value": 6.4}]
    assert invalid_telemetry["current_harmonics_a"] == [
        {"order": 3, "value": 0.8},
        {"order": 11, "value": 2.1},
    ]
