# Windows RS485 Device Stack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows-friendly three-process RS485 simulation stack that sends device frames through an edge collector and MQTT gateway into the existing platform ingest pipeline.

**Architecture:** Add an isolated `scripts/python/windows_device_stack/` module with focused files for shared protocol helpers, a serial frame simulator, a resilient edge collector, and an MQTT gateway. Keep the simulator unaware of MQTT, keep the collector unaware of platform-specific payload mapping, and keep the gateway unaware of raw RS485 framing so each layer can be replaced independently later.

**Tech Stack:** Python 3.10+, `pyserial`, `paho-mqtt`, `pytest`, JSONL queue files, existing CampusEnergySystem MQTT ingest contract

---

## File Structure

- Create: `scripts/python/windows_device_stack/__init__.py`
- Create: `scripts/python/windows_device_stack/common.py`
- Create: `scripts/python/windows_device_stack/rs485_device_simulator.py`
- Create: `scripts/python/windows_device_stack/edge_collector.py`
- Create: `scripts/python/windows_device_stack/mqtt_gateway.py`
- Create: `scripts/python/windows_device_stack/config.example.json`
- Create: `scripts/python/windows_device_stack/README.md`
- Create: `tests/test_windows_device_stack_common.py`
- Create: `tests/test_windows_device_stack_collector.py`
- Create: `tests/test_windows_device_stack_gateway.py`

### Responsibilities

- `common.py`: frame encoding/decoding, checksum, config loading, unified JSON model, MQTT payload mapping
- `rs485_device_simulator.py`: generate deterministic telemetry profiles and write framed messages to a serial port
- `edge_collector.py`: read serial frames, validate/checksum/parse, reconnect, and append normalized records to a JSONL queue
- `mqtt_gateway.py`: read queue records, convert them to platform MQTT payloads, publish with retry, and preserve unsent messages
- `config.example.json`: Windows-friendly runtime defaults for simulator/collector/gateway
- `README.md`: setup, dependency install, virtual COM pairing, and run commands

### Contract Decisions Locked By This Plan

- Raw frame format:
  - `<device_code|timestamp|voltage|current|power|reactive_power|power_factor|temperature|scene|CRC>`
- Collector output JSON schema:
  - `device_code`, `timestamp`, `source`, `transport`, `metrics`, `meta`, `raw`
- Gateway publish topic:
  - `campus/telemetry`
- Gateway payload fields:
  - `device_code`, `timestamp`, `voltage`, `current`, `power`, `reactive_power`, `power_factor`, `temperature`

### Test Scope

- Unit tests for checksum and frame parsing
- Unit tests for collector normalization and queue append behavior
- Unit tests for gateway payload mapping and queue preservation on publish failure

## Task 1: Shared Protocol Helpers

**Files:**
- Create: `scripts/python/windows_device_stack/__init__.py`
- Create: `scripts/python/windows_device_stack/common.py`
- Test: `tests/test_windows_device_stack_common.py`

- [ ] **Step 1: Write the failing tests**

```python
from scripts.python.windows_device_stack.common import (
    build_frame,
    calculate_checksum,
    parse_frame,
    to_gateway_payload,
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
    assert parsed["transport"] == "rs485"
    assert parsed["metrics"]["reactive_power"] == -2.3
    assert parsed["metrics"]["power_factor"] == 0.95
    assert parsed["raw"]["crc_ok"] is True


def test_parse_frame_rejects_invalid_checksum():
    frame = "<CAP-001|2026-04-16T10:30:00|221.4|12.8|4.6|-2.3|0.95|35.2|normal|FFFF>"

    try:
        parse_frame(frame, port="COM6", baudrate=9600)
    except ValueError as exc:
        assert "checksum" in str(exc).lower()
    else:
        raise AssertionError("expected checksum validation to fail")


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_windows_device_stack_common.py -v`
Expected: FAIL with `ModuleNotFoundError` for `scripts.python.windows_device_stack.common`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/python/windows_device_stack/common.py
from __future__ import annotations

from dataclasses import dataclass


FIELD_NAMES = (
    "device_code",
    "timestamp",
    "voltage",
    "current",
    "power",
    "reactive_power",
    "power_factor",
    "temperature",
    "scene",
)


def calculate_checksum(payload: str) -> str:
    checksum = 0
    for char in payload.encode("utf-8"):
        checksum = (checksum + char) & 0xFFFF
    return f"{checksum:04X}"


def build_frame(
    *,
    device_code: str,
    timestamp: str,
    voltage: float,
    current: float,
    power: float,
    reactive_power: float,
    power_factor: float,
    temperature: float,
    scene: str,
) -> str:
    body = "|".join(
        [
            device_code,
            timestamp,
            str(voltage),
            str(current),
            str(power),
            str(reactive_power),
            str(power_factor),
            str(temperature),
            scene,
        ]
    )
    return f"<{body}|{calculate_checksum(body)}>"


