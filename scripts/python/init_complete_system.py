#!/usr/bin/env python3
"""
完整系统初始化脚本 v2.2
- 创建完整的设备数据
- 生成正确格式的遥测数据
- 所有字段与数据库模型完全匹配
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import random
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.core.database import engine
from app.models.tables import Device, EnergyData, User
from app.core.security import get_password_hash
from app.core.logger import logger


def create_admin():
    """创建管理员账户"""
    logger.info("👤 创建管理员账户...")
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    if not admin_password:
        logger.warning("  ⚠️ 未设置 ADMIN_PASSWORD 环境变量，使用临时密码（请尽快修改！）")
        admin_password = "change-me-immediately-2026!"
    with Session(engine) as session:
        stmt = select(User).where(User.username == "admin")
        existing = session.exec(stmt).first()
        if existing:
            logger.info("  ✅ 管理员已存在")
            return
        
        admin = User(
            username="admin",
            hashed_password=get_password_hash(admin_password),
            role="admin",
            is_active=True,
            must_change_password=True,
        )
        session.add(admin)
        session.commit()
        logger.info("  ✅ 管理员创建成功（首次登录需改密）")


def create_devices():
    """创建完整的设备列表"""
    logger.info("\n📦 创建设备...")
    
    devices_config = [
        # 电力设备
        {
            "name": "1号配电柜",
            "sn": "LOAD001",
            "device_type": "load",
            "device_category": "load",
            "energy_type": "electricity",
            "location": "A栋配电室",
            "description": "主配电柜，负责整栋楼供电",
            "rated_capacity": 500.0,
            "unit": "kW",
            "is_active": True
        },
        {
            "name": "屋顶光伏阵列",
            "sn": "SOLAR001",
            "device_type": "solar",
            "device_category": "solar",
            "energy_type": "electricity",
            "location": "A栋屋顶",
            "description": "20kW分布式光伏发电系统",
            "rated_capacity": 20.0,
            "unit": "kW",
            "is_active": True
        },
        {
            "name": "储能柜A",
            "sn": "STORAGE001",
            "device_type": "storage",
            "device_category": "storage",
            "energy_type": "electricity",
            "location": "储能室",
            "description": "50kWh储能系统",
            "rated_capacity": 50.0,
            "unit": "kWh",
            "is_active": True
        },
        {
            "name": "1号充电桩",
            "sn": "CHARGER001",
            "device_type": "charger",
            "device_category": "charger",
            "energy_type": "electricity",
            "location": "地下停车场",
            "description": "7kW交流充电桩",
            "rated_capacity": 7.0,
            "unit": "kW",
            "is_active": True
        },
        
        # 水表
        {
            "name": "1号水表",
            "sn": "WATER001",
            "device_type": "water_meter",
            "device_category": "water_meter",
            "energy_type": "water",
            "location": "A栋1层水泵房",
            "description": "生活用水总表",
            "rated_capacity": 50.0,
            "unit": "m³/h",
            "is_active": True
        },
        {
            "name": "2号水表",
            "sn": "WATER002",
            "device_type": "water_meter",
            "device_category": "water_meter",
            "energy_type": "water",
            "location": "B栋1层水泵房",
            "description": "B栋用水总表",
            "rated_capacity": 30.0,
            "unit": "m³/h",
            "is_active": True
        },
        
        # 燃气表
        {
            "name": "1号燃气表",
            "sn": "GAS001",
            "device_type": "gas_meter",
            "device_category": "gas_meter",
            "energy_type": "gas",
            "location": "锅炉房",
            "description": "供暖锅炉燃气表",
            "rated_capacity": 100.0,
            "unit": "m³/h",
            "is_active": True
        },
        {
            "name": "2号燃气表",
            "sn": "GAS002",
            "device_type": "gas_meter",
            "device_category": "gas_meter",
            "energy_type": "gas",
            "location": "食堂",
            "description": "食堂用气表",
            "rated_capacity": 20.0,
            "unit": "m³/h",
            "is_active": True
        },
        
        # 热量表
        {
            "name": "1号热量表",
            "sn": "HEAT001",
            "device_type": "heat_meter",
            "device_category": "heat_meter",
            "energy_type": "heat",
            "location": "换热站",
            "description": "集中供暖热量计量",
            "rated_capacity": 10.0,
            "unit": "GJ/h",
            "is_active": True
        },
        
        # 冷量表
        {
            "name": "中央空调冷量表",
            "sn": "COOLING001",
            "device_type": "cooling_meter",
            "device_category": "cooling_meter",
            "energy_type": "cooling",
            "location": "制冷机房",
            "description": "中央空调系统冷量计量",
            "rated_capacity": 200.0,
            "unit": "kW",
            "is_active": True
        },
    ]
    
    created_devices = []
    with Session(engine) as session:
        for dev_config in devices_config:
            # 检查是否已存在
            stmt = select(Device).where(Device.sn == dev_config["sn"])
            existing = session.exec(stmt).first()
            if existing:
                logger.info(f"  ⏭️  设备已存在: {dev_config['name']}")
                created_devices.append(existing)
                continue
            
            # 创建设备
            device = Device(**dev_config)
            session.add(device)
            session.commit()
            session.refresh(device)
            created_devices.append(device)
            logger.info(f"  ✅ 创建设备: {device.name} (ID:{device.id}, 类型:{device.energy_type})")
    
    logger.info(f"\n✅ 共有 {len(created_devices)} 个设备")
    return created_devices


def generate_energy_data(device: Device, base_time: datetime) -> dict:
    """
    根据设备类型生成正确格式的能源数据
    返回的字典键名必须与 EnergyData 模型字段完全匹配
    """
    energy_type = device.energy_type
    
    # 基础数据（所有设备必需）
    data = {
        "device_id": device.id,
        "timestamp": base_time,
        "energy_type": energy_type,
        "consumption": round(random.uniform(100, 1000), 2),  # 累计消耗量（必填）
    }
    
    # 根据能源类型添加专用字段
    if energy_type == "electricity":
        data.update({
            "flow_rate": round(random.uniform(5, 50), 2),  # 瞬时功率 kW
            "voltage": round(random.uniform(215, 225), 1),  # 电压 V
            "current": round(random.uniform(10, 100), 2),  # 电流 A
            "power_factor": round(random.uniform(0.85, 0.99), 2),  # 功率因数
        })
    
    elif energy_type == "water":
        data.update({
            "flow_rate": round(random.uniform(1, 10), 2),  # 瞬时流量 m³/h
            "pressure": round(random.uniform(0.2, 0.4), 2),  # 压力 MPa
            "temperature": round(random.uniform(15, 25), 1),  # 温度 ℃
        })
    
    elif energy_type == "gas":
        data.update({
            "flow_rate": round(random.uniform(5, 20), 2),  # 瞬时流量 m³/h
            "pressure": round(random.uniform(0.1, 0.3), 2),  # 压力 MPa
            "temperature": round(random.uniform(10, 20), 1),  # 温度 ℃
        })
    
    elif energy_type == "heat":
        supply_temp = round(random.uniform(65, 85), 1)
        return_temp = round(supply_temp - random.uniform(10, 20), 1)
        data.update({
            "flow_rate": round(random.uniform(10, 30), 2),  # 瞬时流量 m³/h
            "heat_flow": round(random.uniform(1, 5), 2),  # 热流量 GJ/h
            "supply_temp": supply_temp,  # 供水温度 ℃
            "return_temp": return_temp,  # 回水温度 ℃
            "pressure": round(random.uniform(0.3, 0.5), 2),  # 压力 MPa
        })
    
    elif energy_type == "cooling":
        supply_temp = round(random.uniform(5, 10), 1)
        return_temp = round(supply_temp + random.uniform(5, 10), 1)
        data.update({
            "flow_rate": round(random.uniform(100, 300), 2),  # 冷功率 kW
            "supply_temp": supply_temp,  # 供水温度 ℃
            "return_temp": return_temp,  # 回水温度 ℃
            "pressure": round(random.uniform(0.2, 0.4), 2),  # 压力 MPa
        })
    
    return data


def create_initial_data():
    """为所有设备创建初始遥测数据"""
    logger.info("\n📊 创建初始遥测数据...")
    
    base_time = datetime.now()
    total_count = 0
    
    with Session(engine) as session:
        # 重新获取设备列表（在当前session中）
        devices = session.exec(select(Device)).all()
        
        for device in devices:
            # 为每个设备创建3条历史数据
            for i in range(3):
                timestamp = base_time - timedelta(minutes=i*10)
                data_dict = generate_energy_data(device, timestamp)
                
                # 创建 EnergyData 对象
                energy_data = EnergyData(**data_dict)
                session.add(energy_data)
                total_count += 1
            
            logger.info(f"  ✅ {device.name:20s} - 已创建 3 条数据")
        
        session.commit()
    
    logger.info(f"\n✅ 共创建 {total_count} 条遥测数据")


def verify_system():
    """验证系统数据"""
    logger.info("\n🔍 验证系统...")
    
    with Session(engine) as session:
        # 统计设备
        devices = session.exec(select(Device)).all()
        logger.info(f"  • 设备总数: {len(devices)}")
        
        # 按能源类型统计
        energy_types = {}
        for device in devices:
            energy_types[device.energy_type] = energy_types.get(device.energy_type, 0) + 1
        
        for energy_type, count in sorted(energy_types.items()):
            logger.info(f"    - {energy_type}: {count} 个")
        
        # 统计数据
        data_count = session.exec(select(EnergyData)).all()
        logger.info(f"  • 遥测数据: {len(data_count)} 条")
        
        # 检查最新数据时间
        latest = session.exec(
            select(EnergyData).order_by(EnergyData.timestamp.desc())
        ).first()
        if latest:
            logger.info(f"  • 最新数据时间: {latest.timestamp}")


def main():
    logger.info("=" * 60)
    logger.info("  🏭 园区综合能源管理系统 - 完整初始化")
    logger.info("=" * 60)
    
    try:
        # 1. 创建管理员
        create_admin()
        
        # 2. 创建设备
        create_devices()
        
        # 3. 创建初始数据
        create_initial_data()
        
        # 4. 验证
        verify_system()
        
        logger.info("\n" + "=" * 60)
        logger.info("  ✨ 系统初始化完成！")
        logger.info("=" * 60)
        logger.info("\n下一步:")
        logger.info("  1. 启动后端: python run.py")
        logger.info("  2. 启动模拟器: python scripts/python/simulator_unified.py")
        logger.info("  3. 启动前端: cd frontend && npm run dev")
        logger.info("  4. 登录系统: admin / <ADMIN_PASSWORD 环境变量值>")
        logger.info("")
        
    except Exception as e:
        logger.error(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
