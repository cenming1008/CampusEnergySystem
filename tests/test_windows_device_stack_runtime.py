import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.python.windows_device_stack.common import build_frame


def test_load_runtime_config_resolves_relative_runtime_paths(tmp_path):
    from scripts.python.windows_device_stack.common import load_runtime_config

    runtime_dir = tmp_path / "runtime"
    config_path = tmp_path / "windows-device-config.json"
    config_path.write_text(
        json.dumps(
            {
                "simulator": {
                    "device_code": "CAP-001",
                    "serial_port": "COM5",
                    "baudrate": 9600,
                    "interval_seconds": 3,
                    "profile": "normal",
                },
                "collector": {
                    "serial_port": "COM6",
                    "baudrate": 9600,
                    "timeout_seconds": 1,
                    "cache_file": "./runtime/collector_queue.jsonl",
                },
                "gateway": {
                    "transport": "mqtt",
                    "mqtt_broker": "127.0.0.1",
                    "mqtt_port": 1883,
                    "mqtt_topic": "campus/telemetry",
                    "queue_file": "./runtime/collector_queue.jsonl",
                    "cursor_file": "./runtime/gateway.cursor",
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path)

    assert config["collector"]["cache_file"] == str(runtime_dir / "collector_queue.jsonl")
    assert config["gateway"]["queue_file"] == str(runtime_dir / "collector_queue.jsonl")
    assert config["gateway"]["cursor_file"] == str(runtime_dir / "gateway.cursor")


def test_simulator_runtime_step_writes_frame_to_serial_handle(monkeypatch):
    import scripts.python.windows_device_stack.rs485_device_simulator as simulator

    measurement = {
        "device_code": "CAP-001",
        "timestamp": "2026-04-16T10:30:00+00:00",
        "voltage": 221.4,
        "current": 12.8,
        "power": 4.6,
        "reactive_power": -2.3,
        "power_factor": 0.95,
        "temperature": 35.2,
        "scene": "normal",
    }

    class FakeSerial:
        def __init__(self):
            self.writes = []

        def write(self, payload):
            self.writes.append(payload)
            return len(payload)

    serial_handle = FakeSerial()
    monkeypatch.setattr(simulator, "build_measurement", lambda **kwargs: measurement)

    result = simulator.run_simulator_step(
        serial_handle,
        {"device_code": "CAP-001", "profile": "normal"},
        tick=7,
    )

    expected_frame = simulator.measurement_to_frame(measurement).encode("utf-8")
    assert serial_handle.writes == [expected_frame]
    assert result["measurement"] == measurement
    assert result["frame"] == expected_frame.decode("utf-8")
    assert result["bytes_written"] == len(expected_frame)


def test_simulator_runtime_uses_current_time_without_tick_timestamp_drift(monkeypatch):
    from datetime import datetime, timezone

    import scripts.python.windows_device_stack.rs485_device_simulator as simulator

    timestamps = iter(
        [
            datetime(2026, 4, 16, 10, 30, 0, tzinfo=timezone.utc),
            datetime(2026, 4, 16, 10, 30, 3, tzinfo=timezone.utc),
        ]
    )
    writes = []
    class Done(BaseException):
        pass

    class FakeSerial:
        def write(self, payload):
            writes.append(payload.decode("utf-8"))
            if len(writes) >= 2:
                raise Done("stop runtime loop")
            return len(payload)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(simulator, "_current_timestamp", lambda: next(timestamps))
    monkeypatch.setattr(simulator, "open_serial_port", lambda _config: FakeSerial())

    with pytest.raises(Done):
        simulator.run_runtime(
            {"device_code": "CAP-001", "profile": "normal", "interval_seconds": 3},
            sleep_func=lambda _seconds: None,
        )

    assert "|2026-04-16T10:30:00+00:00|" in writes[0]
    assert "|2026-04-16T10:30:03+00:00|" in writes[1]


def test_collector_runtime_step_reads_frame_and_appends_queue_record(tmp_path):
    import scripts.python.windows_device_stack.edge_collector as edge_collector

    frame = build_frame(
        device_code="CAP-001",
        timestamp="2026-04-16T10:30:00+00:00",
        voltage=221.4,
        current=12.8,
        power=4.6,
        reactive_power=-2.3,
        power_factor=0.95,
        temperature=35.2,
        scene="normal",
    )

    class FakeSerial:
        def __init__(self, payload):
            self.payload = payload
            self.index = 0

        def read(self, size=1):
            if self.index >= len(self.payload):
                return b""
            chunk = self.payload[self.index : self.index + size]
            self.index += size
            return chunk

    queue_file = tmp_path / "collector_queue.jsonl"
    serial_handle = FakeSerial(frame.encode("utf-8"))

    result = edge_collector.run_collector_step(
        serial_handle,
        {
            "serial_port": "COM6",
            "baudrate": 9600,
            "cache_file": str(queue_file),
        },
    )

    saved = json.loads(queue_file.read_text(encoding="utf-8").strip())
    assert result == saved
    assert saved["device_code"] == "CAP-001"
    assert saved["meta"]["port"] == "COM6"
    assert saved["raw"]["frame"] == frame


def test_gateway_runtime_step_reads_queue_and_publishes_only_new_records(tmp_path, monkeypatch):
    import scripts.python.windows_device_stack.mqtt_gateway as mqtt_gateway

    queue_file = tmp_path / "collector_queue.jsonl"
    cursor_file = tmp_path / "gateway.cursor"
    measurements = [
        {
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
        },
        {
            "device_code": "CAP-002",
            "timestamp": "2026-04-16T10:30:03+00:00",
            "source": "rs485_collector",
            "transport": "rs485",
            "metrics": {
                "voltage": 222.1,
                "current": 12.5,
                "power": 4.4,
                "reactive_power": -2.1,
                "power_factor": 0.96,
                "temperature": 35.0,
            },
            "meta": {"scene": "normal", "port": "COM6", "baudrate": 9600},
            "raw": {"frame": "<...>", "crc_ok": True},
        },
    ]
    queue_file.write_text(
        "".join(json.dumps(item) + "\n" for item in measurements),
        encoding="utf-8",
    )

    class FakeClient:
        pass

    published = []

    def fake_publish_measurement_result(client, measurement, topic, *, qos, wait_timeout):
        published.append((client, measurement, topic, qos, wait_timeout))
        return mqtt_gateway.PublishMeasurementResult(
            success=True,
            topic=topic,
            qos=qos,
            wait_timeout=wait_timeout,
            payload=json.dumps({"device_code": measurement["device_code"]}),
        )

    client = FakeClient()
    config = {
        "queue_file": str(queue_file),
        "cursor_file": str(cursor_file),
        "mqtt_topic": "campus/telemetry",
        "mqtt_qos": 1,
        "wait_timeout": 5.0,
    }
    monkeypatch.setattr(
        mqtt_gateway,
        "publish_measurement_result",
        fake_publish_measurement_result,
    )

    first_results = mqtt_gateway.run_gateway_step(client, config)
    second_results = mqtt_gateway.run_gateway_step(client, config)

    assert [item.measurement["device_code"] for item in first_results] == ["CAP-001", "CAP-002"]
    assert second_results == []
    assert [item[1]["device_code"] for item in published] == ["CAP-001", "CAP-002"]
    assert cursor_file.exists()


def test_collector_runtime_retries_after_open_failure(monkeypatch):
    import scripts.python.windows_device_stack.edge_collector as edge_collector

    events = []
    attempts = {"count": 0}
    class Done(BaseException):
        pass

    class FakeSerial:
        def __enter__(self):
            events.append("serial_opened")
            return self

        def __exit__(self, exc_type, exc, tb):
            events.append("serial_closed")
            return False

    def fake_serial_factory(_config):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise OSError("port unavailable")
        return FakeSerial()

    def fake_run_step(_serial_handle, _config, *, buffer=None):
        events.append("step")
        raise Done("stop runtime loop")

    monkeypatch.setattr(edge_collector, "run_collector_step", fake_run_step)

    with pytest.raises(Done):
        edge_collector.run_runtime(
            {"serial_port": "COM6", "baudrate": 9600, "cache_file": "queue.jsonl"},
            serial_factory=fake_serial_factory,
            sleep_func=lambda _seconds: events.append("sleep"),
        )

    assert attempts["count"] == 2
    assert events == ["sleep", "serial_opened", "step", "serial_closed"]


def test_gateway_runtime_retries_after_transient_runtime_failure(monkeypatch):
    import scripts.python.windows_device_stack.mqtt_gateway as mqtt_gateway

    events = []
    attempts = {"count": 0}
    class Done(BaseException):
        pass

    class FakeClient:
        def loop_start(self):
            events.append("loop_start")

        def loop_stop(self):
            events.append("loop_stop")

        def disconnect(self):
            events.append("disconnect")

    def fake_client_factory(_config):
        attempts["count"] += 1
        events.append(f"connect_{attempts['count']}")
        return FakeClient()

    def fake_run_step(_client, _config):
        events.append(f"step_{attempts['count']}")
        if attempts["count"] == 1:
            raise OSError("broker unavailable")
        raise Done("stop runtime loop")

    monkeypatch.setattr(mqtt_gateway, "run_gateway_step", fake_run_step)

    with pytest.raises(Done):
        mqtt_gateway.run_runtime(
            {"mqtt_broker": "127.0.0.1", "mqtt_port": 1883, "queue_file": "queue.jsonl"},
            client_factory=fake_client_factory,
            sleep_func=lambda _seconds: events.append("sleep"),
        )

    assert attempts["count"] == 2
    assert events == [
        "connect_1",
        "loop_start",
        "step_1",
        "sleep",
        "loop_stop",
        "disconnect",
        "connect_2",
        "loop_start",
        "step_2",
        "loop_stop",
        "disconnect",
    ]


def test_windows_device_stack_scripts_support_direct_help_invocation():
    repo_root = Path(__file__).resolve().parent.parent
    script_dir = repo_root / "scripts/python/windows_device_stack"

    for script_name in (
        "rs485_device_simulator.py",
        "edge_collector.py",
        "mqtt_gateway.py",
    ):
        result = subprocess.run(
            [sys.executable, str(script_dir / script_name), "--help"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        assert "--config" in result.stdout