def parse_frame(frame: str, *, port: str, baudrate: int) -> dict:
    if not frame.startswith("<") or not frame.endswith(">"):
        raise ValueError("frame markers missing")

    body_with_checksum = frame[1:-1]
    parts = body_with_checksum.split("|")
    if len(parts) != 10:
        raise ValueError("frame field count invalid")

    body = "|".join(parts[:-1])
    expected_checksum = calculate_checksum(body)
    if parts[-1] != expected_checksum:
        raise ValueError("checksum validation failed")

    parsed = dict(zip(FIELD_NAMES, parts[:-1], strict=True))
    return {
        "device_code": parsed["device_code"],
        "timestamp": parsed["timestamp"],
        "source": "rs485_collector",
        "transport": "rs485",
        "metrics": {
            "voltage": float(parsed["voltage"]),
            "current": float(parsed["current"]),
            "power": float(parsed["power"]),
            "reactive_power": float(parsed["reactive_power"]),
            "power_factor": float(parsed["power_factor"]),
            "temperature": float(parsed["temperature"]),
        },
        "meta": {
            "scene": parsed["scene"],
            "port": port,
            "baudrate": baudrate,
        },
        "raw": {
            "frame": frame,
            "crc_ok": True,
        },
    }


def to_gateway_payload(measurement: dict) -> dict:
    metrics = measurement["metrics"]
    return {
        "device_code": measurement["device_code"],
        "timestamp": measurement["timestamp"],
        "voltage": metrics["voltage"],
        "current": metrics["current"],
        "power": metrics["power"],
        "reactive_power": metrics["reactive_power"],
        "power_factor": metrics["power_factor"],
        "temperature": metrics["temperature"],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_windows_device_stack_common.py -v`
Expected: PASS with 4 passing tests

- [ ] **Step 5: Commit**

```bash
git add tests/test_windows_device_stack_common.py scripts/python/windows_device_stack/__init__.py scripts/python/windows_device_stack/common.py
git commit -m "feat: add windows rs485 protocol helpers"
```

## Task 2: RS485 Simulator

**Files:**
- Modify: `scripts/python/windows_device_stack/common.py`
- Create: `scripts/python/windows_device_stack/rs485_device_simulator.py`
- Test: `tests/test_windows_device_stack_common.py`

- [ ] **Step 1: Write the failing test**

```python
from scripts.python.windows_device_stack.rs485_device_simulator import build_measurement


def test_build_measurement_generates_expected_profile_fields():
    measurement = build_measurement(device_code="CAP-001", profile="normal", tick=0)

    assert measurement["device_code"] == "CAP-001"
    assert measurement["scene"] == "normal"
    assert "timestamp" in measurement
    assert measurement["voltage"] > 0
    assert measurement["current"] > 0
    assert "reactive_power" in measurement
    assert "power_factor" in measurement
    assert "temperature" in measurement
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_windows_device_stack_common.py::test_build_measurement_generates_expected_profile_fields -v`
Expected: FAIL with `ModuleNotFoundError` for `rs485_device_simulator`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/python/windows_device_stack/rs485_device_simulator.py
from __future__ import annotations

from datetime import datetime
from math import sin, pi

from scripts.python.windows_device_stack.common import build_frame


def build_measurement(*, device_code: str, profile: str, tick: int) -> dict:
    phase = sin((tick % 60) / 60 * 2 * pi)
    voltage = round(221.0 + phase * 1.5, 2)
    current = round(12.0 + phase * 0.8, 2)
    power = round(4.5 + phase * 0.3, 2)
    reactive_power = round(-2.0 - phase * 0.4, 2)
    power_factor = round(min(0.999, max(0.8, abs(power) / ((power ** 2 + reactive_power ** 2) ** 0.5))), 3)
    temperature = round(35.0 + phase * 1.2, 2)

    if profile == "overtemp":
        temperature = 56.0
    elif profile == "harmonic":
        reactive_power = -3.2

    return {
        "device_code": device_code,
        "timestamp": datetime.now().replace(microsecond=0).isoformat(),
        "voltage": voltage,
        "current": current,
        "power": power,
        "reactive_power": reactive_power,
        "power_factor": power_factor,
        "temperature": temperature,
        "scene": profile,
    }


def measurement_to_frame(measurement: dict) -> str:
    return build_frame(**measurement)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_windows_device_stack_common.py::test_build_measurement_generates_expected_profile_fields -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_windows_device_stack_common.py scripts/python/windows_device_stack/rs485_device_simulator.py scripts/python/windows_device_stack/common.py
git commit -m "feat: add windows rs485 simulator"
```

## Task 3: Edge Collector Queueing And Recovery

**Files:**
- Modify: `scripts/python/windows_device_stack/common.py`
- Create: `scripts/python/windows_device_stack/edge_collector.py`
- Test: `tests/test_windows_device_stack_collector.py`

- [ ] **Step 1: Write the failing tests**

```python
import json

from scripts.python.windows_device_stack.common import build_frame
from scripts.python.windows_device_stack.edge_collector import (
    append_measurement_to_queue,
    collect_frame,
)


def test_collect_frame_parses_serial_frame_into_unified_measurement():
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

    measurement = collect_frame(frame, port="COM6", baudrate=9600)

    assert measurement["device_code"] == "CAP-001"
    assert measurement["metrics"]["temperature"] == 35.2


def test_append_measurement_to_queue_writes_jsonl_record(tmp_path):
    queue_file = tmp_path / "collector_queue.jsonl"
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

    append_measurement_to_queue(measurement, queue_file)

    saved = queue_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(saved) == 1
    assert json.loads(saved[0])["device_code"] == "CAP-001"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_windows_device_stack_collector.py -v`
Expected: FAIL with `ModuleNotFoundError` for `edge_collector`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/python/windows_device_stack/edge_collector.py
from __future__ import annotations

import json
from pathlib import Path

from scripts.python.windows_device_stack.common import parse_frame


def collect_frame(frame: str, *, port: str, baudrate: int) -> dict:
    return parse_frame(frame, port=port, baudrate=baudrate)


def append_measurement_to_queue(measurement: dict, queue_file: str | Path) -> None:
    queue_path = Path(queue_file)
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(measurement, ensure_ascii=False) + "\n")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_windows_device_stack_collector.py -v`
Expected: PASS with 2 passing tests

- [ ] **Step 5: Commit**

```bash
git add tests/test_windows_device_stack_collector.py scripts/python/windows_device_stack/edge_collector.py scripts/python/windows_device_stack/common.py
git commit -m "feat: add windows edge collector queue flow"
```

## Task 4: MQTT Gateway Publishing

**Files:**
- Modify: `scripts/python/windows_device_stack/common.py`
- Create: `scripts/python/windows_device_stack/mqtt_gateway.py`
- Test: `tests/test_windows_device_stack_gateway.py`

- [ ] **Step 1: Write the failing tests**

```python
from scripts.python.windows_device_stack.mqtt_gateway import publish_measurement


