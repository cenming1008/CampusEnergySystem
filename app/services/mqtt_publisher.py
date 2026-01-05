import json
import paho.mqtt.client as mqtt
from app.core.settings import settings  # 使用统一配置管理

# 从统一配置中获取MQTT配置
MQTT_BROKER = settings.mqtt_broker
MQTT_PORT = settings.mqtt_port

def publish_control_command(device_id: int, action: str):
    """
    发送反向控制指令给设备
    :param device_id: 设备ID
    :param action: "start" | "stop"
    """
    try:
        # 创建一个临时客户端发送单条指令
        # 注意：高并发场景下应维护全局连接，但这里演示够用了
        client = mqtt.Client()
        
        # 如果配置了用户名和密码，设置认证
        if settings.mqtt_username and settings.mqtt_password:
            client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        topic = f"mine/control/{device_id}"
        payload = json.dumps({
            "command": action, 
            "device_id": device_id
        })
        
        client.publish(topic, payload, qos=1)
        client.disconnect()
        
        print(f"📡 [指令下发] To ID:{device_id} -> {action}")
        return True
    except Exception as e:
        print(f"❌ 指令发送失败: {e}")
        return False