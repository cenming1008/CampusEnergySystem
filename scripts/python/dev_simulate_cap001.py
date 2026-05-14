#!/usr/bin/env python3
"""
Dev 环境 CAP-001 模拟器：走 TLS + 独立凭据推 telemetry 到 broker。
用于验证 P0 安全加固（TLS + ACL + 一设备一密钥）后的链路是否通畅。

用法:
    python scripts/python/dev_simulate_cap001.py

读取环境变量（建议从 .env 加载）:
    MQTT_BROKER, MQTT_PORT, MQTT_TLS_CA_PATH, MQTT_TLS_INSECURE
    MQTT_DEVICE_CAP001_USERNAME, MQTT_DEVICE_CAP001_PASSWORD
"""

from __future__ import annotations

import json
import os
import random
import signal
import ssl
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_env() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def make_payload(seq: int) -> dict:
    base_pf = 0.92 + random.uniform(-0.01, 0.01)
    return {
        "device_code": "CAP-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "voltage_a": round(220 + random.uniform(-2, 2), 2),
        "voltage_b": round(220 + random.uniform(-2, 2), 2),
        "voltage_c": round(220 + random.uniform(-2, 2), 2),
        "current_a": round(90 + random.uniform(-5, 5), 2),
        "current_b": round(80 + random.uniform(-5, 5), 2),
        "current_c": round(83 + random.uniform(-5, 5), 2),
        "power_factor_a": round(base_pf, 4),
        "power_factor_b": round(base_pf + 0.03, 4),
        "power_factor_c": round(base_pf + 0.01, 4),
        "frequency": round(49.97 + random.uniform(-0.03, 0.03), 2),
        "temperature": round(41 + random.uniform(-1, 1), 1),
        "voltage": round(220 + random.uniform(-1, 1), 2),
        "current": round(84 + random.uniform(-2, 2), 2),
        "power": 58 + random.randint(-2, 2),
        "reactive_power": 23 + random.randint(-2, 2),
        "power_factor": round(base_pf, 4),
        "seq": seq,
    }


def main() -> int:
    load_env()

    broker = os.environ.get("MQTT_BROKER", "localhost")
    port = int(os.environ.get("MQTT_PORT", "1883"))
    tls_enabled = os.environ.get("MQTT_TLS_ENABLED", "False").lower() == "true"
    ca = os.environ.get("MQTT_TLS_CA_PATH")
    insecure = os.environ.get("MQTT_TLS_INSECURE", "False").lower() == "true"
    user = os.environ.get("MQTT_DEVICE_CAP001_USERNAME", "cap-001")
    pwd = os.environ.get("MQTT_DEVICE_CAP001_PASSWORD")
    topic = "campus/device/CAP-001/telemetry"

    if not pwd:
        print("❌ 缺少 MQTT_DEVICE_CAP001_PASSWORD", file=sys.stderr)
        return 2

    c = mqtt.Client(client_id="dev-sim-cap-001")
    c.username_pw_set(user, pwd)
    if tls_enabled:
        if not ca and not insecure:
            print("❌ MQTT_TLS_ENABLED=True 但缺少 MQTT_TLS_CA_PATH", file=sys.stderr)
            return 2
        c.tls_set(ca_certs=ca, tls_version=ssl.PROTOCOL_TLS_CLIENT)
        if insecure:
            c.tls_insecure_set(True)

    mode = "TLS" if tls_enabled else "plain"
    print(f"🔌 连接 {broker}:{port} ({mode}, user={user})")
    c.connect(broker, port, keepalive=60)
    c.loop_start()

    stopping = False

    def handle_sigint(_sig, _frm):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    seq = 0
    try:
        while not stopping:
            seq += 1
            payload = make_payload(seq)
            info = c.publish(topic, json.dumps(payload), qos=1)
            info.wait_for_publish(timeout=5)
            print(f"→ [{seq:04d}] {topic}  V={payload['voltage']} I={payload['current']} PF={payload['power_factor']}")
            time.sleep(5)
    finally:
        c.loop_stop()
        c.disconnect()
    print("👋 退出")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
