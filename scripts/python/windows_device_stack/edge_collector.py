"""Edge collector helpers for the Windows RS485 device stack."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Any, Dict

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.python.windows_device_stack.common import load_runtime_config, parse_frame

try:  # pragma: no cover - import availability depends on platform
    import fcntl  # type: ignore
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]

try:  # pragma: no cover - import availability depends on platform
    import msvcrt  # type: ignore
except ImportError:  # pragma: no cover - POSIX
    msvcrt = None  # type: ignore[assignment]


_QUEUE_APPEND_LOCK = Lock()


def collect_frame(frame: str, port: str, baudrate: int) -> Dict[str, Any]:
    """Parse a raw RS485 frame into the unified measurement structure."""
    return parse_frame(frame, port=port, baudrate=baudrate)


@contextmanager
def _queue_file_lock(handle: Any):
    """Serialize queue writers across processes when the platform supports it."""
    if msvcrt is not None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return

    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return

    yield


def append_measurement_to_queue(measurement: Dict[str, Any], queue_file: Any) -> None:
    """Append a measurement record to a local JSONL queue file."""
    queue_path = Path(queue_file)
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(measurement) + "\n"
    with _QUEUE_APPEND_LOCK:
        with queue_path.open("a", encoding="utf-8") as handle:
            with _queue_file_lock(handle):
                handle.write(line)
                handle.flush()
                try:
                    os.fsync(handle.fileno())
                except (AttributeError, OSError, ValueError):
                    pass


def open_serial_port(config: Dict[str, Any]) -> Any:
    """Open the configured serial port on demand."""
    import serial

    return serial.Serial(
        port=config["serial_port"],
        baudrate=config["baudrate"],
        timeout=config.get("timeout_seconds", 1),
    )


def _is_retryable_serial_error(exc: Exception) -> bool:
    """Return whether a runtime/open error should trigger a serial retry."""
    return isinstance(exc, OSError) or exc.__class__.__name__ == "SerialException"


def _read_frame_from_serial(serial_handle: Any, *, buffer: bytearray | None = None) -> str | None:
    """Read until one complete frame is available or the port times out."""
    active_buffer = buffer if buffer is not None else bytearray()

    while True:
        chunk = serial_handle.read(1)
        if not chunk:
            return None

        byte = chunk[0]
        if byte == ord("<"):
            active_buffer.clear()
            active_buffer.append(byte)
            continue

        if not active_buffer:
            continue

        active_buffer.append(byte)
        if byte == ord(">"):
            frame = active_buffer.decode("utf-8")
            active_buffer.clear()
            return frame


def run_collector_step(
    serial_handle: Any,
    config: Dict[str, Any],
    *,
    buffer: bytearray | None = None,
) -> Dict[str, Any] | None:
    """Read one complete frame from serial and append it to the queue."""
    frame = _read_frame_from_serial(serial_handle, buffer=buffer)
    if frame is None:
        return None

    measurement = collect_frame(
        frame,
        port=config["serial_port"],
        baudrate=config["baudrate"],
    )
    append_measurement_to_queue(measurement, config["cache_file"])
    return measurement


def run_runtime(config: Dict[str, Any], *, serial_factory: Any = None, sleep_func: Any = None) -> None:
    """Run the collector loop until interrupted."""
    serial_factory = serial_factory or open_serial_port
    sleep_func = sleep_func or time.sleep
    idle_sleep_seconds = float(config.get("idle_sleep_seconds", 0.1))
    retry_interval_seconds = float(config.get("retry_interval_seconds", 1.0))
    buffer = bytearray()

    while True:
        try:
            with serial_factory(config) as serial_handle:
                while True:
                    measurement = run_collector_step(serial_handle, config, buffer=buffer)
                    if measurement is None:
                        sleep_func(idle_sleep_seconds)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            if not _is_retryable_serial_error(exc):
                raise
            buffer.clear()
            sleep_func(retry_interval_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Windows RS485 edge collector.")
    parser.add_argument("--config", required=True, help="Path to the JSON runtime config.")
    args = parser.parse_args(argv)

    config = load_runtime_config(args.config)["collector"]
    try:
        run_runtime(config)
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
