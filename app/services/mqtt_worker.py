import os
import json
import asyncio
import paho.mqtt.client as mqtt
from datetime import datetime
from sqlmodel import Session
from app.core.database import engine
from app.services.data_processor import process_device_data

# 配置
MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_TOPIC = "mine/telemetry"

# 全局客户端实例
client = mqtt.Client()

def process_data(payload_str, broadcast_callback=None):
    """
    处理消息：
    1. 存入数据库 (同步)
    2. 如果有回调，通过 WebSocket 广播 (异步)
    """
    try:
        data = json.loads(payload_str)
        device_id = data['device_id']
        ts = datetime.fromtimestamp(data.get('timestamp', datetime.now().timestamp()))
        
        # 1. 存库 (复用之前的逻辑)
        with Session(engine) as session:
            # 调用公共服务处理数据和报警
            record = process_device_data(
                session=session,
                device_id=device_id,
                voltage=data['voltage'],
                current=data['current'],
                power=data['power'],
                energy=data['energy'],
                timestamp=ts
            )
            
        # 2. WebSocket 广播 (构建前端需要的数据格式)
        if broadcast_callback:
            ws_msg = {
                "type": "telemetry_update",
                "data": {
                    "device_id": device_id,
                    "voltage": record.voltage,
                    "current": record.current,
                    "power": record.power,
                    "energy": record.energy,
                    "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            # 因为 MQTT 回调是同步的，而 broadcast 是异步的，需要这就用 run_coroutine_threadsafe
            # 或者简单的方案：我们在 main.py 里定义 callback 时处理 event loop
            broadcast_callback(ws_msg)

    except json.JSONDecodeError:
        print("❌ JSON 解析失败")
    except Exception as e:
        print(f"❌ 数据处理错误: {e}")

# --- 新增：专门给 FastAPI 调用的非阻塞启动函数 ---
def start_mqtt_background(on_message_callback):
    
    def on_connect_internal(client, userdata, flags, rc):
        print(f"✅ [系统内部] MQTT 已连接 (代码: {rc})")
        client.subscribe(MQTT_TOPIC)

    def on_message_internal(client, userdata, msg):
        payload = msg.payload.decode()
        # 将接收到的消息传给处理函数，并带上回调
        process_data(payload, broadcast_callback=on_message_callback)

    client.on_connect = on_connect_internal
    client.on_message = on_message_internal
    
    try:
        client.connect(MQTT_BROKER, 1883, 60)
        # loop_start 会启动一个后台线程自动处理网络循环，不会阻塞主程序
        client.loop_start()
    except Exception as e:
        print(f"❌ MQTT 连接失败: {e}")

# (保留原来的 main 块，以便你可以单独测试这个文件)
if __name__ == "__main__":
    def dummy_cb(msg):
        print(f"模拟广播: {msg}")
        
    print("单独运行模式...")
    client.on_connect = lambda c, u, f, r: c.subscribe(MQTT_TOPIC)
    client.on_message = lambda c, u, m: process_data(m.payload.decode(), dummy_cb)
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_forever()