class FakeResult:
    def __init__(self, published: bool):
        self._published = published

    def wait_for_publish(self, timeout: float) -> None:
        return None

    def is_published(self) -> bool:
        return self._published


class FakeClient:
    def __init__(self, published: bool = True):
        self.published = published
        self.calls = []

    def publish(self, topic: str, payload: str, qos: int = 1):
        self.calls.append((topic, payload, qos))
        return FakeResult(self.published)


def test_publish_measurement_uses_existing_platform_topic():
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
    client = FakeClient()

    ok = publish_measurement(client, measurement, topic="campus/telemetry")

    assert ok is True
    assert client.calls[0][0] == "campus/telemetry"
    assert '"device_code": "CAP-001"' in client.calls[0][1]


def test_publish_measurement_returns_false_when_publish_fails():
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
    client = FakeClient(published=False)

    ok = publish_measurement(client, measurement, topic="campus/telemetry")

    assert ok is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_windows_device_stack_gateway.py -v`
Expected: FAIL with `ModuleNotFoundError` for `mqtt_gateway`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/python/windows_device_stack/mqtt_gateway.py
from __future__ import annotations

import json

from scripts.python.windows_device_stack.common import to_gateway_payload


def publish_measurement(client, measurement: dict, *, topic: str) -> bool:
    payload = to_gateway_payload(measurement)
    result = client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1)
    result.wait_for_publish(timeout=5)
    return bool(result.is_published())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_windows_device_stack_gateway.py -v`
Expected: PASS with 2 passing tests

- [ ] **Step 5: Commit**

```bash
git add tests/test_windows_device_stack_gateway.py scripts/python/windows_device_stack/mqtt_gateway.py scripts/python/windows_device_stack/common.py
git commit -m "feat: add windows mqtt gateway publisher"
```

## Task 5: Runtime Config And Windows Documentation

**Files:**
- Create: `scripts/python/windows_device_stack/config.example.json`
- Create: `scripts/python/windows_device_stack/README.md`
- Modify: `scripts/python/windows_device_stack/rs485_device_simulator.py`
- Modify: `scripts/python/windows_device_stack/edge_collector.py`
- Modify: `scripts/python/windows_device_stack/mqtt_gateway.py`

- [ ] **Step 1: Write the failing test**

