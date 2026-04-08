#!/usr/bin/env python3
"""
设备网关采集器
从真实设备读取数据，转发到 MQTT

支持的协议：
- Modbus TCP/RTU
- HTTP API
- 串口通信

使用方法：
1. 安装依赖：pip install pymodbus paho-mqtt
2. 在 config/gateway_devices.json 中按类别添加设备（推荐），或使用代码内默认配置
3. 运行：python device_gateway.py
"""

import json
import time
import os
from datetime import datetime
import paho.mqtt.client as mqtt

# ================= 配置 =================

# MQTT 配置
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "campus_mqtt")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "campus_mqtt_secret_2026")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "campus/telemetry")

# 设备配置文件路径（可选）：环境变量 > 项目根 config/gateway_devices.json > 代码内默认
def _project_root():
    """脚本所在目录为 scripts/python，项目根为其上两级"""
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

def load_device_config():
    """
    从配置文件加载设备列表。配置文件按类别分组，便于维护。
    若文件不存在或解析失败，则使用代码内默认配置。
    返回：设备字典列表，与原先 DEVICE_CONFIG 格式一致。
    """
    config_path = os.getenv("GATEWAY_DEVICES_CONFIG")
    if not config_path:
        config_path = os.path.join(_project_root(), "config", "gateway_devices.json")
    if not os.path.isfile(config_path):
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ 读取配置文件失败 {config_path}: {e}，使用默认配置")
        return None
    categories = data.get("categories") or {}
    devices = []
    for cat_name, cat_value in categories.items():
        if cat_name.startswith("_"):
            continue
        if isinstance(cat_value, dict) and "devices" in cat_value:
            for d in cat_value["devices"]:
                if isinstance(d, dict):
                    devices.append(d)
    if not devices:
        return None
    return devices

# 代码内默认配置（无配置文件或配置为空时使用）
DEFAULT_DEVICE_CONFIG = [
    {
        "device_id": 11,
        "device_code": "METER001",
        "name": "智能电表",
        "protocol": "modbus_tcp",
        "host": "192.168.1.100",
        "port": 502,
        "slave_id": 1,
        "registers": {
            "voltage": {"address": 0x0000, "type": "float32"},
            "current": {"address": 0x0002, "type": "float32"},
            "power": {"address": 0x0004, "type": "float32"},
            "energy": {"address": 0x0006, "type": "float32"},
        }
    },
    {
        "device_id": 12,
        "device_code": "WATER001",
        "name": "水表",
        "protocol": "http",
        "url": "http://192.168.1.101/api/data",
        "field_mapping": {
            "flow_rate": "flowRate",
            "consumption": "totalVolume"
        }
    }
]

# 采集间隔（秒）
COLLECT_INTERVAL = 5

# ================= 协议实现 =================

def read_modbus_tcp(config):
    """从 Modbus TCP 设备读取数据"""
    try:
        from pymodbus.client import ModbusTcpClient
        from pymodbus.payload import BinaryPayloadDecoder
        from pymodbus.constants import Endian
        
        client = ModbusTcpClient(config['host'], port=config['port'])
        client.connect()
        
        data = {}
        registers = config.get('registers', {})
        
        for field, reg_config in registers.items():
            address = reg_config['address']
            reg_type = reg_config.get('type', 'uint16')
            
            # 读取寄存器
            result = client.read_holding_registers(address, 2, slave=config.get('slave_id', 1))
            
            if result.isError():
                print(f"⚠️ 读取 {field} 失败: {result}")
                continue
            
            # 解码数据
            decoder = BinaryPayloadDecoder.fromRegisters(
                result.registers, 
                byteorder=Endian.BIG, 
                wordorder=Endian.BIG
            )
            
            if reg_type == 'float32':
                data[field] = round(decoder.decode_32bit_float(), 2)
            elif reg_type == 'uint16':
                data[field] = decoder.decode_16bit_uint()
            elif reg_type == 'int16':
                data[field] = decoder.decode_16bit_int()
        
        client.close()
        return data
        
    except ImportError:
        print("❌ 请安装 pymodbus: pip install pymodbus")
        return None
    except Exception as e:
        print(f"❌ Modbus TCP 读取失败: {e}")
        return None


def read_http(config):
    """从 HTTP API 读取数据"""
    try:
        import requests
        
        response = requests.get(config['url'], timeout=5)
        if response.status_code == 200:
            raw_data = response.json()
            
            # 字段映射
            mapping = config.get('field_mapping', {})
            data = {}
            
            for our_field, their_field in mapping.items():
                if their_field in raw_data:
                    data[our_field] = raw_data[their_field]
            
            return data
        else:
            print(f"⚠️ HTTP 请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ HTTP 读取失败: {e}")
        return None


def read_device(config):
    """根据协议类型读取设备数据"""
    protocol = config.get('protocol', 'modbus_tcp')
    
    if protocol == 'modbus_tcp':
        return read_modbus_tcp(config)
    elif protocol == 'http':
        return read_http(config)
    else:
        print(f"⚠️ 不支持的协议: {protocol}")
        return None


# ================= 主程序 =================

def main():
    # 优先从配置文件加载设备，便于新增/修改设备而无需改代码
    DEVICE_CONFIG = load_device_config()
    if DEVICE_CONFIG is None:
        DEVICE_CONFIG = DEFAULT_DEVICE_CONFIG
        print("📋 使用代码内默认设备配置")
    else:
        print("📋 已从 config/gateway_devices.json 加载设备配置")

    print("=" * 60)
    print("   🔌 设备网关采集器")
    print(f"   MQTT: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"   设备数: {len(DEVICE_CONFIG)}")
    print("=" * 60)
    print()

    client = mqtt.Client()
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        print("✅ MQTT 连接成功")
    except Exception as e:
        print(f"❌ MQTT 连接失败: {e}")
        return

    print(f"🚀 开始采集，间隔 {COLLECT_INTERVAL} 秒...")
    print("-" * 60)

    try:
        while True:
            for config in DEVICE_CONFIG:
                device_id = config['device_id']
                device_code = config['device_code']
                device_name = config['name']
                
                # 读取设备数据
                sensor_data = read_device(config)
                
                if sensor_data:
                    # 构造 MQTT 消息
                    payload = {
                        "device_id": device_id,
                        "device_code": device_code,
                        "timestamp": time.time(),
                        **sensor_data
                    }
                    
                    # 发送到 MQTT
                    client.publish(MQTT_TOPIC, json.dumps(payload))
                    
                    print(f"📡 [{datetime.now().strftime('%H:%M:%S')}] "
                          f"{device_name}: {sensor_data}")
                else:
                    print(f"⚠️ [{datetime.now().strftime('%H:%M:%S')}] "
                          f"{device_name}: 读取失败")
            
            time.sleep(COLLECT_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n👋 网关已停止")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
