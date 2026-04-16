"""Shared protocol helpers for the Windows RS485 device stack."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict

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

_RUNTIME_PATH_FIELDS = {
    ("collector", "cache_file"),
    ("gateway", "queue_file"),
    ("gateway", "cursor_file"),
}


def _validate_text_field(field_name: str, value: str) -> None:
    if "|" in value:
        raise ValueError(f"{field_name} must not contain reserved delimiter '|'")


def _parse_finite_float(field_name: str, value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{field_name} must not be non-finite")
    return parsed


def calculate_checksum(payload: str) -> str:
    """Return the uppercase 16-bit checksum for a frame body."""
    checksum = 0
    for byte in payload.encode("utf-8"):
        checksum = (checksum + byte) & 0xFFFF
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
    """Build a raw RS485 frame with markers and checksum."""
    _validate_text_field("device_code", device_code)
    _validate_text_field("scene", scene)

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


def parse_frame(frame: str, *, port: str, baudrate: int) -> Dict[str, Any]:
    """Parse a raw frame into the unified measurement structure."""
    if not frame.startswith("<") or not frame.endswith(">"):
        raise ValueError("frame markers missing")

    body_with_checksum = frame[1:-1]
    parts = body_with_checksum.split("|")
    if len(parts) != len(FIELD_NAMES) + 1:
        raise ValueError("frame field count invalid")

    body = "|".join(parts[:-1])
    expected_checksum = calculate_checksum(body)
    received_checksum = parts[-1]
    if received_checksum != expected_checksum:
        raise ValueError("checksum validation failed")

    measurement = {
        "device_code": parts[0],
        "timestamp": parts[1],
        "source": "rs485_collector",
        "transport": "rs485",
        "metrics": {
            "voltage": _parse_finite_float("voltage", parts[2]),
            "current": _parse_finite_float("current", parts[3]),
            "power": _parse_finite_float("power", parts[4]),
            "reactive_power": _parse_finite_float("reactive_power", parts[5]),
            "power_factor": _parse_finite_float("power_factor", parts[6]),
            "temperature": _parse_finite_float("temperature", parts[7]),
        },
        "meta": {
            "scene": parts[8],
            "port": port,
            "baudrate": baudrate,
        },
        "raw": {
            "frame": frame,
            "crc_ok": True,
        },
    }
    return measurement


def to_gateway_payload(measurement: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a measurement into the existing ingest payload contract."""
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


def _resolve_runtime_path(base_dir: Path, value: str) -> str:
    candidate = Path(value)
    if candidate.is_absolute():
        return str(candidate)
    return str((base_dir / candidate).resolve())


def load_runtime_config(config_path: Any) -> Dict[str, Any]:
    """Load JSON config and resolve runtime file paths relative to the config."""
    config_file = Path(config_path)
    config = json.loads(config_file.read_text(encoding="utf-8"))
    base_dir = config_file.parent

    for section_name, field_name in _RUNTIME_PATH_FIELDS:
        section = config.get(section_name)
        if section is None:
            continue
        value = section.get(field_name)
        if not value:
            continue
        section[field_name] = _resolve_runtime_path(base_dir, value)

    gateway = config.setdefault("gateway", {})
    if gateway.get("queue_file") and not gateway.get("cursor_file"):
        gateway["cursor_file"] = f"{gateway['queue_file']}.cursor"

    return config


def read_cursor(cursor_file: Any) -> int:
    """Read a byte-offset cursor file, defaulting to zero."""
    path = Path(cursor_file)
    try:
        return max(0, int(path.read_text(encoding="utf-8").strip() or "0"))
    except (FileNotFoundError, ValueError):
        return 0


def write_cursor(cursor_file: Any, offset: int) -> None:
    """Persist a byte-offset cursor for queue draining."""
    path = Path(cursor_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(max(0, int(offset))), encoding="utf-8")
