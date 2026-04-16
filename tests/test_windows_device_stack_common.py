from scripts.python.windows_device_stack.common import (
    build_frame,
    parse_frame,
    to_gateway_payload,
)
from scripts.python.windows_device_stack.rs485_device_simulator import (
    build_measurement,
    measurement_to_frame,
)


def test_build_frame_appends_checksum_and_markers():
    frame = build_frame(
        device_code="CAP-001",
        timestamp="2026-04-16T10:30:00",
        voltage=221.4,
        current=12.8,
        power=4.6,
        reactive_power=-2.3,
        power_factor=0.95,
        temperature=35.2,
        scene="normal",
    )

    assert frame.startswith("<")
    assert frame.endswith(">")
    assert "CAP-001" in frame
    assert frame.count("|") == 9


def test_parse_frame_returns_unified_measurement_fields():
    frame = build_frame(
        device_code="CAP-001",
        timestamp="2026-04-16T10:30:00",
        voltage=221.4,
        current=12.8,
        power=4.6,
        reactive_power=-2.3,
        power_factor=0.95,
        temperature=35.2,
        scene="normal",
    )

    parsed = parse_frame(frame, port="COM6", baudrate=9600)

    assert parsed["device_code"] == "CAP-001"
    assert parsed["timestamp"] == "2026-04-16T10:30:00"
    assert parsed["source"] == "rs485_collector"
    assert parsed["transport"] == "rs485"
    assert parsed["metrics"]["voltage"] == 221.4
    assert parsed["metrics"]["current"] == 12.8
    assert parsed["metrics"]["power"] == 4.6
    assert parsed["metrics"]["reactive_power"] == -2.3
    assert parsed["metrics"]["power_factor"] == 0.95
    assert parsed["metrics"]["temperature"] == 35.2
    assert parsed["meta"] == {"scene": "normal", "port": "COM6", "baudrate": 9600}
    assert parsed["raw"]["frame"] == frame
    assert parsed["raw"]["crc_ok"] is True


def test_parse_frame_rejects_invalid_checksum():
    frame = "<CAP-001|2026-04-16T10:30:00|221.4|12.8|4.6|-2.3|0.95|35.2|normal|FFFF>"

    try:
        parse_frame(frame, port="COM6", baudrate=9600)
    except ValueError as exc:
        assert "checksum" in str(exc).lower()
    else:
        raise AssertionError("expected checksum validation to fail")


def test_parse_frame_rejects_non_finite_numeric_values():
    frame = build_frame(
        device_code="CAP-001",
        timestamp="2026-04-16T10:30:00",
        voltage=float("nan"),
        current=12.8,
        power=4.6,
        reactive_power=-2.3,
        power_factor=0.95,
        temperature=35.2,
        scene="normal",
    )

    try:
        parse_frame(frame, port="COM6", baudrate=9600)
    except ValueError as exc:
        assert "non-finite" in str(exc).lower()
    else:
        raise AssertionError("expected non-finite numeric validation to fail")


def test_build_frame_rejects_pipe_in_device_code():
    try:
        build_frame(
            device_code="CAP|001",
            timestamp="2026-04-16T10:30:00",
            voltage=221.4,
            current=12.8,
            power=4.6,
            reactive_power=-2.3,
            power_factor=0.95,
            temperature=35.2,
            scene="normal",
        )
    except ValueError as exc:
        assert "device_code" in str(exc)
    else:
        raise AssertionError("expected delimiter validation to fail")


def test_build_frame_rejects_pipe_in_scene():
    try:
        build_frame(
            device_code="CAP-001",
            timestamp="2026-04-16T10:30:00",
            voltage=221.4,
            current=12.8,
            power=4.6,
            reactive_power=-2.3,
            power_factor=0.95,
            temperature=35.2,
            scene="nor|mal",
        )
    except ValueError as exc:
        assert "scene" in str(exc)
    else:
        raise AssertionError("expected delimiter validation to fail")


