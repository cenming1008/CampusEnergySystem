import random
import time
import json
import requests
import paho.mqtt.client as mqtt

# ================= 配置区域 =================
# 1. MQTT 配置 (负责收发数据)
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC_TELEMETRY = "mine/telemetry"    # 发送：遥测数据
MQTT_TOPIC_CONTROL_PREFIX = "mine/control/" # 接收：控制指令前缀 (mine/control/1)

# 2. HTTP 配置 (负责登录和同步初始状态)
API_BASE = "http://127.0.0.1:8088"
LOGIN_URL = f"{API_BASE}/auth/login"  # 登录接口
DEVICES_URL = f"{API_BASE}/devices/"  # 设备列表接口

# 3. 登录账号 (必须与数据库中的一致)
ADMIN_USER = "admin"
ADMIN_PASS = "123456"

# 4. 模拟设备列表 (ID 1-10)
TARGET_DEVICES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# ================= 全局状态管理 =================
# 记录每个设备的运行状态 (True: 运行中, False: 已停机)
# 默认全开，后续会根据 API 或 MQTT 指令动态更新
device_states = {device_id: True for device_id in TARGET_DEVICES}

# 记录累计能耗 (模拟电表走字)
device_energies = {device_id: 0.0 for device_id in TARGET_DEVICES}

# 全局 API Token
current_token = None


# ================= 核心功能函数 =================

def login():
    """登录后端 API 获取 Token，用于同步设备状态"""
    global current_token
    print(f"🔑 模拟器正在尝试登录 ({ADMIN_USER})...")
    try:
        response = requests.post(LOGIN_URL, data={"username": ADMIN_USER, "password": ADMIN_PASS})
        if response.status_code == 200:
            current_token = response.json().get("access_token")
            print("✅ 登录成功！已获取 API 访问权限。")
            return True
        else:
            print(f"❌ 登录失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 连接后端 API 失败: {e}")
        return False

def sync_device_status():
    """从后端 API 拉取最新的设备开关状态 (双重保险)"""
    global device_states
    if not current_token:
        return

    try:
        headers = {"Authorization": f"Bearer {current_token}"}
        # 设置短超时，防止卡住主循环
        res = requests.get(DEVICES_URL, headers=headers, timeout=2)
        
        if res.status_code == 200:
            devices = res.json()
            count = 0
            for d in devices:
                d_id = d['id']
                is_active = d['is_active']
                # 如果状态不一致，更新本地状态
                if d_id in device_states and device_states[d_id] != is_active:
                    device_states[d_id] = is_active
                    count += 1
            if count > 0:
                print(f"🔄 [自动同步] 从 API 更新了 {count} 个设备的状态")
    except Exception:
        pass # 网络波动忽略，不影响主流程

# ================= MQTT 回调函数 (反向控制核心) =================

def on_connect(client, userdata, flags, rc):
    """连接成功后，立即订阅控制频道"""
    if rc == 0:
        print("✅ MQTT Broker 连接成功！")
        # 订阅所有设备的控制指令：mine/control/+
        # '+' 是通配符，表示匹配任何 ID
        subscription_topic = f"{MQTT_TOPIC_CONTROL_PREFIX}+"
        client.subscribe(subscription_topic)
        print(f"👂 已启动指令监听: {subscription_topic}")
    else:
        print(f"❌ MQTT 连接失败，错误代码: {rc}")

def on_message(client, userdata, msg):
    """
    当收到控制指令时触发
    Topic 示例: mine/control/2
    Payload 示例: {"command": "stop", "device_id": 2}
    """
    try:
        topic = msg.topic
        payload_str = msg.payload.decode()
        data = json.loads(payload_str)
        
        # 1. 解析设备 ID (从 Topic 或 Payload 解析均可)
        # 这里从 topic 解析: mine/control/2 -> 2
        target_id_str = topic.split("/")[-1]
        
        if not target_id_str.isdigit():
            return
            
        target_id = int(target_id_str)
        command = data.get("command")

        # 2. 执行指令
        if command == "stop":
            device_states[target_id] = False
            print(f"\n🛑 [收到指令] !!! 紧急停止设备 {target_id} !!!")
            print(f"   -> 传感器读数将立即归零\n")
            
        elif command == "start":
            device_states[target_id] = True
            print(f"\n▶️  [收到指令] !!! 启动设备 {target_id} !!!")
            print(f"   -> 恢复正常数据上报\n")
            
    except Exception as e:
        print(f"⚠️ 指令解析错误: {e}")

