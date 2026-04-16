import json

from pathlib import Path

import scripts.python.windows_device_stack.mqtt_gateway as mqtt_gateway
from scripts.python.windows_device_stack.common import to_gateway_payload
from scripts.python.windows_device_stack.mqtt_gateway import (
    PublishMeasurementResult,
    publish_measurement,
    publish_measurement_result,
)


class _FakePublishInfo:
    def __init__(self, published: bool):
        self._published = published
        self.wait_timeout = None

    def wait_for_publish(self, timeout=None):
        self.wait_timeout = timeout

    def is_published(self):
        return self._published


class _FakeClient:
    def __init__(self, published: bool):
        self.published = []
        self._published = published

    def publish(self, topic, payload, qos=0):
        self.published.append((topic, payload, qos))
        return _FakePublishInfo(self._published)


def _measurement():
    return {
        "device_code": "CAP-001",
        "timestamp": "2026-04-16T10:30:00+00:00",
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


def test_publish_measurement_uses_existing_platform_topic_and_ingest_payload():
    client = _FakeClient(published=True)
    measurement = _measurement()

    result = publish_measurement(client, measurement)

    assert result is True
    assert len(client.published) == 1
    topic, payload, qos = client.published[0]
    assert topic == "campus/telemetry"
    assert qos == 1
    assert json.loads(payload) == to_gateway_payload(measurement)


def test_publish_measurement_result_returns_success_details_with_custom_publish_settings():
    client = _FakeClient(published=True)

    result = publish_measurement_result(
        client,
        _measurement(),
        qos=2,
        wait_timeout=7.5,
    )

    assert isinstance(result, PublishMeasurementResult)
    assert result.success is True
    assert result.failure_class is None
    assert result.topic == "campus/telemetry"
    assert result.qos == 2
    assert result.wait_timeout == 7.5
    assert len(client.published) == 1
    topic, payload, qos = client.published[0]
    assert topic == "campus/telemetry"
    assert qos == 2
    assert json.loads(payload) == to_gateway_payload(_measurement())


def test_publish_measurement_returns_false_when_publish_does_not_complete_successfully():
    client = _FakeClient(published=False)

    result = publish_measurement(client, _measurement())

    assert result is False
    assert len(client.published) == 1


def test_publish_measurement_returns_false_when_payload_conversion_fails(monkeypatch):
    client = _FakeClient(published=True)

    def _boom(_measurement):
        raise RuntimeError("conversion failed")

    monkeypatch.setattr(mqtt_gateway, "to_gateway_payload", _boom)

    result = publish_measurement(client, _measurement())

    assert result is False
    assert client.published == []


def test_publish_measurement_returns_false_when_json_serialization_fails(monkeypatch):
    client = _FakeClient(published=True)

    def _boom(*_args, **_kwargs):
        raise TypeError("serialization failed")

    monkeypatch.setattr(mqtt_gateway.json, "dumps", _boom)

    result = publish_measurement(client, _measurement())

    assert result is False
    assert client.published == []


def test_publish_measurement_result_marks_conversion_failure_class(monkeypatch):
    client = _FakeClient(published=True)

    def _boom(_measurement):
        raise RuntimeError("conversion failed")

    monkeypatch.setattr(mqtt_gateway, "to_gateway_payload", _boom)

    result = publish_measurement_result(client, _measurement())

    assert result.success is False
    assert result.failure_class == "payload_conversion_error"
    assert result.payload is None
    assert client.published == []


def test_publish_measurement_result_marks_serialization_failure_class(monkeypatch):
    client = _FakeClient(published=True)

    def _boom(*_args, **_kwargs):
        raise TypeError("serialization failed")

    monkeypatch.setattr(mqtt_gateway.json, "dumps", _boom)

    result = publish_measurement_result(client, _measurement())

    assert result.success is False
    assert result.failure_class == "payload_serialization_error"
    assert result.payload is None
    assert client.published == []


def test_config_example_contains_simulator_collector_and_gateway_sections():
    config_path = Path("scripts/python/windows_device_stack/config.example.json")
    data = json.loads(config_path.read_text(encoding="utf-8"))

    assert set(data.keys()) == {"simulator", "collector", "gateway"}

    assert data["simulator"]["device_code"] == "CAP-001"
    assert data["simulator"]["serial_port"].startswith("COM")
    assert data["simulator"]["baudrate"] == 9600
    assert data["simulator"]["interval_seconds"] == 3
    assert data["simulator"]["profile"] == "normal"

    assert data["collector"]["serial_port"].startswith("COM")
    assert data["collector"]["baudrate"] == 9600
    assert data["collector"]["timeout_seconds"] == 1
    assert data["collector"]["cache_file"].endswith(".jsonl")

    assert data["gateway"]["network_mode"] == "wifi"
    assert data["gateway"]["transport"] == "mqtt"
    assert data["gateway"]["mqtt_topic"] == "campus/telemetry"
    assert data["gateway"]["queue_file"].endswith(".jsonl")
