import requests # 发送HTTP请求
import time
import random # 生成随机数
import threading # 多线程
import sys # 系统相关
import json # JSON处理
import paho.mqtt.client as mqtt # MQTT客户端

# 配置
API_URL = "http://localhost:8088" # API地址（后端运行在8088端口，无/api/v1前缀）
MQTT_BROKER = "127.0.0.1" # MQTT Broker地址
MQTT_PORT = 1883 # MQTT端口
MQTT_USERNAME = "admin" # MQTT用户名
MQTT_PASSWORD = "123456" # MQTT密码
MQTT_TOPIC = "test" # MQTT主题
MQTT_QOS = 0 # MQTT QoS这是MQTT协议中的一个参数，表示消息的可靠传输级别。0表示最多一次，1表示至少一次，2表示只有一次。
MQTT_RETAIN = False # MQTT Retain
MQTT_CLIENT_ID = "stress_test" # MQTT客户端ID

# 模拟配置：模拟100个设备，每个设备每秒发送10条消息
DEVICE_COUNT = 100 # 设备数量
INTERVAL_SECONDS = 2 # 间隔时间
MESSAGE_COUNT = 10 # 消息数量
ALARM_RATE = 0.05 # 告警数量比例

# 全局变量
oauth_token = None # OAuth token
device_ids = [] # 设备ID列表

def login():
    """获取OAuth token"""
    global oauth_token
    try:
        # 使用OAuth2PasswordRequestForm格式（username和password作为form data）
        response = requests.post(
            f"{API_URL}/auth/login",
            data={"username": MQTT_USERNAME, "password": MQTT_PASSWORD}
        )
        if response.status_code == 200:  # 登录成功
            oauth_token = response.json()["access_token"]
            print("登录成功")
        else:
            print(f"登录失败: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"登录失败: {e}")
        sys.exit(1) # 退出程序
    return oauth_token

def register_device():
    """注册设备"""
    global device_ids
    headers = {"Authorization": f"Bearer {oauth_token}"}

    for i in range(1, DEVICE_COUNT + 1): # 详细解释：range(1, DEVICE_COUNT + 1) 表示从1到DEVICE_COUNT，包括1和DEVICE_COUNT
        device_code = f"SIM_DEV_{i:04d}" # 设备编码，4位数字，不足4位前面补0

        # 1.  创建设备（使用正确的字段名：sn而不是code，device_type而不是type）
        payload = {
            "name": f"模拟通风机 #{i}",
            "sn": device_code,  # 使用sn字段（对应Device模型的sn字段）
            "device_type": "VENTILATOR",
            "location": "Simulated Site A",
            "is_active": True,
        }

        try:
            res = requests.post(f"{API_URL}/devices", headers=headers, json=payload)  # 使用/devices端点
            if res.status_code in [200, 201]:
                device_id = res.json().get("id")
                device_ids.append(device_code)  # 将设备编码添加到列表
                print(f"设备 {device_code} 创建成功: {device_id}")
            else:
                print(f"设备 {device_code} 创建失败: {res.status_code} {res.text}")
        except Exception as e:
            print(f"设备 {device_code} 创建失败: {e}")
            sys.exit(1) # 退出程序
    print(f"设备创建完成: {len(device_ids)} 个设备")
    return device_ids
    
def simulate_device_behavior(device_code):
    """模拟设备数据（包含后端需要的字段）"""
    timestamp = time.time()
    
    # 模拟电压（正常范围：360-400V）
    voltage = 380.0 + random.uniform(-20, 20)
    
    # 模拟电流（根据设备状态变化）
    is_faulty = random.random() < ALARM_RATE
    if is_faulty:
        # 故障状态：电流异常高
        current = random.uniform(80, 120)
        power = voltage * current / 1000.0  # 转换为kW
    else:
        # 正常状态：电流在合理范围
        current = random.uniform(45, 55)
        power = voltage * current / 1000.0  # 转换为kW
    
    # 模拟能耗（累计值，这里简化为基于功率的增量）
    energy = power * 0.001  # 简化计算：假设每次发送间隔很小
    
    payload = {
        "device_code": device_code,  # 保留device_code用于后端查找设备ID
        "timestamp": timestamp,
        "voltage": round(voltage, 2),
        "current": round(current, 2),
        "power": round(power, 3),
        "energy": round(energy, 3),
        # 可选：保留原始字段用于扩展
        "status": "ALARM" if is_faulty else "RUNNING"
    }
    return payload

def mqtt_worker(worker_id, assigned_devices):
    """MQTT工作线程"""
    client = mqtt.Client(f"Sim_Worker_{worker_id}")
    
    # 设置MQTT用户名和密码
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()  # 启动消息循环，确保消息能够发送
    except Exception as e:
        print(f"MQTT连接失败: {e}，线程 {worker_id} 退出")
        return 

    while True:
        for code in assigned_devices:
            data = simulate_device_behavior(code)
            topic = f"mine/device/{code}/telemetry"
            try:
                result = client.publish(topic, json.dumps(data), qos=MQTT_QOS, retain=MQTT_RETAIN)
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    print(f"线程 {worker_id} 发送设备 {code} 数据失败: {result.rc}")
                else:
                    print(f"线程 {worker_id} 发送设备 {code} 数据: {data}")
            except Exception as e:
                print(f"线程 {worker_id} 发送设备 {code} 数据异常: {e}")
            time.sleep(0.01)
        time.sleep(INTERVAL_SECONDS)

def start_simulation():
    if not login():
        print("登录失败，无法继续")
        sys.exit(1)
    
    register_device()
    
    if not device_ids:
        print("没有设备被创建，无法开始模拟")
        sys.exit(1)
    
    threads = []
    chunk_size = 50
    chunks = [device_ids[i:i+chunk_size] for i in range(0, len(device_ids), chunk_size)]
    print(f"总共 {len(chunks)} 个线程，每个线程发送 {chunk_size} 个设备")

    for i, chunk in enumerate(chunks):
        t = threading.Thread(target=mqtt_worker, args=(i, chunk)) #
        t.daemon = True # 设置为守护线程
        t.start() # 启动线程
        threads.append(t) # 将线程添加到列表中
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序中断")
        for thread in threads:
            thread.join()
        print("所有线程完成")
        
if __name__ == "__main__":
    start_simulation()