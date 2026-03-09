"""
通用 MQTT 订阅骨架（复制即用）

用法：
1. 改 BROKER / PORT / TOPICS
2. 在 on_message 里写你自己的处理逻辑（不要调 process_data）
3. 运行: python mqtt_subscriber_template.py
"""
import paho.mqtt.client as mqtt

# ---------- 配置（按需修改）----------
BROKER = "localhost"
PORT = 1883
TOPICS = ["mine/telemetry", "mine/device/+/telemetry"]  # 可多个
USERNAME = None   # 无需鉴权时保持 None
PASSWORD = None
KEEPALIVE = 60
# ------------------------------------

client = mqtt.Client()


def on_connect(_client, _userdata, _flags, rc):
    print(f"MQTT 已连接 rc={rc}")
    for topic in TOPICS:
        _client.subscribe(topic)
        print(f"  已订阅: {topic}")


def on_message(_client, _userdata, msg):
    topic = getattr(msg, "topic", "")
    payload = msg.payload.decode(errors="ignore")
    # ---------- 这里写你的逻辑，例如只打印 ----------
    print(f"[{topic}] {payload[:200]}")
    # 若需要解析 JSON: data = json.loads(payload); ...
    # 若需要写库/推 WebSocket: 在这里调用你的函数，传入 payload 或 data
    # ---------- 结束 ----------


if __name__ == "__main__":
    client.on_connect = on_connect
    client.on_message = on_message

    if USERNAME and PASSWORD:
        client.username_pw_set(USERNAME, PASSWORD)
    client.connect(BROKER, PORT, KEEPALIVE)

    # 二选一：
    client.loop_start()   # 后台线程，不阻塞，适合嵌入到 FastAPI 等
    # client.loop_forever()  # 阻塞直到进程结束，适合单独跑脚本

    print("MQTT 已在后台运行 (loop_start)。按 Ctrl+C 退出。")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.loop_stop()
