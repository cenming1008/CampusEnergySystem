#!/usr/bin/env python3
"""
向指定电容补偿控制器发送模拟 MQTT 遥测数据。

发送内容同时覆盖：
  - 公共层字段：voltage/current/power/reactive_power/power_factor/temperature
  - 控制器专属字段：三相功率、电压 THD、谐波电流、状态位、投切状态

用法：
  # 查看当前系统中的电容补偿控制器列表
  python scripts/python/send_capacitor_bank_telemetry.py --list

  # 向 device_id=1 的设备发送一条 MQTT 数据
  python scripts/python/send_capacitor_bank_telemetry.py --id 1

  # 持续发送 30 条，每隔 5 秒一条
  python scripts/python/send_capacitor_bank_telemetry.py --id 1 --loop 30 --interval 5

  # 补发过去 2 小时的历史数据（每分钟一条，共 120 条）
  python scripts/python/send_capacitor_bank_telemetry.py --id 1 --backfill 120 --backfill-step 60
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("请先安装: pip install paho-mqtt")
    raise SystemExit(1)

from sqlmodel import Session, select

from app.core.database import engine
from app.core.settings import settings
from app.domain.device_payloads import resolve_compensation_subtype
from app.models.tables import Device

BROKER = os.getenv("MQTT_BROKER", settings.mqtt_broker)
PORT = int(os.getenv("MQTT_PORT", str(settings.mqtt_port)))
USERNAME = os.getenv("MQTT_USERNAME", settings.mqtt_username or "campus_mqtt")
PASSWORD = os.getenv("MQTT_PASSWORD", settings.mqtt_password or "campus_mqtt_secret_2026")
TOPIC = os.getenv("MQTT_TOPIC", settings.mqtt_topic)
BROKER_CONTAINER_CANDIDATES = (
    "campusenergysystem-mqtt-1",
    "campus_mqtt",
    "campus_mqtt_dev",
    "campus_mqtt_prod",
)


def _wave(base: float, amplitude: float, t: float, period: float = 60.0) -> float:
    return base + amplitude * math.sin(2 * math.pi * t / period) + random.uniform(-amplitude * 0.1, amplitude * 0.1)


def _build_mask(enabled: int, total: int = 8) -> int:
    enabled = max(0, min(total, enabled))
    return sum(1 << i for i in range(enabled))


def _build_payload(device: Device, timestamp: datetime, tick: int = 0) -> dict[str, Any]:
    t = float(tick)

    voltage_a = _wave(220.0, 2.6, t, 120)
    voltage_b = _wave(219.4, 2.8, t + 30, 120)
    voltage_c = _wave(220.6, 2.5, t + 60, 120)

    current_a = _wave(92.0, 16.0, t, 90)
    current_b = _wave(88.0, 15.0, t + 25, 90)
    current_c = _wave(95.0, 14.0, t + 50, 90)

    power_factor_a = min(0.999, max(0.88, _wave(0.972, 0.02, t, 90)))
    power_factor_b = min(0.999, max(0.88, _wave(0.968, 0.02, t + 15, 90)))
    power_factor_c = min(0.999, max(0.88, _wave(0.975, 0.02, t + 30, 90)))

    active_power_a = max(8.0, _wave(20.0, 4.0, t, 90))
    active_power_b = max(8.0, _wave(19.0, 4.0, t + 20, 90))
    active_power_c = max(8.0, _wave(21.0, 4.0, t + 40, 90))

    reactive_power_a = min(-2.0, _wave(-8.0, 2.2, t, 90))
    reactive_power_b = min(-2.0, _wave(-7.0, 2.0, t + 20, 90))
    reactive_power_c = min(-2.0, _wave(-9.0, 2.4, t + 40, 90))

    apparent_power_a = math.sqrt(active_power_a**2 + reactive_power_a**2)
    apparent_power_b = math.sqrt(active_power_b**2 + reactive_power_b**2)
    apparent_power_c = math.sqrt(active_power_c**2 + reactive_power_c**2)

    voltage_thd_a = max(1.0, _wave(2.8, 0.5, t, 180))
    voltage_thd_b = max(1.0, _wave(3.0, 0.4, t + 20, 180))
    voltage_thd_c = max(1.0, _wave(2.7, 0.5, t + 40, 180))
    current_harmonic_a = max(0.4, _wave(1.4, 0.35, t, 180))
    current_harmonic_b = max(0.4, _wave(1.3, 0.30, t + 15, 180))
    current_harmonic_c = max(0.4, _wave(1.5, 0.35, t + 30, 180))
    temperature = _wave(37.0, 5.0, t, 180)
    frequency = _wave(50.0, 0.03, t, 300)

    power = active_power_a + active_power_b + active_power_c
    reactive_power = reactive_power_a + reactive_power_b + reactive_power_c
    power_factor = (power_factor_a + power_factor_b + power_factor_c) / 3
    voltage = (voltage_a + voltage_b + voltage_c) / 3
    current = (current_a + current_b + current_c) / 3
    energy = round(max(0.0, power) * max(1, tick + 1) / 3600, 4)

    phase_a_groups = round(min(8, max(0, abs(reactive_power_a) / 1.25)))
    phase_b_groups = round(min(8, max(0, abs(reactive_power_b) / 1.25)))
    phase_c_groups = round(min(8, max(0, abs(reactive_power_c) / 1.25)))
    common_1_groups = round(min(8, max(0, (abs(reactive_power) - 18) / 1.5)))
    common_2_groups = 1 if max(voltage_thd_a, voltage_thd_b, voltage_thd_c) > 3.4 else 0
    common_3_groups = 1 if temperature > 42.0 else 0

    circuit_state_1 = (_build_mask(phase_a_groups) << 8) | _build_mask(phase_b_groups)
    circuit_state_2 = (_build_mask(phase_c_groups) << 8) | _build_mask(common_1_groups)
    circuit_state_3 = (_build_mask(common_2_groups) << 8) | _build_mask(common_3_groups)

    jkwf_status = 0
    if reactive_power_a < 0:
        jkwf_status |= 1 << 0
    if reactive_power_b < 0:
        jkwf_status |= 1 << 1
    if reactive_power_c < 0:
        jkwf_status |= 1 << 2
    if voltage_a > 231.0:
        jkwf_status |= 1 << 6
    if voltage_b > 231.0:
        jkwf_status |= 1 << 7
    if voltage_c > 231.0:
        jkwf_status |= 1 << 8
    if voltage_thd_a > 4.2:
        jkwf_status |= 1 << 9
    if voltage_thd_b > 4.2:
        jkwf_status |= 1 << 10
    if voltage_thd_c > 4.2:
        jkwf_status |= 1 << 11
    if current_harmonic_a > 2.6:
        jkwf_status |= 1 << 12
    if current_harmonic_b > 2.6:
        jkwf_status |= 1 << 13
    if current_harmonic_c > 2.6:
        jkwf_status |= 1 << 14
    if temperature > 52.0:
        jkwf_status |= 1 << 15

    payload = {
        "device_code": device.sn,
        "device_name": device.name,
        "device_type": "capacitor_bank_controller",
        "timestamp": timestamp.isoformat(),
        "voltage": round(voltage, 2),
        "current": round(current, 2),
        "power": round(power, 2),
        "energy": energy,
        "reactive_power": round(reactive_power, 2),
        "power_factor": round(power_factor, 4),
        "temperature": round(temperature, 1),
        "voltage_a": round(voltage_a, 2),
        "voltage_b": round(voltage_b, 2),
        "voltage_c": round(voltage_c, 2),
        "current_a": round(current_a, 2),
        "current_b": round(current_b, 2),
        "current_c": round(current_c, 2),
        "power_factor_a": round(power_factor_a, 4),
        "power_factor_b": round(power_factor_b, 4),
        "power_factor_c": round(power_factor_c, 4),
        "active_power_a": round(active_power_a, 2),
        "active_power_b": round(active_power_b, 2),
        "active_power_c": round(active_power_c, 2),
        "reactive_power_a": round(reactive_power_a, 2),
        "reactive_power_b": round(reactive_power_b, 2),
        "reactive_power_c": round(reactive_power_c, 2),
        "apparent_power_a": round(apparent_power_a, 2),
        "apparent_power_b": round(apparent_power_b, 2),
        "apparent_power_c": round(apparent_power_c, 2),
        "voltage_thd_a": round(voltage_thd_a, 2),
        "voltage_thd_b": round(voltage_thd_b, 2),
        "voltage_thd_c": round(voltage_thd_c, 2),
        "current_harmonic_a": round(current_harmonic_a, 2),
        "current_harmonic_b": round(current_harmonic_b, 2),
        "current_harmonic_c": round(current_harmonic_c, 2),
        "frequency": round(frequency, 3),
        "jkwf_status": jkwf_status,
        "circuit_state_1": circuit_state_1,
        "circuit_state_2": circuit_state_2,
        "circuit_state_3": circuit_state_3,
    }
    return payload


def _create_client() -> mqtt.Client:
    client = mqtt.Client()
    if USERNAME and PASSWORD:
        client.username_pw_set(USERNAME, PASSWORD)
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    return client


def _find_local_broker_container() -> str | None:
    if BROKER not in {"localhost", "127.0.0.1"}:
        return None
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return None
    for name in BROKER_CONTAINER_CANDIDATES:
        result = subprocess.run(
            [docker_bin, "ps", "--filter", f"name={name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if lines:
            return lines[0]
    return None


def _publish_via_docker(payload: dict[str, Any]) -> bool:
    container = _find_local_broker_container()
    if not container:
        return False
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return False
    result = subprocess.run(
        [
            docker_bin,
            "exec",
            container,
            "mosquitto_pub",
            "-h",
            "localhost",
            "-u",
            USERNAME,
            "-P",
            PASSWORD,
            "-t",
            TOPIC,
            "-m",
            json.dumps(payload, ensure_ascii=False),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True
    if result.stderr.strip():
        print(f"⚠️ Docker mosquitto_pub 失败，回退 paho: {result.stderr.strip()}")
    return False


def _is_capacitor_bank_device(device: Device) -> bool:
    return resolve_compensation_subtype(
        getattr(device, "device_type", None),
        getattr(device, "device_subtype", None),
    ) == "capacitor_bank_controller"


def list_capacitor_bank_devices(session: Session) -> None:
    devices = session.exec(select(Device).order_by(Device.id)).all()
    matched = [device for device in devices if _is_capacitor_bank_device(device)]
    if not matched:
        print("⚠️  系统中尚无 capacitor_bank_controller 类型的设备。")
        return
    print(f"\n{'ID':>4}  {'序列号':<16}  {'名称':<20}  {'位置':<20}  {'额定容量'}")
    print("-" * 75)
    for device in matched:
        print(
            f"{device.id:>4}  {device.sn or '--':<16}  {device.name:<20}  "
            f"{(device.location or '--'):<20}  {device.rated_capacity or '--'} kvar"
        )
    print()


def send_one(client: mqtt.Client, device: Device, timestamp: datetime, tick: int) -> bool:
    payload = _build_payload(device, timestamp, tick)
    if _publish_via_docker(payload):
        ok = True
    else:
        try:
            result = client.publish(TOPIC, json.dumps(payload, ensure_ascii=False), qos=1)
            result.wait_for_publish(timeout=5)
            ok = result.is_published()
            if not ok:
                print("❌ MQTT 消息未在超时时间内完成发布")
                return False
        except Exception as exc:
            print(f"❌ MQTT 发送失败: {exc}")
            return False
    if ok:
        print(
            f"  [{timestamp.strftime('%H:%M:%S')}] "
            f"topic={TOPIC} code={device.sn} "
            f"P={payload['power']}kW Q={payload['reactive_power']}kvar "
            f"PF={payload['power_factor']} status=0x{payload['jkwf_status']:04X}"
        )
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description="向电容补偿控制器发送模拟 MQTT 遥测数据")
    parser.add_argument("--list", action="store_true", help="列出系统中所有电容补偿控制器")
    parser.add_argument("--id", type=int, dest="device_id", help="目标设备 ID")
    parser.add_argument("--sn", dest="device_sn", help="目标设备序列号（与 --id 二选一）")
    parser.add_argument("--loop", type=int, default=1, help="发送条数（默认 1，0=无限循环）")
    parser.add_argument("--interval", type=float, default=3.0, help="连续发送时的间隔秒数（默认 3）")
    parser.add_argument("--backfill", type=int, default=0, help="补发历史条数（从当前时间向前）")
    parser.add_argument("--backfill-step", type=int, default=60, help="补发历史时每条的时间间隔（秒，默认 60）")
    args = parser.parse_args()

    with Session(engine) as session:
        if args.list:
            list_capacitor_bank_devices(session)
            return

        if args.device_id:
            device = session.get(Device, args.device_id)
        elif args.device_sn:
            device = session.exec(select(Device).where(Device.sn == args.device_sn)).first()
        else:
            print("❌ 请指定 --id 或 --sn，或使用 --list 查看可用设备")
            parser.print_help()
            return

        if not device:
            print("❌ 设备未找到")
            return
        if not _is_capacitor_bank_device(device):
            print(f"⚠️  设备 {device.name}（{device.device_type}/{device.device_subtype}）不是电容补偿控制器，仍继续发送...")

        print(f"\n▶  目标设备: [{device.id}] {device.name}  SN={device.sn}  MQTT={BROKER}:{PORT} {TOPIC}")

        try:
            client = _create_client()
        except Exception as exc:
            print(f"❌ MQTT 连接失败: {exc}")
            return

        if args.backfill > 0:
            print(f"\n📅 补发历史数据：{args.backfill} 条，步长 {args.backfill_step}s")
            base_time = datetime.now() - timedelta(seconds=args.backfill * args.backfill_step)
            success = 0
            for i in range(args.backfill):
                ts = base_time + timedelta(seconds=i * args.backfill_step)
                success += int(send_one(client, device, ts, tick=i))
            print(f"\n✅ 补发完成，成功 {success}/{args.backfill} 条\n")
            client.loop_stop()
            client.disconnect()
            return

        count = 0
        success = 0
        infinite = args.loop == 0
        total = args.loop
        print(f"\n📡 开始发送{'（无限循环，Ctrl+C 停止）' if infinite else f'，共 {total} 条'}\n")
        try:
            while infinite or count < total:
                success += int(send_one(client, device, datetime.now(), tick=count))
                count += 1
                if infinite or count < total:
                    time.sleep(args.interval)
        except KeyboardInterrupt:
            print(f"\n⏹  已停止，成功发送 {success}/{count} 条")
            client.loop_stop()
            client.disconnect()
            return

        print(f"\n✅ 完成，成功发送 {success}/{count} 条\n")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
