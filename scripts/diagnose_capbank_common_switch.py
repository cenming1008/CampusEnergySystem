"""
诊断脚本：对比公补 vs A 相 手动投切命令，定位公补失败原因。

流程：
  1. 抓取 device 12 当前 telemetry 基线（直读数据库）
  2. 订阅所有相关 MQTT 主题（telemetry/control/receipt 等）
  3. 发送 1 次 A 相 投入命令（已知能成功，作为正常基线）
  4. 等 8s 抓所有 MQTT 流量 + telemetry 差量
  5. 发送 1 次 公补 投入命令（疑似失败）
  6. 等 8s 抓所有 MQTT 流量 + telemetry 差量
  7. 打印对比报告

注意：会真实下发投切命令到设备。运行前请确认设备状态正常。
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime

import psycopg2
import paho.mqtt.client as mqtt

DB_URL = "postgresql://admin:password123@localhost:5432/campus_energy"
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_USER = "campus_mqtt"
MQTT_PASS = "campus_mqtt_secret_2026"

DEVICE_ID = 12
DEVICE_SN = "CAP-001"
CONTROL_TOPIC = f"campus/control/{DEVICE_SN}"
WATCH_PATTERNS = [
    "campus/#",  # 抓所有 campus topic，便于看采集器回执到底走的哪条
]


def snapshot_state():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT timestamp, circuit_state_phase_a, circuit_state_phase_b, circuit_state_phase_c,
               circuit_state_common_1, circuit_state_common_2, circuit_state_common_3,
               phase_a_circuit_running_count, phase_b_circuit_running_count, phase_c_circuit_running_count,
               common_circuit_running_count, running_circuit_count
        FROM capacitor_bank_telemetry
        WHERE device_id=%s
        ORDER BY timestamp DESC LIMIT 1
        """,
        (DEVICE_ID,),
    )
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    conn.close()
    return dict(zip(cols, row)) if row else None


def format_state(state):
    if not state:
        return "<no telemetry>"
    bits = {
        "A": f"{state['circuit_state_phase_a']:08b}",
        "B": f"{state['circuit_state_phase_b']:08b}",
        "C": f"{state['circuit_state_phase_c']:08b}",
        "common_1": f"{state['circuit_state_common_1']:08b}",
        "common_2": f"{state['circuit_state_common_2']:08b}",
        "common_3": f"{state['circuit_state_common_3']:08b}",
    }
    counts = (
        f"A={state['phase_a_circuit_running_count']} "
        f"B={state['phase_b_circuit_running_count']} "
        f"C={state['phase_c_circuit_running_count']} "
        f"common={state['common_circuit_running_count']} "
        f"total={state['running_circuit_count']}"
    )
    return f"t={state['timestamp']} bits={bits} counts={counts}"


def latest_control_log_id():
    """返回当前最大 control_log id，便于知道我们插入的 log id 范围。"""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM device_control_log")
    n = cur.fetchone()[0]
    conn.close()
    return n


