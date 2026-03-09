#!/usr/bin/env python3
"""
向 MQTT 发送测试 JSON，用于调试「设备 → MQTT → 后端」整条链路。

用法：
  # 发送一条，触发即插即用（自动创建设备）
  python scripts/python/mqtt_send_test.py

  # 指定 device_code、可选名称和类型
  python scripts/python/mqtt_send_test.py --code METER002 --name "2号电表" --type load

  # 指定 broker 和端口
  MQTT_BROKER=192.168.1.10 MQTT_PORT=1883 python scripts/python/mqtt_send_test.py
"""
import argparse
import json
import os
import time
from typing import Optional

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("请先安装: pip install paho-mqtt")
    raise SystemExit(1)

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "mine/telemetry")


def send_one(
    device_code: str = "TEST_DEVICE_001",
    device_name: Optional[str] = None,
    device_type: str = "load",
    voltage: float = 220.0,
    current: float = 5.0,
    power: Optional[float] = None,
    energy: float = 100.0,
) -> bool:
    payload = {
        "device_code": device_code,
        "timestamp": time.time(),
        "voltage": voltage,
        "current": current,
        "energy": energy,
    }
    if power is not None:
        payload["power"] = power
    else:
        payload["power"] = voltage * current / 1000.0
    if device_name:
        payload["device_name"] = device_name
    if device_type:
        payload["device_type"] = device_type

    client = mqtt.Client()
    try:
        client.connect(BROKER, PORT, 60)
        msg = json.dumps(payload)
        client.publish(TOPIC, msg)
        print(f"✅ 已发送到 {BROKER}:{PORT} 主题 {TOPIC}")
        print(f"   内容: {msg}")
        return True
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False
    finally:
        client.disconnect()


def main():
    ap = argparse.ArgumentParser(description="向 MQTT 发送一条测试遥测 JSON")
    ap.add_argument("--code", default="TEST_DEVICE_001", help="device_code（设备序列号）")
    ap.add_argument("--name", default=None, help="设备名称（即插即用时使用）")
    ap.add_argument("--type", default="load", help="设备类型 load/water_meter 等")
    ap.add_argument("--voltage", type=float, default=220, help="电压")
    ap.add_argument("--current", type=float, default=5, help="电流")
    ap.add_argument("--energy", type=float, default=100, help="累计电量")
    ap.add_argument("--loop", type=int, default=0, help="连续发送次数，0=只发一条")
    args = ap.parse_args()

    if args.loop <= 0:
        send_one(
            device_code=args.code,
            device_name=args.name,
            device_type=args.type,
            voltage=args.voltage,
            current=args.current,
            energy=args.energy,
        )
        return

    for i in range(args.loop):
        send_one(
            device_code=args.code,
            device_name=args.name,
            device_type=args.type,
            voltage=args.voltage,
            current=args.current,
            energy=args.energy,
        )
        if i < args.loop - 1:
            time.sleep(1)
    print(f"共发送 {args.loop} 条")


if __name__ == "__main__":
    main()
