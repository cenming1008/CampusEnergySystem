#!/usr/bin/env python3
"""
统一多能源模拟器 v2.2
- 自动从数据库获取设备列表
- 支持多种能源类型（电、水、气、热、冷）
- 根据设备类型生成相应的遥测数据
"""

import random
import time
import json
import requests
import paho.mqtt.client as mqtt
import os
from datetime import datetime

# ================= 配置 =================
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_TELEMETRY = "mine/telemetry"

API_BASE = os.getenv("API_BASE", "http://localhost:8088")
LOGIN_URL = f"{API_BASE}/auth/login"
DEVICES_URL = f"{API_BASE}/devices/"

# 管理员账号
ADMIN_USER = "admin"
ADMIN_PASS = "123456"

# 全局变量
current_token = None
devices_cache = []
device_states = {}
device_energies = {}

# ================= 登录和设备获取 =================

def login():
    """登录获取 Token"""
    global current_token
    print(f"🔑 正在登录 ({ADMIN_USER})...", flush=True)
    try:
        response = requests.post(
            LOGIN_URL, 
            data={"username": ADMIN_USER, "password": ADMIN_PASS},
            timeout=5
        )
        if response.status_code == 200:
            current_token = response.json().get("access_token")
            print("✅ 登录成功！", flush=True)
            return True
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}", flush=True)
            return False
    except Exception as e:
        print(f"❌ 登录失败: {e}", flush=True)
        return False

def fetch_devices():
    """从 API 获取设备列表"""
    global devices_cache, device_states, device_energies
    
    if not current_token:
        print("⚠️ 未登录，无法获取设备列表", flush=True)
        return False
    
    try:
        headers = {"Authorization": f"Bearer {current_token}"}
        response = requests.get(DEVICES_URL, headers=headers, timeout=5)
        
        if response.status_code == 200:
            devices_cache = response.json()
            print(f"\n📋 获取到 {len(devices_cache)} 个设备：", flush=True)
            
            for device in devices_cache:
                dev_id = device['id']
                device_states[dev_id] = device.get('is_active', True)
                device_energies[dev_id] = 0.0
                
                print(f"  • ID:{dev_id:2d} | {device['name']:15s} | "
                      f"类型:{device['device_type']:12s} | "
                      f"能源:{device['energy_type']}", flush=True)
            
            print(f"\n", flush=True)
            return True
        else:
            print(f"❌ 获取设备失败: {response.status_code}", flush=True)
            return False
    except Exception as e:
        print(f"❌ 获取设备失败: {e}", flush=True)
        return False

# ================= 数据生成逻辑 =================

def generate_electricity_data(device, is_active):
    """生成电力设备数据（电压、电流、功率）"""
    if not is_active:
        return {"voltage": 0.0, "current": 0.0, "power": 0.0}
    
    dev_id = device['id']
    device_type = device.get('device_type', 'load')
    
    # 根据设备类型设置不同的基准值
    if device_type == 'solar':
        # 光伏：电压稳定，电流波动大（受光照影响）
        voltage = round(220.0 + random.uniform(-2, 2), 1)
        current = round(random.uniform(5, 30), 2)  # 光照影响
    elif device_type == 'wind':
        # 风机：功率波动大
        voltage = round(220.0 + random.uniform(-3, 3), 1)
        current = round(random.uniform(10, 50), 2)  # 风速影响
    elif device_type == 'storage':
        # 储能：充放电切换
        voltage = round(220.0 + random.uniform(-1, 1), 1)
        current = round(random.uniform(-20, 20), 2)  # 负值=充电
        soc = round(random.uniform(20, 90), 1)  # 荷电状态 20-90%
    elif device_type == 'charger':
        # 充电桩
        voltage = round(220.0 + random.uniform(-2, 2), 1)
        current = round(random.uniform(0, 32), 2)  # 7kW充电桩
    else:
        # 负载类设备（默认）
        voltage = round(220.0 + random.uniform(-5, 5), 1)
        base_current = 10.0 + (dev_id * 5)
        current = round(base_current + random.uniform(-2, 2), 2)
    
    # 功率计算
    power = round((voltage * current) / 1000, 3)
    
    result = {
        "voltage": voltage,
        "current": current,
        "power": power
    }
    
    # 为储能设备添加 soc
    if device_type == 'storage':
        result["soc"] = soc
    
    return result

def generate_water_data(device, is_active):
    """生成水表数据（流量）"""
    if not is_active:
        return {"flow_rate": 0.0}
    
    # 流量 (m³/h)
    flow_rate = round(random.uniform(0.5, 5.0), 2)
    
    return {
        "flow_rate": flow_rate,
        "power": flow_rate  # 用 power 字段存储主要指标
    }

def generate_gas_data(device, is_active):
    """生成燃气表数据（流量）"""
    if not is_active:
        return {"flow_rate": 0.0}
    
    # 流量 (m³/h)
    flow_rate = round(random.uniform(1.0, 10.0), 2)
    
    return {
        "flow_rate": flow_rate,
        "power": flow_rate
    }

def generate_heat_data(device, is_active):
    """生成热量表数据（热功率）"""
    if not is_active:
        return {"heat_power": 0.0, "temperature": 20.0}
    
    # 热功率 (kW)
    heat_power = round(random.uniform(50, 200), 1)
    # 供回水温度
    supply_temp = round(random.uniform(65, 85), 1)
    return_temp = round(supply_temp - random.uniform(5, 15), 1)
    
    return {
        "heat_power": heat_power,
        "supply_temperature": supply_temp,
        "return_temperature": return_temp,
        "power": heat_power
    }

