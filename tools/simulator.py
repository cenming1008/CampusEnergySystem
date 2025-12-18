import random
import time
import json
import requests
import paho.mqtt.client as mqtt

# ================= 配置 =================
# 1. MQTT 配置 (负责发数据)
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "mine/telemetry"

# 2. HTTP 配置 (负责查开关状态)
API_BASE = "http://127.0.0.1:8088"
LOGIN_URL = f"{API_BASE}/auth/login"  # 登录接口
DEVICES_URL = f"{API_BASE}/devices/"  # 查状态接口

# 3. 登录账号 (必须与 create_admin.py 创建的一致)
ADMIN_USER = "admin"
ADMIN_PASS = "123456"

TARGET_DEVICES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# 设备模拟参数
DEVICE_PROFILES = {
    1: (15.0, 2.0), 2: (90.0, 5.0), 3: (55.0, 5.0), 4: (180.0, 15.0), 5: (35.0, 3.0),
    6: (280.0, 40.0), 7: (100.0, 10.0), 8: (150.0, 50.0), 9: (70.0, 5.0), 10: (110.0, 15.0)
}

# 全局 Token
current_token = None

def login():
    """登录获取 Token"""
    global current_token
    print(f"🔑 模拟器正在登录 ({ADMIN_USER})...")
    try:
        response = requests.post(LOGIN_URL, data={"username": ADMIN_USER, "password": ADMIN_PASS})
        if response.status_code == 200:
            current_token = response.json().get("access_token")
            print("✅ 登录成功，已获取控制权！")
            return True
        else:
            print(f"❌ 登录失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 连接后端失败: {e}")
        return False

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT 连接成功！")
    else:
        print(f"❌ MQTT 连接失败，代码: {rc}")

def generate_instant_data(device_id):
    base_voltage = 220.0
    voltage = round(base_voltage + random.uniform(-3, 3), 1)
    
    profile = DEVICE_PROFILES.get(device_id, (20.0, 2.0))
    base_amp, fluctuation = profile
    current = round(base_amp + random.uniform(-fluctuation, fluctuation), 2)
    
    if random.randint(1, 100) > 99:
        current = current * 1.5
        print(f"⚠️ [模拟故障] 设备 {device_id} 电流激增!")

    power = round((voltage * current) / 1000, 3)
    return voltage, current, power

def start_simulation():
    print(f"--- 启动工业级 MQTT 模拟器 (带鉴权) ---")
    
    # 1. 启动时先登录一次
    if not login():
        print("⚠️ 警告：登录失败，将无法获取设备开关状态（默认全部开启）")

    # 2. 初始化 MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"❌ 无法连接 MQTT: {e}")
        return

    device_energies = {id: 0.0 for id in TARGET_DEVICES}
    
    while True:
        try:
            # 3. 获取在线状态 (带 Token 访问)
            online_map = {}
            if current_token:
                headers = {"Authorization": f"Bearer {current_token}"}
                try:
                    res = requests.get(DEVICES_URL, headers=headers, timeout=1)
                    if res.status_code == 200:
                        online_map = {d['id']: d['is_active'] for d in res.json()}
                    elif res.status_code == 401:
                        print("🔄 Token 过期，尝试重新登录...")
                        login() # 重新登录
                except:
                    pass # 网络波动忽略
            
            # 4. 生成并发送数据
            for dev_id in TARGET_DEVICES:
                # 如果获取不到状态，默认视为开启
                if online_map and not online_map.get(dev_id, True):
                    continue

                v, c, p = generate_instant_data(dev_id)
                device_energies[dev_id] += p * (1 / 3600)

                payload = {
                    "device_id": dev_id,
                    "voltage": v,
                    "current": c,
                    "power": p,
                    "energy": round(device_energies[dev_id], 4),
                    "timestamp": time.time()
                }

                client.publish(MQTT_TOPIC, json.dumps(payload))
                
                if dev_id == 6 or random.random() > 0.95:
                    print(f"📡 [MQTT] 发送 ID:{dev_id} | {p}kW")

        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(1)

        time.sleep(1)

if __name__ == "__main__":
    start_simulation()