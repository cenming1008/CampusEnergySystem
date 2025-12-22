import json
import paho.mqtt.client as mqtt

# 配置 (与你的 docker-compose 保持一致)
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

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
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        topic = f"mine/control/{device_id}"
        payload = json.dumps({
            "command": action, 
            "device_id": device_id
        })
        
        client.publish(topic, payload)
        client.disconnect()
        
        print(f"📡 [指令下发] To ID:{device_id} -> {action}")
        return True
    except Exception as e:
        print(f"❌ 指令发送失败: {e}")
        return False