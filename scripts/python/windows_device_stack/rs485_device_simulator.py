"""Deterministic telemetry generator for the Windows RS485 simulator."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from math import pi, sin, sqrt
from pathlib import Path
from typing import Any, Dict

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.python.windows_device_stack.common import build_frame, load_runtime_config


def _current_timestamp() -> datetime:
    """Return the current simulator timestamp in UTC, rounded to seconds."""
    return datetime.now(timezone.utc).replace(microsecond=0)


def _profile_offset(profile: str, phase: float) -> Dict[str, float]:
    if profile == "normal":
        return {
            "voltage": 0.0,
            "current": 0.0,
            "power": 0.0,
            "reactive_power": 0.0,
            "power_factor": 0.0,
            "temperature": 0.0,
        }
    if profile == "overtemp":
        return {
            "voltage": 0.4,
            "current": 0.2,
            "power": 0.15,
            "reactive_power": 0.1,
            "power_factor": -0.01,
            "temperature": 18.0 + abs(phase) * 4.0,
        }
    if profile == "harmonic":
        return {
            "voltage": -0.3,
            "current": 0.5 + abs(phase) * 0.4,
            "power": -0.05,
            "reactive_power": -0.8 - abs(phase) * 0.6,
            "power_factor": -0.08,
            "temperature": 1.0,
        }
    raise ValueError(f"unsupported profile: {profile}")


def build_measurement(*, device_code: str, profile: str, tick: int) -> Dict[str, Any]:
    """Build a device-oriented measurement for the Windows RS485 simulator."""
    phase = sin((tick % 60) / 60.0 * 2.0 * pi)
    offsets = _profile_offset(profile, phase)

    voltage = round(220.5 + phase * 1.6 + offsets["voltage"], 2)
    current = round(11.8 + phase * 0.9 + offsets["current"], 2)
    power = round(4.4 + phase * 0.35 + offsets["power"], 2)
    reactive_power = round(-2.1 - phase * 0.45 + offsets["reactive_power"], 2)
    apparent_power = sqrt(power * power + reactive_power * reactive_power)
    if apparent_power == 0:
        power_factor = 0.0
    else:
        power_factor = round(max(0.0, min(0.999, abs(power) / apparent_power + offsets["power_factor"])), 3)
    temperature = round(34.5 + phase * 1.4 + offsets["temperature"], 2)

    timestamp = _current_timestamp().isoformat()

    return {
        "device_code": device_code,
        "timestamp": timestamp,
        "voltage": voltage,
        "current": current,
        "power": power,
        "reactive_power": reactive_power,
        "power_factor": power_factor,
        "temperature": temperature,
        "scene": profile,
    }


def measurement_to_frame(measurement: Dict[str, Any]) -> str:
    """Convert a simulator measurement into the shared RS485 frame format."""
    return build_frame(**measurement)


def open_serial_port(config: Dict[str, Any]) -> Any:
    """Open the configured serial port on demand."""
    import serial

    timeout = config.get("timeout_seconds", 1)
    return serial.Serial(
        port=config["serial_port"],
        baudrate=config["baudrate"],
        timeout=timeout,
        write_timeout=timeout,
    )


def run_simulator_step(serial_handle: Any, config: Dict[str, Any], *, tick: int) -> Dict[str, Any]:
    """Generate one measurement/frame pair and write it to the serial port."""
    measurement = build_measurement(
        device_code=config["device_code"],
        profile=config["profile"],
        tick=tick,
    )
    frame = measurement_to_frame(measurement)
    payload = frame.encode("utf-8")
    bytes_written = serial_handle.write(payload)
    return {
        "measurement": measurement,
        "frame": frame,
        "bytes_written": bytes_written,
    }


def run_runtime(config: Dict[str, Any], *, serial_factory: Any = None, sleep_func: Any = None) -> None:
    """Run the simulator loop until interrupted."""
    serial_factory = serial_factory or open_serial_port
    sleep_func = sleep_func or time.sleep
    interval_seconds = float(config.get("interval_seconds", 1))
    tick = 0
    with serial_factory(config) as serial_handle:
        while True:
            run_simulator_step(serial_handle, config, tick=tick)
            tick += 1
            sleep_func(interval_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Windows RS485 device simulator.")
    parser.add_argument("--config", required=True, help="Path to the JSON runtime config.")
    args = parser.parse_args(argv)

    config = load_runtime_config(args.config)["simulator"]
    try:
        run_runtime(config)
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
