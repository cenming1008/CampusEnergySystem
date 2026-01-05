import json
import asyncio
import paho.mqtt.client as mqtt
from datetime import datetime
from sqlmodel import Session, select
from app.core.database import engine
from app.core.settings import settings  # 使用统一配置管理
from app.services.data_processor import process_device_data
from app.models.tables import Device

# 从统一配置中获取MQTT配置
MQTT_BROKER = settings.mqtt_broker
MQTT_PORT = settings.mqtt_port
MQTT_TOPIC = settings.mqtt_topic
MQTT_TOPIC_WILDCARD = settings.mqtt_topic_wildcard

# 全局客户端实例
client = mqtt.Client()

def get_device_id_by_code(device_code: str, session: Session) -> int | None:
    """根据设备编码(device_code)或序列号(sn)查找设备ID"""
    # 先尝试用code查找（如果Device模型有code字段）
    # 如果没有，则用sn字段（因为压力测试脚本的code应该对应sn）
    device = session.exec(select(Device).where(Device.sn == device_code)).first()
    if device:
        return device.id
    return None

def process_data(payload_str, topic: str = None, broadcast_callback=None):
    """
    处理消息：
    1. 存入数据库 (同步)
    2. 如果有回调，通过 WebSocket 广播 (异步)
    
    Args:
        payload_str: MQTT消息内容
        topic: MQTT主题（用于提取device_code）
        broadcast_callback: WebSocket广播回调
    """
    try:
        data = json.loads(payload_str)
        
        # 1. 确定device_id
        device_id = None
        if 'device_id' in data:
            # 标准格式：直接使用device_id
            device_id = data['device_id']
        elif 'device_code' in data or topic:
            # 压力测试格式：从device_code或topic中提取
            device_code = data.get('device_code')
            if not device_code and topic:
                # 从topic中提取：mine/device/{code}/telemetry
                parts = topic.split('/')
                if len(parts) >= 3:
                    device_code = parts[2]
            
            if device_code:
                with Session(engine) as session:
                    device_id = get_device_id_by_code(device_code, session)
                    if not device_id:
                        print(f"⚠️ 未找到设备编码: {device_code}，跳过此消息")
                        return
        
        if not device_id:
            print("❌ 无法确定device_id，跳过此消息")
            return
        
        # 2. 处理时间戳
        ts = datetime.fromtimestamp(data.get('timestamp', datetime.now().timestamp()))
        
        # 3. 数据格式转换（支持压力测试脚本的格式）
        # 压力测试脚本发送：temperature, humidity, vibration, current, status
        # 后端期望：voltage, current, power, energy
        voltage = data.get('voltage', 380.0)  # 默认电压
        current = data.get('current', 0.0)
        
        # 如果只有temperature等字段，进行转换
        if 'power' not in data:
            # 根据current计算power（简化计算：P = U * I）
            power = voltage * current / 1000.0  # 转换为kW
        else:
            power = data['power']
        
        if 'energy' not in data:
            # 如果没有energy，设为0（或根据实际情况计算）
            energy = 0.0
        else:
            energy = data['energy']
        
        # 4. 存库
        with Session(engine) as session:
            record = process_device_data(
                session=session,
                device_id=device_id,
                voltage=voltage,
                current=current,
                power=power,
                energy=energy,
                timestamp=ts
            )
            
        # 5. WebSocket 广播
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
            broadcast_callback(ws_msg)

    except json.JSONDecodeError:
        print("❌ JSON 解析失败")
    except Exception as e:
        print(f"❌ 数据处理错误: {e}")
        import traceback
        traceback.print_exc()

# --- 新增：专门给 FastAPI 调用的非阻塞启动函数 ---
def start_mqtt_background(on_message_callback):
    
    def on_connect_internal(client, userdata, flags, rc):
        print(f"✅ [系统内部] MQTT 已连接 (代码: {rc})")
        # 订阅多个主题：标准主题和通配符主题（支持压力测试脚本）
        client.subscribe(MQTT_TOPIC)
        client.subscribe(MQTT_TOPIC_WILDCARD)
        print(f"📡 [MQTT] 已订阅主题: {MQTT_TOPIC} 和 {MQTT_TOPIC_WILDCARD}")

    def on_message_internal(client, userdata, msg):
        payload = msg.payload.decode()
        topic = msg.topic
        # 将接收到的消息传给处理函数，并带上主题和回调
        process_data(payload, topic=topic, broadcast_callback=on_message_callback)

    client.on_connect = on_connect_internal
    client.on_message = on_message_internal
    
    try:
        # 如果配置了用户名和密码，设置认证
        if settings.mqtt_username and settings.mqtt_password:
            client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        # loop_start 会启动一个后台线程自动处理网络循环，不会阻塞主程序
        client.loop_start()
    except Exception as e:
        print(f"❌ MQTT 连接失败: {e}")

# (保留原来的 main 块，以便你可以单独测试这个文件)
if __name__ == "__main__":
    def dummy_cb(msg):
        print(f"模拟广播: {msg}")
        
    print("单独运行模式...")
    def on_connect_test(c, u, f, r):
        c.subscribe(MQTT_TOPIC)
        c.subscribe(MQTT_TOPIC_WILDCARD)
    client.on_connect = on_connect_test
    client.on_message = lambda c, u, m: process_data(m.payload.decode(), topic=m.topic, broadcast_callback=dummy_cb)
    
    # 如果配置了用户名和密码，设置认证
    if settings.mqtt_username and settings.mqtt_password:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()