```python
import json
from pathlib import Path


def test_config_example_contains_simulator_collector_and_gateway_sections():
    config_path = Path("scripts/python/windows_device_stack/config.example.json")
    data = json.loads(config_path.read_text(encoding="utf-8"))

    assert set(data.keys()) == {"simulator", "collector", "gateway"}
    assert data["simulator"]["serial_port"].startswith("COM")
    assert data["collector"]["cache_file"].endswith(".jsonl")
    assert data["gateway"]["mqtt_topic"] == "campus/telemetry"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_windows_device_stack_gateway.py::test_config_example_contains_simulator_collector_and_gateway_sections -v`
Expected: FAIL with `FileNotFoundError` for `config.example.json`

- [ ] **Step 3: Write minimal implementation**

```json
{
  "simulator": {
    "device_code": "CAP-001",
    "serial_port": "COM5",
    "baudrate": 9600,
    "interval_seconds": 3,
    "profile": "normal"
  },
  "collector": {
    "serial_port": "COM6",
    "baudrate": 9600,
    "timeout_seconds": 1,
    "cache_file": "./runtime/collector_queue.jsonl"
  },
  "gateway": {
    "network_mode": "wifi",
    "transport": "mqtt",
    "mqtt_broker": "127.0.0.1",
    "mqtt_port": 1883,
    "mqtt_username": "campus_mqtt",
    "mqtt_password": "campus_mqtt_secret_2026",
    "mqtt_topic": "campus/telemetry",
    "queue_file": "./runtime/collector_queue.jsonl"
  }
}
```

```md
# Windows Device Stack

## Install

```bash
pip install pyserial paho-mqtt
```

## Prepare Virtual COM Ports

Create a paired virtual serial port such as `COM5 <-> COM6`.

## Run

```bash
python scripts/python/windows_device_stack/rs485_device_simulator.py --config scripts/python/windows_device_stack/config.example.json
python scripts/python/windows_device_stack/edge_collector.py --config scripts/python/windows_device_stack/config.example.json
python scripts/python/windows_device_stack/mqtt_gateway.py --config scripts/python/windows_device_stack/config.example.json
```

## Verify

- Collector queue file receives JSONL lines
- Gateway publishes to `campus/telemetry`
- Platform worker ingests `device_code`, `reactive_power`, `power_factor`, `temperature`
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_windows_device_stack_gateway.py::test_config_example_contains_simulator_collector_and_gateway_sections -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/python/windows_device_stack/config.example.json scripts/python/windows_device_stack/README.md tests/test_windows_device_stack_gateway.py scripts/python/windows_device_stack/rs485_device_simulator.py scripts/python/windows_device_stack/edge_collector.py scripts/python/windows_device_stack/mqtt_gateway.py
git commit -m "docs: add windows device stack runtime config"
```

## Task 6: Final Verification

**Files:**
- Verify: `tests/test_windows_device_stack_common.py`
- Verify: `tests/test_windows_device_stack_collector.py`
- Verify: `tests/test_windows_device_stack_gateway.py`
- Verify: `scripts/python/windows_device_stack/README.md`

- [ ] **Step 1: Run the full new test suite**

Run: `pytest tests/test_windows_device_stack_common.py tests/test_windows_device_stack_collector.py tests/test_windows_device_stack_gateway.py -v`
Expected: PASS with all new tests green

- [ ] **Step 2: Run one existing MQTT contract check**

Run: `pytest tests/test_mqtt_contracts.py tests/test_mqtt_processor.py -q`
Expected: PASS, confirming the new gateway payload contract does not conflict with existing ingest assumptions

- [ ] **Step 3: Smoke-check docs and config paths**

Run: `python -m json.tool scripts/python/windows_device_stack/config.example.json`
Expected: Pretty-printed JSON with simulator/collector/gateway sections

- [ ] **Step 4: Manual Windows runbook review**

Check:
- `README.md` uses Windows-friendly `COM` examples
- runtime queue path stays under `scripts/python/windows_device_stack/` or a sibling `runtime/`
- only RS485 is a live input path
- GPRS remains configuration-only, not a fake implemented transport

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-04-16-windows-rs485-device-stack.md
git commit -m "chore: add windows rs485 device stack implementation plan"
```

## Self-Review

### Spec Coverage

- Three-process architecture: covered by Tasks 2, 3, 4
- RS485 frame contract: covered by Task 1
- Collector reconnect/queue boundary: collector queue contract covered by Task 3; runtime reconnect loop belongs in the implementation details when executing Task 3
- MQTT-only formal uplink: covered by Tasks 4 and 5
- Windows docs/config and virtual COM usage: covered by Task 5
- Existing platform ingest compatibility: covered by Tasks 1, 4, and 6

### Placeholder Scan

- No `TBD`, `TODO`, or “similar to Task N” placeholders remain
- Each task includes file paths, tests, commands, and concrete code snippets

### Type Consistency

- Unified measurement shape is reused consistently across Tasks 1, 3, and 4
- Gateway payload fields match the current ingest-friendly field names already recognized by `app/integrations/mqtt/processor.py`
