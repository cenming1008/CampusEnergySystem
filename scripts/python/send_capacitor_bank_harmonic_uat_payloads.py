#!/usr/bin/env python3
"""电容补偿控制器逐次谐波联调 payload 生成与发送工具。"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Iterable


def _spectrum(
    *,
    peak_order: int | None = None,
    peak_value: float | None = None,
    base_value: float = 0.6,
) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    for order in range(2, 32):
        value = round(base_value + (order % 4) * 0.12, 2)
        if order == peak_order and peak_value is not None:
            value = peak_value
        rows.append({"order": order, "value": value})
    return rows


def _base_payload(timestamp: str) -> dict[str, object]:
    return {
        "device_code": "CAP-001",
        "timestamp": timestamp,
        "device_category": "compensation",
        "device_subtype": "capacitor_bank_controller",
        "energy_type": "electricity",
        "voltage_a": 220.2,
        "voltage_b": 219.9,
        "voltage_c": 220.8,
        "current_a": 18.2,
        "current_b": 17.8,
        "current_c": 18.4,
        "power_factor_a": 0.96,
        "power_factor_b": 0.95,
        "power_factor_c": 0.96,
        "reactive_power_a": 3.2,
        "reactive_power_b": 3.1,
        "reactive_power_c": 3.3,
        "power": 11.8,
        "reactive_power": 9.6,
        "consumption": 0.0,
        "frequency": 50.0,
        "temperature": 39.5,
        "voltage_thd_a": 2.4,
        "voltage_thd_b": 2.2,
        "voltage_thd_c": 2.3,
        "current_harmonic_a": 1.0,
        "current_harmonic_b": 0.9,
        "current_harmonic_c": 1.1,
        "voltage_harmonic_threshold": 5.0,
        "current_harmonic_threshold": 2.5,
    }


def build_harmonic_uat_payloads(timestamp: str | None = None) -> dict[str, dict[str, object]]:
    """生成逐次谐波联调验收 payload。

    返回的四组 payload 分别覆盖：
    1. A 相 5 次电压谐波超过门限。
    2. B 相电流谱线缺失。
    3. 旧 CAP-001 payload 不带逐次谱线。
    4. 非法阶次 / 非数值项，供平台过滤校验。
    """
    ts = timestamp or datetime.now(timezone.utc).isoformat()

    over_limit = _base_payload(ts)
    over_limit.update(
        {
            "voltage_harmonics_a": _spectrum(peak_order=5, peak_value=6.4, base_value=0.7),
            "voltage_harmonics_b": _spectrum(base_value=0.5),
            "voltage_harmonics_c": _spectrum(base_value=0.55),
            "current_harmonics_a": _spectrum(base_value=0.35),
            "current_harmonics_b": _spectrum(base_value=0.4),
            "current_harmonics_c": _spectrum(base_value=0.42),
        }
    )

    missing_current_b = _base_payload(ts)
    missing_current_b.update(
        {
            "voltage_harmonics_a": _spectrum(base_value=0.45),
            "voltage_harmonics_b": _spectrum(base_value=0.43),
            "voltage_harmonics_c": _spectrum(base_value=0.44),
            "current_harmonics_a": _spectrum(base_value=0.3),
            "current_harmonics_c": _spectrum(base_value=0.32),
        }
    )

    legacy = _base_payload(ts)
    for key in (
        "voltage_harmonic_threshold",
        "current_harmonic_threshold",
    ):
        legacy.pop(key, None)

    invalid_items = _base_payload(ts)
    invalid_items.update(
        {
            "voltage_harmonics_a": [
                {"order": 1, "value": 9.9},
                {"order": 5, "value": 6.4},
                {"order": 32, "value": 8.8},
                {"order": 7, "value": "bad"},
            ],
            "current_harmonics_a": [
                {"order": 3, "value": 0.8},
                {"order": "11", "value": 2.1},
                {"order": 12, "value": "nan"},
            ],
        }
    )

    return {
        "a_phase_voltage_5th_over_threshold": over_limit,
        "b_phase_current_missing": missing_current_b,
        "legacy_cap001_without_spectrum": legacy,
        "invalid_spectrum_items_ignored": invalid_items,
    }


def iter_publish_messages(payloads: dict[str, dict[str, object]]) -> Iterable[tuple[str, str]]:
    for payload in payloads.values():
        device_code = str(payload["device_code"])
        topic = f"campus/device/{device_code}/telemetry"
        yield topic, json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _publish_messages(messages: Iterable[tuple[str, str]], *, broker: str, port: int) -> None:
    import paho.mqtt.client as mqtt

    client = mqtt.Client(client_id="cap-harmonic-uat")
    username = os.environ.get("MQTT_USERNAME")
    password = os.environ.get("MQTT_PASSWORD")
    if username:
        client.username_pw_set(username, password)

    client.connect(broker, port, keepalive=60)
    client.loop_start()
    try:
        for topic, payload_json in messages:
            info = client.publish(topic, payload_json, qos=1)
            info.wait_for_publish(timeout=5)
            print(f"published {topic} {payload_json}")
    finally:
        client.loop_stop()
        client.disconnect()


def main() -> int:
    parser = argparse.ArgumentParser(description="发送或打印电容补偿控制器逐次谐波联调 payload")
    parser.add_argument("--broker", default=os.environ.get("MQTT_BROKER", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("MQTT_PORT", "1883")))
    parser.add_argument("--timestamp", default=None)
    parser.add_argument("--print-only", action="store_true", help="只打印 topic 和 JSON payload，不连接 MQTT")
    args = parser.parse_args()

    payloads = build_harmonic_uat_payloads(timestamp=args.timestamp)
    messages = list(iter_publish_messages(payloads))
    if args.print_only:
        for topic, payload_json in messages:
            print(f"{topic} {payload_json}")
        return 0

    _publish_messages(messages, broker=args.broker, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
