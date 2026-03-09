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
2. 配置 DEVICE_CONFIG 中的设备信息
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
MQTT_TOPIC = "mine/telemetry"

# 设备配置列表
# 根据你的实际设备修改这里
DEVICE_CONFIG = [
    {
        "device_id": 11,          # 数据库中的设备 ID
        "device_code": "METER001", # 设备序列号
        "name": "智能电表",
        "protocol": "modbus_tcp",  # 协议类型: modbus_tcp, modbus_rtu, http, serial
        "host": "192.168.1.100",   # 设备 IP（Modbus TCP）
        "port": 502,               # 端口
        "slave_id": 1,             # Modbus 从站地址
        "registers": {             # 寄存器映射
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
        "url": "http://192.168.1.101/api/data",  # 设备 HTTP 接口
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
    print("=" * 60)
    print("   🔌 设备网关采集器")
    print(f"   MQTT: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"   设备数: {len(DEVICE_CONFIG)}")
    print("=" * 60)
    print()
    
    # 连接 MQTT
    client = mqtt.Client()
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
