import random
import time
import requests

# 配置 API 地址
BASE_URL = "http://127.0.0.1:8088"
UPLOAD_URL = f"{BASE_URL}/telemetry/"
DEVICES_URL = f"{BASE_URL}/devices/"

# 目标设备 ID 列表
TARGET_DEVICES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# 设备基准配置
DEVICE_PROFILES = {
    1: (15.0, 2.0), 2: (90.0, 5.0), 3: (55.0, 5.0), 4: (180.0, 15.0), 5: (35.0, 3.0),
    6: (280.0, 40.0), 7: (100.0, 10.0), 8: (150.0, 50.0), 9: (70.0, 5.0), 10: (110.0, 15.0)
}

def generate_instant_data(device_id):
    """生成模拟的电压、电流、功率"""
    base_voltage = 220.0
    voltage = round(base_voltage + random.uniform(-3, 3), 1)
    
    profile = DEVICE_PROFILES.get(device_id, (20.0, 2.0))
    base_amp = profile[0]
    fluctuation = profile[1]
    
    current = round(base_amp + random.uniform(-fluctuation, fluctuation), 2)
    
    # 1% 几率模拟过载
    if random.randint(1, 100) > 99:
        current = current * 1.5
        print(f"⚠️ [模拟故障] 设备 {device_id} 电流激增!")

    power = round((voltage * current) / 1000, 3)
    return voltage, current, power

def start_simulation():
    print(f"--- 启动全矿井设备模拟器 (智能联动版) ---")
    print(f"数据中心: {BASE_URL}")
    
    device_energies = {id: 0.0 for id in TARGET_DEVICES}

    while True:
        try:
            # 👇👇👇 核心修改：每轮循环前，先去问问后端哪些设备是开着的 👇👇👇
            online_map = {}
            try:
                # 请求后端获取设备列表
                res = requests.get(DEVICES_URL, timeout=1)
                if res.status_code == 200:
                    devices = res.json()
                    # 建立一个字典: {1: True, 2: False, ...}
                    online_map = {d['id']: d['is_active'] for d in devices}
            except Exception:
                # 如果连不上后端，默认全开，或者报错
                pass

            for dev_id in TARGET_DEVICES:
                # 1. 检查状态：如果后端说这台设备关了，或者没找到这台设备
                # 默认值给 True (防止刚启动没读到就全停了)，但如果读到了是 False，就停机
                is_running = online_map.get(dev_id, True)

                if not is_running:
                    # 🛑 如果是停机状态，跳过数据生成，直接进行下一个循环
                    # 只有偶尔打印日志，证明模拟器知道它停了
                    if random.random() > 0.98: 
                        print(f"[ID:{dev_id:<2}] 💤 已停机 (静默中...)")
                    continue

                # 2. 如果是运行状态，正常生成数据
                v, c, p = generate_instant_data(dev_id)
                device_energies[dev_id] += p * (1 / 3600)

                payload = {
                    "device_id": dev_id,
                    "voltage": v,
                    "current": c,
                    "power": p,
                    "energy": round(device_energies[dev_id], 4)
                }

                # 发送数据
                res = requests.post(UPLOAD_URL, json=payload, timeout=1)
                
                if res.status_code == 200:
                    # 只打印部分日志
                    if dev_id in [6] or random.random() > 0.9:
                        print(f"[ID:{dev_id:<2}] ✅ 运行中 | 电流: {c:>5}A | 功率: {p:>6}kW")

        except Exception as e:
            print(f"[连接错误] {e}")
            time.sleep(2)

        # 休息 1 秒进入下一轮
        time.sleep(1)

if __name__ == "__main__":
    start_simulation()