# ================= 数据生成逻辑 =================

def generate_sensor_data(device_id, is_active):
    """
    生成模拟的电气参数
    :param is_active: 如果为 False，强制返回 0
    """
    # 🛑 停机状态：所有读数归零
    if not is_active:
        return 0.0, 0.0, 0.0  # 电压, 电流, 功率

    # ▶️ 运行状态：生成符合煤矿设备特征的波动数据
    
    # 1. 电压 (220V 基准，小幅波动)
    base_voltage = 220.0
    voltage = round(base_voltage + random.uniform(-5, 5), 1)
    
    # 2. 电流 (根据设备ID区分负载大小，模拟不同功率的设备)
    # ID越大，模拟的电流越大
    base_amp = 15.0 + (device_id * 8) 
    fluctuation = base_amp * 0.1 # 10% 波动
    current = round(base_amp + random.uniform(-fluctuation, fluctuation), 2)
    
    # 模拟偶尔的电流尖峰 (过载前兆)
    # 1% 的概率电流飙升到 2 倍
    if random.randint(1, 100) > 99:
        current = round(current * 2.5, 2)
        print(f"⚠️ [模拟故障] 设备 {device_id} 瞬时电流过载: {current}A")

    # 3. 功率 (P = U * I / 1000) kW
    power = round((voltage * current) / 1000, 3)
    
    return voltage, current, power

# ================= 主程序 =================

def start_simulation():
    print("========================================")
    print("   🏭 煤矿能源系统 - 智能硬件模拟器 v2.0   ")
    print("========================================")
    
    # 1. 先登录 API (获取 Token)
    login()
    
    # 2. 初始化 MQTT 客户端
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message # 👈 绑定消息回调
    
    # 3. 连接 MQTT 并启动后台线程
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start() # ⚡ 开启后台线程处理网络收发 (非阻塞)
    except Exception as e:
        print(f"❌ 致命错误: 无法连接 MQTT Broker ({MQTT_BROKER})")
        print("请检查 docker 容器是否启动: docker-compose ps")
        return

    # 4. 进入主循环：产生数据 -> 发送 -> 休眠
    loop_count = 0
    try:
        while True:
            current_time = time.time()
            
            # 每 10 轮循环 (约10秒) 同步一次 API 状态
            if loop_count % 10 == 0:
                sync_device_status()

            # 遍历所有设备生成数据
            for dev_id in TARGET_DEVICES:
                # 获取当前状态 (受 MQTT 指令控制)
                is_running = device_states.get(dev_id, True)
                
                # 生成数据
                v, c, p = generate_sensor_data(dev_id, is_running)
                
                # 只有运行中才累加电表读数 (kWh = kW * h)
                # 模拟器每1秒跑一次，所以是 p * (1/3600)
                if is_running:
                    device_energies[dev_id] += p * (1 / 3600)

                # 构造 Payload
                payload = {
                    "device_id": dev_id,
                    "voltage": v,
                    "current": c,
                    "power": p,
                    "energy": round(device_energies[dev_id], 4),
                    "timestamp": current_time
                }

                # 发送 MQTT 消息
                client.publish(MQTT_TOPIC_TELEMETRY, json.dumps(payload))
                
                # 为了控制台清爽，只打印部分日志
                # 打印 ID=1 的，或者刚刚被停机的，或者发生过载的
                if dev_id == 1: 
                    status_icon = "🟢" if is_running else "🔴"
                    print(f"📡 发送 [ID:1] {status_icon} | U:{v}V I:{c}A P:{p}kW")

            loop_count += 1
            time.sleep(1) # 模拟采样频率 1Hz

    except KeyboardInterrupt:
        print("\n👋 模拟器已停止")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    start_simulation()