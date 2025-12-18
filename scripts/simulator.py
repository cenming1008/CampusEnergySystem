import random
import time
import requests

# ================= 配置区域 =================

# 后端服务的基础地址
# 注意：如果模拟器在 Docker 外部运行，使用 127.0.0.1
# 如果在 Docker 内部运行，可能需要改为 http://web:8088
BASE_URL = "http://127.0.0.1:8088"

# 1. 遥测数据上传接口 (POST)
UPLOAD_URL = f"{BASE_URL}/telemetry/"

# 2. 设备列表接口 (GET) - 用于判断设备是否开机
DEVICES_URL = f"{BASE_URL}/devices/"

# 3. 历史数据接口 (GET) - 用于启动时同步最新的能耗值
# 格式：/telemetry/{id}?limit=1 (只取最后一条)
HISTORY_URL_TEMPLATE = "{base}/telemetry/{id}?limit=1"

# 目标设备 ID 列表 (覆盖 1-10 号设备)
TARGET_DEVICES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# 设备基准配置 {ID: (基准电流A, 波动范围A)}
# 这些值设置得比 settings.json 的阈值低，保证正常运行，偶尔触发报警
DEVICE_PROFILES = {
    1: (15.0, 2.0),   # 智能电表 (阈值25)
    2: (90.0, 5.0),   # 主通风机 (阈值120)
    3: (55.0, 5.0),   # 排水泵 (阈值80)
    4: (180.0, 15.0), # 变压器 (阈值300)
    5: (35.0, 3.0),   # 瓦斯泵 (阈值60)
    6: (280.0, 40.0), # 采煤机 (阈值400) - 功率大
    7: (100.0, 10.0), # 皮带机 (阈值150)
    8: (150.0, 50.0), # 提升机 (阈值250)
    9: (70.0, 5.0),   # 压风机 (阈值100)
    10: (110.0, 15.0) # 刮板机 (阈值180)
}

def generate_instant_data(device_id):
    """
    生成模拟的电压、电流、功率
    """
    # 1. 模拟电压：220V 左右微小波动
    base_voltage = 220.0
    voltage = round(base_voltage + random.uniform(-3, 3), 1)
    
    # 2. 模拟电流：基准值 + 随机波动
    profile = DEVICE_PROFILES.get(device_id, (20.0, 2.0))
    base_amp = profile[0]
    fluctuation = profile[1]
    current = round(base_amp + random.uniform(-fluctuation, fluctuation), 2)
    
    # 3. 模拟随机故障：1% 的概率电流激增 (触发后端报警)
    if random.randint(1, 100) > 99:
        current = current * 1.5
        print(f"⚠️ [模拟故障] 设备 {device_id} 电流激增至 {current:.2f}A!")

    # 4. 计算功率 (kW)
    power = round((voltage * current) / 1000, 3)
    return voltage, current, power

def start_simulation():
    print(f"--- 启动全矿井设备模拟器 (智能联动修正版) ---")
    print(f"数据中心地址: {BASE_URL}")
    print("-" * 50)
    
    # ================= 阶段 1: 同步历史数据 =================
    # 目的：防止模拟器重启后，能耗从 0 开始计数，导致前端图表断崖式下跌
    
    device_energies = {} # 存储每个设备的累积能耗
    
    print("🔄 正在从数据库同步历史能耗...")
    for dev_id in TARGET_DEVICES:
        try:
            # 拼接 URL: http://127.0.0.1:8088/telemetry/1?limit=1
            url = HISTORY_URL_TEMPLATE.format(base=BASE_URL, id=dev_id)
            res = requests.get(url, timeout=2)
            
            if res.status_code == 200:
                history_list = res.json()
                if history_list and len(history_list) > 0:
                    # 后端返回的数据是按时间正序排列的 (旧 -> 新)
                    # 所以列表的最后一个元素 [-1] 就是最新的数据
                    last_record = history_list[-1]
                    last_energy = float(last_record.get("energy", 0.0))
                    
                    device_energies[dev_id] = last_energy
                    print(f"  ✅ [已同步] 设备 {dev_id:<2} | 初始能耗: {last_energy:.4f} kWh")
                else:
                    # 如果列表为空，说明是新设备，从 0 开始
                    device_energies[dev_id] = 0.0
                    print(f"  🆕 [新设备] 设备 {dev_id:<2} | 初始能耗: 0.0000 kWh")
            else:
                # 接口报错，为了安全起见归零
                device_energies[dev_id] = 0.0
                print(f"  ❌ [同步失败] 设备 {dev_id:<2} (API返回 {res.status_code}) -> 重置为 0")
        
        except Exception as e:
            device_energies[dev_id] = 0.0
            print(f"  ❌ [连接错误] 设备 {dev_id:<2} ({e}) -> 重置为 0")
            
    print("-" * 50)
    print("🚀 同步完成，开始数据上传循环...\n")

    # ================= 阶段 2: 循环模拟上传 =================
    
    while True:
        try:
            # 1. 获取全场设备的在线状态 (智能联动)
            # 只有后端显示 "Running" (is_active=True) 的设备，模拟器才发数据
            online_map = {}
            try:
                res = requests.get(DEVICES_URL, timeout=1)
                if res.status_code == 200:
                    devices = res.json()
                    # 生成字典: {1: True, 2: False, ...}
                    online_map = {d['id']: d['is_active'] for d in devices}
            except Exception:
                # 如果获取列表失败（比如后端短暂重启），默认所有设备都运行，防止模拟中断
                pass

            for dev_id in TARGET_DEVICES:
                # 2. 检查是否停机
                # 如果后端查不到这个ID，默认视为运行中(True)
                is_running = online_map.get(dev_id, True)

                if not is_running:
                    # 停机状态：跳过，不产生能耗，不上传数据
                    # 5% 的概率打印日志，证明它还活着但休息了
                    if random.random() > 0.95: 
                        print(f"💤 [ID:{dev_id:<2}] 设备已停机 (等待启动...)")
                    continue

                # 3. 运行状态：生成数据
                v, c, p = generate_instant_data(dev_id)
                
                # 累加能耗 (模拟每 1 秒的数据)
                # 公式: 功率(kW) * 时间(h) = kWh -> 1秒 = 1/3600 小时
                device_energies[dev_id] += p * (1 / 3600)

                payload = {
                    "device_id": dev_id,
                    "voltage": v,
                    "current": c,
                    "power": p,
                    "energy": round(device_energies[dev_id], 4) # 保留4位小数
                }

                # 4. 发送数据
                res = requests.post(UPLOAD_URL, json=payload, timeout=1)
                
                # 5. 日志输出 (带错误检测)
                if res.status_code == 200:
                    # 成功：为了防止刷屏，只打印部分日志
                    # 采煤机(6)、提升机(8) 每次都打印，其他设备 10% 概率打印
                    if dev_id in [6, 8] or random.random() > 0.9:
                        print(f"✅ [ID:{dev_id:<2}] 上传OK | 电流: {c:>6.2f}A | 功率: {p:>6.2f}kW | 总能耗: {payload['energy']:.2f}")
                else:
                    # 失败：必须打印！
                    print(f"❌ [ID:{dev_id:<2}] 上传失败! 状态码: {res.status_code}")
                    print(f"   错误详情: {res.text}")

        except Exception as e:
            print(f"⚠️ [主循环异常] {e}")
            time.sleep(2) # 出错后多休息一下

        # 全局循环间隔 1 秒
        time.sleep(1)

if __name__ == "__main__":
    start_simulation()