def insert_control_log(action_label: str, command_args: dict) -> int:
    """直接插一条 pending control_log，模拟 API 走过的路径，拿到 command_id。"""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO device_control_log
          (device_id, action, target_status, previous_status, operator, command_source, result, reason, created_at)
        VALUES (%s, 'manual_switch', TRUE, TRUE, 'diagnostic-script', 'diagnostic-script', 'accepted', %s, NOW())
        RETURNING id
        """,
        (DEVICE_ID, f"[诊断] {action_label} args={json.dumps(command_args, ensure_ascii=False)}"),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return new_id


def build_payload(command_id: int, *, phase: str, switch_action: str = "on") -> dict:
    phase_code = {"A": 0, "B": 1, "C": 2, "COMMON": 3}[phase]
    action_code = {"none": 0, "on": 0x11, "off": 0x22}[switch_action]
    return {
        "message_type": "control_command",
        "protocol_version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "device_id": DEVICE_ID,
        "device_code": DEVICE_SN,
        "command": "manual_switch",
        "command_id": str(command_id),
        "reason": f"[diagnostic] manual_switch {phase} {switch_action}",
        "manual_mode": "manual",
        "phase": phase,
        "switch_action": switch_action,
        "protocol_function_code": "0x44",
        "manual_mode_code": 1,
        "phase_code": phase_code,
        "switch_action_code": action_code,
    }


class MqttCapture:
    def __init__(self):
        self.events = []  # list of (timestamp, topic, payload_str)
        self.lock = threading.Lock()
        self.client = mqtt.Client(client_id=f"diag-{uuid.uuid4().hex[:8]}")
        self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.client.on_message = self._on_message
        self.client.on_connect = lambda c, *_: [c.subscribe(p, qos=1) for p in WATCH_PATTERNS]
        self.client.connect(MQTT_HOST, MQTT_PORT, 60)
        self.client.loop_start()
        time.sleep(0.5)

    def _on_message(self, client, userdata, msg):
        try:
            text = msg.payload.decode("utf-8", errors="replace")
        except Exception:
            text = repr(msg.payload)
        with self.lock:
            self.events.append((datetime.now().isoformat(timespec="milliseconds"), msg.topic, text))

    def drain(self):
        with self.lock:
            out = list(self.events)
            self.events.clear()
        return out

    def publish(self, topic: str, payload: dict):
        info = self.client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1)
        info.wait_for_publish(timeout=5)

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()


def filter_events(events, *, command_id: str):
    """过滤出 telemetry / receipt / 与本次命令相关的事件。"""
    relevant = []
    for ts, topic, text in events:
        keep = False
        lower = topic.lower()
        if "control" in lower or "receipt" in lower or "command" in lower:
            keep = True
        if command_id and command_id in text:
            keep = True
        if "telemetry" in lower:
            # 仅保留补偿器 telemetry，避免污染
            if DEVICE_SN.lower() in lower or f'"device_id": {DEVICE_ID}' in text or f'"device_code": "{DEVICE_SN}"' in text:
                keep = True
        if keep:
            relevant.append((ts, topic, text))
    return relevant


def run_one_round(label: str, capture: MqttCapture, *, phase: str, switch_action: str = "on", wait_seconds: float = 8.0):
    print(f"\n{'=' * 80}\n[{label}] phase={phase} action={switch_action}")
    print(f"--- 命令前 state ---")
    before = snapshot_state()
    print(f"  {format_state(before)}")

    command_id = insert_control_log(f"{phase} {switch_action}", {"phase": phase, "switch_action": switch_action})
    payload = build_payload(command_id, phase=phase, switch_action=switch_action)
    print(f"--- 发送 payload (command_id={command_id}) ---")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    capture.drain()  # 清空之前的事件
    capture.publish(CONTROL_TOPIC, payload)
    print(f"--- 等待 {wait_seconds}s 抓取 MQTT 流量 + telemetry ---")
    time.sleep(wait_seconds)

    events = capture.drain()
    rel = filter_events(events, command_id=str(command_id))
    print(f"--- 抓到 {len(events)} 条 MQTT 事件，与本命令相关 {len(rel)} 条 ---")
    for ts, topic, text in rel:
        short = text if len(text) < 400 else text[:380] + f"...<+{len(text) - 380}b>"
        print(f"  [{ts}] {topic}\n    {short}")

    after = snapshot_state()
    print(f"--- 命令后 state ---")
    print(f"  {format_state(after)}")

    # 计算差量
    if before and after:
        deltas = {}
        for key in (
            "phase_a_circuit_running_count",
            "phase_b_circuit_running_count",
            "phase_c_circuit_running_count",
            "common_circuit_running_count",
            "running_circuit_count",
        ):
            d = (after[key] or 0) - (before[key] or 0)
            if d != 0:
                deltas[key] = d
        print(f"--- 差量: {deltas or '无变化（投切未生效）'} ---")

    # 查 control_log 当前状态
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT result, reason FROM device_control_log WHERE id=%s", (command_id,))
    log_row = cur.fetchone()
    conn.close()
    if log_row:
        print(f"--- control_log[{command_id}] result={log_row[0]!r}")
        print(f"    reason={log_row[1]}")


def main():
    print(f"=== 公补投切诊断脚本 ===")
    print(f"  设备 device_id={DEVICE_ID} sn={DEVICE_SN}")
    print(f"  控制 topic={CONTROL_TOPIC}")
    print(f"  开始时间={datetime.now().isoformat()}")

    capture = MqttCapture()
    print(f"  MQTT 订阅成功: {WATCH_PATTERNS}")

    try:
        # Round 1: 公补投入（疑似失败基线，先做，避免后续 A 相投入污染状态对比）
        run_one_round("R1 公补 投入（疑似失败基线）", capture, phase="COMMON", switch_action="on")

        # Round 2: A 相投入（已知能工作的对照）
        run_one_round("R2 A 相 投入（正常对照）", capture, phase="A", switch_action="on")

        # Round 3: 把 A 相切回去，避免对设备状态造成净影响
        run_one_round("R3 A 相 切除（恢复）", capture, phase="A", switch_action="off")
    finally:
        capture.close()

    print(f"\n=== 完成 {datetime.now().isoformat()} ===")


if __name__ == "__main__":
    main()
