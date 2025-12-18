import paho.mqtt.client as mqtt
from datetime import datetime
from sqlmodel import Session
from app.core.database import engine
from app.models.tables import DeviceData, Alarm
from app.core.config import load_thresholds

# 配置
MQTT_BROKER = "127.0.0.1"
MQTT_TOPIC = "mine/telemetry"

def process_data(payload_str):
    """处理接收到的单条消息"""
    try:
        data = json.loads(payload_str)
        
        # 1. 解析数据
        device_id = data['device_id']
        # 注意：这里需要把 float 时间戳转为 datetime 对象
        ts = datetime.fromtimestamp(data.get('timestamp', datetime.now().timestamp()))
        
        with Session(engine) as session:
            # 2. 存入 DeviceData 表
            new_record = DeviceData(
                device_id=device_id,
                voltage=data['voltage'],
                current=data['current'],
                power=data['power'],
                energy=data['energy'],
                timestamp=ts
            )
            session.add(new_record)

            # 3. 报警判断逻辑 (从 main.py 移植过来)
            settings = load_thresholds()
            defaults = settings.get("default", {})
            dev_cfg = settings.get("device_thresholds", {}).get(str(device_id), {})
            
            limit_current = dev_cfg.get("current_max", defaults.get("current_max", 45.0))
            
            # 电流报警
            if data['current'] > limit_current:
                msg = f"⚠️ 过载报警! 当前: {data['current']}A (上限: {limit_current}A)"
                print(f"🚨 [报警] {msg}")
                session.add(Alarm(device_id=device_id, message=msg, timestamp=ts, is_resolved=False))
            
            session.commit()
            # print(f"💾 [入库] 设备 {device_id} 数据保存成功")

    except Exception as e:
        print(f"❌ 数据处理错误: {e}")

# MQTT 回调
def on_connect(client, userdata, flags, rc):
    print(f"✅ MQTT Worker 已连接 (代码: {rc})")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    # 收到消息时触发
    payload = msg.payload.decode()
    process_data(payload)

def start_worker():
    print("👷 启动 MQTT 数据处理工人...")
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, 1883, 60)
        client.loop_forever() # 永久阻塞，等待消息
    except KeyboardInterrupt:
        print("停止工作")
    except Exception as e:
        print(f"连接错误: {e}")

if __name__ == "__main__":
    start_worker()