def test_to_gateway_payload_flattens_metrics_for_existing_ingest_contract():
    measurement = {
        "device_code": "CAP-001",
        "timestamp": "2026-04-16T10:30:00",
        "source": "rs485_collector",
        "transport": "rs485",
        "metrics": {
            "voltage": 221.4,
            "current": 12.8,
            "power": 4.6,
            "reactive_power": -2.3,
            "power_factor": 0.95,
            "temperature": 35.2,
        },
        "meta": {"scene": "normal", "port": "COM6", "baudrate": 9600},
        "raw": {"frame": "<...>", "crc_ok": True},
    }

    payload = to_gateway_payload(measurement)

    assert payload == {
        "device_code": "CAP-001",
        "timestamp": "2026-04-16T10:30:00",
        "voltage": 221.4,
        "current": 12.8,
        "power": 4.6,
        "reactive_power": -2.3,
        "power_factor": 0.95,
        "temperature": 35.2,
    }


def test_build_measurement_generates_expected_profile_fields(monkeypatch):
    from datetime import datetime, timezone
    import scripts.python.windows_device_stack.rs485_device_simulator as simulator

    monkeypatch.setattr(
        simulator,
        "_current_timestamp",
        lambda: datetime(2026, 4, 16, 10, 30, tzinfo=timezone.utc),
    )

    measurement = build_measurement(device_code="CAP-001", profile="normal", tick=5)

    assert measurement["device_code"] == "CAP-001"
    assert measurement["scene"] == "normal"
    assert measurement["timestamp"] == "2026-04-16T10:30:00+00:00"
    assert measurement["voltage"] > 0
    assert measurement["current"] > 0
    assert "reactive_power" in measurement
    assert "power_factor" in measurement
    assert "temperature" in measurement


def test_build_measurement_supports_overtemp_profile(monkeypatch):
    from datetime import datetime, timezone
    import scripts.python.windows_device_stack.rs485_device_simulator as simulator

    monkeypatch.setattr(
        simulator,
        "_current_timestamp",
        lambda: datetime(2026, 4, 16, 10, 30, tzinfo=timezone.utc),
    )

    measurement = build_measurement(device_code="CAP-001", profile="overtemp", tick=0)

    assert measurement["scene"] == "overtemp"
    assert measurement["temperature"] > 50
    assert measurement["voltage"] > 0


def test_build_measurement_supports_harmonic_profile(monkeypatch):
    from datetime import datetime, timezone
    import scripts.python.windows_device_stack.rs485_device_simulator as simulator

    monkeypatch.setattr(
        simulator,
        "_current_timestamp",
        lambda: datetime(2026, 4, 16, 10, 30, tzinfo=timezone.utc),
    )

    measurement = build_measurement(device_code="CAP-001", profile="harmonic", tick=0)

    assert measurement["scene"] == "harmonic"
    assert measurement["reactive_power"] < 0
    assert measurement["power_factor"] < 0.95


def test_build_measurement_rejects_unsupported_profile(monkeypatch):
    from datetime import datetime, timezone
    import scripts.python.windows_device_stack.rs485_device_simulator as simulator

    monkeypatch.setattr(
        simulator,
        "_current_timestamp",
        lambda: datetime(2026, 4, 16, 10, 30, tzinfo=timezone.utc),
    )

    try:
        build_measurement(device_code="CAP-001", profile="bad-profile", tick=0)
    except ValueError as exc:
        assert "unsupported profile" in str(exc).lower()
    else:
        raise AssertionError("expected unsupported profile validation to fail")


def test_measurement_round_trip_through_frame_and_parser(monkeypatch):
    from datetime import datetime, timezone
    import scripts.python.windows_device_stack.rs485_device_simulator as simulator

    monkeypatch.setattr(
        simulator,
        "_current_timestamp",
        lambda: datetime(2026, 4, 16, 10, 30, tzinfo=timezone.utc),
    )

    measurement = build_measurement(device_code="CAP-001", profile="normal", tick=2)
    frame = measurement_to_frame(measurement)
    parsed = parse_frame(frame, port="COM6", baudrate=9600)
    payload = to_gateway_payload(parsed)

    assert parsed["device_code"] == measurement["device_code"]
    assert parsed["timestamp"] == measurement["timestamp"]
    assert parsed["meta"]["scene"] == measurement["scene"]
    assert parsed["raw"]["frame"] == frame
    assert payload == {
        "device_code": measurement["device_code"],
        "timestamp": measurement["timestamp"],
        "voltage": measurement["voltage"],
        "current": measurement["current"],
        "power": measurement["power"],
        "reactive_power": measurement["reactive_power"],
        "power_factor": measurement["power_factor"],
        "temperature": measurement["temperature"],
    }
