"""MQTT gateway helpers for the Windows RS485 device stack."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.python.windows_device_stack.common import (
    load_runtime_config,
    read_cursor,
    to_gateway_payload,
    write_cursor,
)

DEFAULT_TOPIC = "campus/telemetry"


@dataclass(frozen=True)
class PublishMeasurementResult:
    """Structured outcome for publishing a unified measurement."""

    success: bool
    failure_class: str | None = None
    failure_message: str | None = None
    topic: str = DEFAULT_TOPIC
    qos: int = 1
    wait_timeout: float = 5.0
    payload: str | None = None


@dataclass(frozen=True)
class GatewayStepResult:
    """Per-record gateway publish outcome."""

    measurement: Dict[str, Any]
    publish_result: PublishMeasurementResult


def publish_measurement_result(
    client: Any,
    measurement: Dict[str, Any],
    topic: str = DEFAULT_TOPIC,
    *,
    qos: int = 1,
    wait_timeout: float = 5.0,
) -> PublishMeasurementResult:
    """Publish a unified measurement and return a structured outcome."""
    try:
        payload = to_gateway_payload(measurement)
    except Exception as exc:
        return PublishMeasurementResult(
            success=False,
            failure_class="payload_conversion_error",
            failure_message=str(exc),
            topic=topic,
            qos=qos,
            wait_timeout=wait_timeout,
        )

    try:
        payload_json = json.dumps(payload, ensure_ascii=False)
    except Exception as exc:
        return PublishMeasurementResult(
            success=False,
            failure_class="payload_serialization_error",
            failure_message=str(exc),
            topic=topic,
            qos=qos,
            wait_timeout=wait_timeout,
        )

    try:
        publish_info = client.publish(topic, payload_json, qos=qos)
    except Exception as exc:
        return PublishMeasurementResult(
            success=False,
            failure_class="publish_error",
            failure_message=str(exc),
            topic=topic,
            qos=qos,
            wait_timeout=wait_timeout,
            payload=payload_json,
        )

    try:
        publish_info.wait_for_publish(timeout=wait_timeout)
        if not publish_info.is_published():
            return PublishMeasurementResult(
                success=False,
                failure_class="publish_incomplete",
                topic=topic,
                qos=qos,
                wait_timeout=wait_timeout,
                payload=payload_json,
            )
    except Exception as exc:
        return PublishMeasurementResult(
            success=False,
            failure_class="publish_error",
            failure_message=str(exc),
            topic=topic,
            qos=qos,
            wait_timeout=wait_timeout,
            payload=payload_json,
        )

    return PublishMeasurementResult(
        success=True,
        topic=topic,
        qos=qos,
        wait_timeout=wait_timeout,
        payload=payload_json,
    )


def publish_measurement(
    client: Any,
    measurement: Dict[str, Any],
    topic: str = DEFAULT_TOPIC,
    *,
    qos: int = 1,
    wait_timeout: float = 5.0,
) -> bool:
    """Compatibility wrapper that preserves the Task 4 bool contract."""
    return publish_measurement_result(
        client,
        measurement,
        topic=topic,
        qos=qos,
        wait_timeout=wait_timeout,
    ).success


def open_mqtt_client(config: Dict[str, Any]) -> Any:
    """Create and connect an MQTT client using the runtime config."""
    from paho.mqtt import client as mqtt_client

    client = mqtt_client.Client()
    username = config.get("mqtt_username")
    password = config.get("mqtt_password")
    if username is not None:
        client.username_pw_set(username, password=password)
    client.connect(config["mqtt_broker"], int(config.get("mqtt_port", 1883)))
    return client


def _is_retryable_mqtt_error(exc: Exception) -> bool:
    """Return whether a connection/publish runtime error should trigger retry."""
    return isinstance(exc, OSError)


def run_gateway_step(client: Any, config: Dict[str, Any]) -> list[GatewayStepResult]:
    """Publish all new queue records since the last cursor position."""
    queue_file = Path(config["queue_file"])
    if not queue_file.exists():
        return []

    cursor_file = config.get("cursor_file")
    offset = read_cursor(cursor_file) if cursor_file else 0
    results: list[GatewayStepResult] = []
    topic = config.get("mqtt_topic", DEFAULT_TOPIC)
    qos = int(config.get("mqtt_qos", 1))
    wait_timeout = float(config.get("wait_timeout", 5.0))

    with queue_file.open("r", encoding="utf-8") as handle:
        handle.seek(offset)
        while True:
            line_start = handle.tell()
            line = handle.readline()
            if not line:
                break
            if not line.strip():
                offset = handle.tell()
                continue

            measurement = json.loads(line)
            publish_result = publish_measurement_result(
                client,
                measurement,
                topic,
                qos=qos,
                wait_timeout=wait_timeout,
            )
            results.append(
                GatewayStepResult(
                    measurement=measurement,
                    publish_result=publish_result,
                )
            )
            if not publish_result.success:
                offset = line_start
                break

            offset = handle.tell()

    if cursor_file is not None:
        write_cursor(cursor_file, offset)

    return results


def run_runtime(config: Dict[str, Any], *, client_factory: Any = None, sleep_func: Any = None) -> None:
    """Run the gateway loop until interrupted."""
    client_factory = client_factory or open_mqtt_client
    sleep_func = sleep_func or time.sleep
    poll_interval_seconds = float(config.get("poll_interval_seconds", 1.0))
    retry_interval_seconds = float(config.get("retry_interval_seconds", 1.0))

    while True:
        client = None
        loop_started = False
        try:
            client = client_factory(config)
            if hasattr(client, "loop_start"):
                client.loop_start()
                loop_started = True

            while True:
                run_gateway_step(client, config)
                sleep_func(poll_interval_seconds)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            if not _is_retryable_mqtt_error(exc):
                raise
            sleep_func(retry_interval_seconds)
        finally:
            if loop_started and hasattr(client, "loop_stop"):
                client.loop_stop()
            if client is not None and hasattr(client, "disconnect"):
                client.disconnect()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Windows RS485 MQTT gateway.")
    parser.add_argument("--config", required=True, help="Path to the JSON runtime config.")
    args = parser.parse_args(argv)

    config = load_runtime_config(args.config)["gateway"]
    try:
        run_runtime(config)
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