def generate_cooling_data(device, is_active):
    """生成冷量表数据（冷功率）"""
    if not is_active:
        return {"cooling_power": 0.0, "flow_rate": 0.0}
    
    # 冷功率 (kW)
    cooling_power = round(random.uniform(100, 300), 1)
    # 流量 (m³/h) - 冷量表需要流量
    flow_rate = round(random.uniform(10, 50), 1)
    # 冷冻水温度
    supply_temp = round(random.uniform(5, 10), 1)
    return_temp = round(supply_temp + random.uniform(3, 8), 1)
    
    return {
        "cooling_power": cooling_power,
        "flow_rate": flow_rate,
        "supply_temperature": supply_temp,
        "return_temperature": return_temp,
        "power": cooling_power  # power 作为备份
    }

def generate_steam_data(device, is_active):
    """生成蒸汽表数据（流量）"""
    if not is_active:
        return {"flow_rate": 0.0}
    
    # 流量 (t/h)
    flow_rate = round(random.uniform(0.5, 5.0), 2)
    # 压力 (MPa)
    pressure = round(random.uniform(0.5, 2.0), 2)
    # 温度 (℃)
    temperature = round(random.uniform(150, 300), 1)
    
    return {
        "flow_rate": flow_rate,
        "pressure": pressure,
        "temperature": temperature,
        "power": flow_rate  # power 作为备份
    }

def generate_device_data(device, is_active):
    """根据设备能源类型生成相应数据"""
    energy_type = device.get('energy_type', 'electricity')
    
    # 根据能源类型调用对应的生成函数
    if energy_type == 'electricity':
        return generate_electricity_data(device, is_active)
    elif energy_type == 'water':
        return generate_water_data(device, is_active)
    elif energy_type == 'gas':
        return generate_gas_data(device, is_active)
    elif energy_type == 'heat':
        return generate_heat_data(device, is_active)
    elif energy_type == 'cooling':
        return generate_cooling_data(device, is_active)
    elif energy_type == 'steam':
        return generate_steam_data(device, is_active)
    else:
        # 未知类型，返回基本数据
        return {"power": round(random.uniform(10, 100), 2)}

# ================= MQTT 回调 =================

def on_connect(client, userdata, flags, rc):
    """MQTT 连接成功"""
    if rc == 0:
        print("✅ MQTT 连接成功！")
    else:
        print(f"❌ MQTT 连接失败: {rc}")

# ================= 主程序 =================

def start_simulation():
    print("=" * 60, flush=True)
    print("   🏭 煤矿综合能源管理系统 - 统一模拟器 v2.2", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)
    
    # 1. 登录
    if not login():
        print("❌ 无法启动模拟器：登录失败", flush=True)
        return
    
    # 2. 获取设备列表
    if not fetch_devices():
        print("❌ 无法启动模拟器：获取设备失败", flush=True)
        return
    
    if not devices_cache:
        print("⚠️ 数据库中没有设备，请先创建设备", flush=True)
        print("   运行: python scripts/python/init_complete_system.py", flush=True)
        return
    
    # 3. 连接 MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    
    try:
        print(f"🔌 正在连接 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}...", flush=True)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        time.sleep(2)  # 等待连接建立
        print(f"✅ MQTT 连接成功！", flush=True)
        print(flush=True)
    except Exception as e:
        print(f"❌ MQTT 连接失败: {e}", flush=True)
        return
    
    # 4. 主循环
    print("🚀 开始生成遥测数据...", flush=True)
    print("   按 Ctrl+C 停止", flush=True)
    print("-" * 60, flush=True)
    
    loop_count = 0
    
    try:
        while True:
            current_time = time.time()
            
            # 每 30 秒重新获取一次设备列表（检测新增设备）
            if loop_count % 30 == 0 and loop_count > 0:
                fetch_devices()
            
            # 遍历所有设备生成数据
            for device in devices_cache:
                dev_id = device['id']
                is_active = device_states.get(dev_id, True)
                
                # 生成设备数据
                sensor_data = generate_device_data(device, is_active)
                
                # 累加能耗（如果有 power 字段）
                if is_active and 'power' in sensor_data:
                    power = abs(sensor_data['power'])
                    device_energies[dev_id] += power * (1 / 3600)  # kWh or 其他单位
                
                # 构造 MQTT 消息
                payload = {
                    "device_id": dev_id,
                    "device_code": device.get('sn', f"DEV{dev_id:03d}"),
                    "timestamp": current_time,
                    "energy": round(device_energies[dev_id], 4),
                    **sensor_data  # 合并传感器数据
                }
                
                # 发送到 MQTT
                client.publish(MQTT_TOPIC_TELEMETRY, json.dumps(payload))
                
                # 打印部分日志（每个能源类型打印一个）
                if loop_count % 5 == 0:  # 每5秒打印一次
                    energy_type = device.get('energy_type', 'unknown')
                    status = "🟢" if is_active else "🔴"
                    
                    # 根据能源类型格式化输出
                    if energy_type == 'electricity' and 'voltage' in sensor_data:
                        detail = f"U:{sensor_data['voltage']}V I:{sensor_data['current']}A P:{sensor_data['power']}kW"
                    elif 'power' in sensor_data:
                        detail = f"P:{sensor_data['power']:.2f}"
                    else:
                        detail = "数据已发送"
                    
                    print(f"📡 [{datetime.now().strftime('%H:%M:%S')}] "
                          f"ID:{dev_id:2d} {status} {device['name']:15s} | {detail}", flush=True)
            
            loop_count += 1
            time.sleep(3)  # 每3秒发送一轮数据
    
    except KeyboardInterrupt:
        print("\n")
        print("=" * 60)
        print("👋 模拟器已停止")
        print(f"📊 总计运行 {loop_count} 轮，发送了 {loop_count * len(devices_cache)} 条消息")
        print("=" * 60)
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    start_simulation()
