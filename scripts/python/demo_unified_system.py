#!/usr/bin/env python3
"""
统一设备管理系统演示脚本

展示新的统一架构：
1. 智能创建各类设备
2. 统一的数据上报接口
3. 自动分类和处理

执行方式:
    python scripts/python/demo_unified_system.py
"""

import sys
import random
from pathlib import Path
from datetime import datetime, timedelta
from sqlmodel import Session
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import engine
from app.services.device_service import DeviceService
from app.services.energy_service import EnergyService


def demo_create_devices(session: Session):
    """演示：智能创建各类设备"""
    logger.info("=" * 60)
    logger.info("📦 演示 1: 智能创建设备")
    logger.info("=" * 60)
    
    # 定义要创建的设备
    devices_to_create = [
        {
            "name": "1号配电柜",
            "sn": "LOAD001",
            "device_type": "load",
            "location": "A栋配电室",
            "rated_capacity": 150.0
        },
        {
            "name": "屋顶光伏阵列A",
            "sn": "SOLAR001",
            "device_type": "solar",
            "location": "A栋屋顶",
            "rated_capacity": 100.0
        },
        {
            "name": "1号水表",
            "sn": "WATER001",
            "device_type": "water_meter",
            "location": "A栋1层",
            "rated_capacity": 50.0
        },
        {
            "name": "1号燃气表",
            "sn": "GAS001",
            "device_type": "gas_meter",
            "location": "锅炉房",
            "rated_capacity": 100.0
        },
        {
            "name": "1号热量表",
            "sn": "HEAT001",
            "device_type": "heat_meter",
            "location": "供暖系统",
            "rated_capacity": 10.0
        },
        {
            "name": "1号冷量表",
            "sn": "COOLING001",
            "device_type": "cooling_meter",
            "location": "中央空调",
            "rated_capacity": 200.0
        },
        {
            "name": "储能柜A",
            "sn": "STORAGE001",
            "device_type": "storage",
            "location": "储能室",
            "rated_capacity": 500.0
        },
        {
            "name": "1号充电桩",
            "sn": "CHARGER001",
            "device_type": "charger",
            "location": "停车场A区",
            "rated_capacity": 60.0
        }
    ]
    
    created_devices = []
    
    for device_data in devices_to_create:
        logger.info(f"\n📝 创建设备: {device_data['name']} (类型: {device_data['device_type']})")
        
        try:
            device = DeviceService.create_device_smart(
                session=session,
                **device_data
            )
            
            logger.info(f"  ✅ 创建成功!")
            logger.info(f"     - ID: {device.id}")
            logger.info(f"     - 能源类型: {device.energy_type}")
            logger.info(f"     - 设备类别: {device.device_category}")
            logger.info(f"     - 单位: {device.unit}")
            logger.info(f"     - 额定容量: {device.rated_capacity} {device.unit}")
            
            created_devices.append(device)
            
        except Exception as e:
            logger.error(f"  ❌ 创建失败: {e}")
    
    logger.info(f"\n✅ 共创建 {len(created_devices)} 个设备")
    
    return created_devices


def demo_report_data(session: Session, devices: list):
    """演示：统一的数据上报接口"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 演示 2: 统一数据上报")
    logger.info("=" * 60)
    
    # 为每个设备生成并上报测试数据
    for device in devices:
        logger.info(f"\n📡 上报数据: {device.name} (类型: {device.device_type})")
        
        # 根据设备类型生成不同的数据
        data = generate_sample_data(device.device_type)
        
        try:
            energy_data = DeviceService.report_device_data(
                session=session,
                device_id=device.id,
                data=data
            )
            
            logger.info(f"  ✅ 上报成功!")
            logger.info(f"     - 消耗量: {energy_data.consumption}")
            logger.info(f"     - 瞬时值: {energy_data.flow_rate}")
            
            # 显示特殊字段
            if energy_data.voltage:
                logger.info(f"     - 电压: {energy_data.voltage} V")
            if energy_data.pressure:
                logger.info(f"     - 压力: {energy_data.pressure} MPa")
            if energy_data.temperature:
                logger.info(f"     - 温度: {energy_data.temperature} ℃")
                
        except Exception as e:
            logger.error(f"  ❌ 上报失败: {e}")
    
    logger.info(f"\n✅ 所有设备数据上报完成")


def generate_sample_data(device_type: str) -> dict:
    """根据设备类型生成样本数据"""
    
    base_consumption = random.uniform(10, 100)
    
    if device_type in ["load", "solar", "wind", "storage", "charger"]:
        # 电力设备
        return {
            "consumption": base_consumption,
            "power": random.uniform(10, 50),
            "voltage": random.uniform(215, 225),
            "current": random.uniform(10, 20),
            "power_factor": random.uniform(0.9, 1.0)
        }
    
    elif device_type == "water_meter":
        # 水表
        return {
            "consumption": base_consumption,
            "flow_rate": random.uniform(1, 5),
            "pressure": random.uniform(0.2, 0.4),
            "temperature": random.uniform(15, 25)
        }
    
    elif device_type == "gas_meter":
        # 燃气表
        return {
            "consumption": base_consumption,
            "flow_rate": random.uniform(5, 15),
            "pressure": random.uniform(0.1, 0.3),
            "temperature": random.uniform(10, 20)
        }
    
    elif device_type == "heat_meter":
        # 热量表
        return {
            "consumption": base_consumption,
            "heat_flow": random.uniform(1, 5),
            "supply_temp": random.uniform(60, 80),
            "return_temp": random.uniform(40, 60),
            "flow_rate": random.uniform(10, 30),
            "pressure": random.uniform(0.3, 0.5)
        }
    
    elif device_type == "cooling_meter":
        # 冷量表
        return {
            "consumption": base_consumption,
            "flow_rate": random.uniform(20, 50),
            "supply_temp": random.uniform(5, 10),
            "return_temp": random.uniform(12, 18),
            "pressure": random.uniform(0.2, 0.4)
        }
    
    else:
        # 默认
        return {
            "consumption": base_consumption,
            "flow_rate": random.uniform(10, 50)
        }


def demo_query_data(session: Session, devices: list):
    """演示：查询设备数据"""
    logger.info("\n" + "=" * 60)
    logger.info("🔍 演示 3: 查询设备数据")
    logger.info("=" * 60)
    
    # 随机选择一个设备
    device = random.choice(devices)
    
    logger.info(f"\n查询设备: {device.name}")
    
    # 查询最近的数据
    data_list = DeviceService.get_device_data(
        session=session,
        device_id=device.id,
        limit=5
    )
    
    logger.info(f"  📊 最近 {len(data_list)} 条数据:")
    for data in data_list:
        logger.info(
            f"    - {data.timestamp.strftime('%H:%M:%S')}: "
            f"消耗={data.consumption:.2f}, 瞬时={data.flow_rate:.2f}"
        )


def demo_statistics(session: Session, devices: list):
    """演示：统计分析"""
    logger.info("\n" + "=" * 60)
    logger.info("📈 演示 4: 统计分析")
    logger.info("=" * 60)
    
    # 随机选择一个设备
    device = random.choice(devices)
    
    logger.info(f"\n统计设备: {device.name}")
    
    # 计算统计数据
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    
    stats = DeviceService.get_device_statistics(
        session=session,
        device_id=device.id,
        start_time=start_time,
        end_time=end_time
    )
    
    logger.info(f"  📊 统计结果（最近1小时）:")
    logger.info(f"    - 总消耗: {stats['total_consumption']:.2f}")
    logger.info(f"    - 平均消耗: {stats['avg_consumption']:.2f}")
    logger.info(f"    - 平均流量: {stats['avg_flow_rate']:.2f}")
    logger.info(f"    - 峰值流量: {stats['peak_flow_rate']:.2f}")
    logger.info(f"    - 数据点数: {stats['data_count']}")


def demo_carbon_tracking(session: Session):
    """演示：碳排放追踪"""
    logger.info("\n" + "=" * 60)
    logger.info("🌱 演示 5: 碳排放追踪")
    logger.info("=" * 60)
    
    # 查询最近1小时的碳排放汇总
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    
    summary = EnergyService.get_carbon_summary(
        session=session,
        start_time=start_time,
        end_time=end_time
    )
    
    logger.info(f"\n📊 碳排放汇总（最近1小时）:")
    logger.info(f"  总碳排放: {summary['total_carbon']:.2f} kg CO2")
    
    logger.info(f"\n  各能源类型明细:")
    for energy_type, data in summary['by_energy_type'].items():
        logger.info(f"    - {energy_type}:")
        logger.info(f"        消耗: {data['energy_consumption']:.2f} {data['unit']}")
        logger.info(f"        碳排放: {data['carbon_emission']:.2f} kg CO2")


def demo_device_types(session: Session):
    """演示：查看支持的设备类型"""
    logger.info("\n" + "=" * 60)
    logger.info("📋 演示 6: 支持的设备类型")
    logger.info("=" * 60)
    
    device_types = DeviceService.get_device_types()
    
    logger.info(f"\n系统支持 {len(device_types)} 种设备类型:\n")
    
    # 按能源类型分组显示
    by_energy = {}
    for dt in device_types:
        energy_type = dt['energy_type']
        if energy_type not in by_energy:
            by_energy[energy_type] = []
        by_energy[energy_type].append(dt)
    
    for energy_type, types in by_energy.items():
        logger.info(f"  🔹 {energy_type} ({len(types)} 种):")
        for dt in types:
            logger.info(
                f"    {dt['icon']} {dt['name_zh']} ({dt['device_type']}) "
                f"- 单位: {dt['unit']}"
            )
        logger.info("")


def demo_filtering(session: Session):
    """演示：设备筛选功能"""
    logger.info("=" * 60)
    logger.info("🔎 演示 7: 设备筛选")
    logger.info("=" * 60)
    
    # 按能源类型筛选
    logger.info("\n📌 按能源类型筛选:")
    energy_types = ["electricity", "water", "gas", "heat", "cooling"]
    
    for energy_type in energy_types:
        devices = DeviceService.get_all_devices(
            session=session,
            energy_type=energy_type
        )
        if devices:
            logger.info(f"  - {energy_type}: {len(devices)} 个设备")
            for device in devices:
                logger.info(f"      • {device.name} ({device.device_type})")


def main():
    """主函数"""
    logger.info("🎯 统一设备管理系统演示")
    logger.info(f"启动时间: {datetime.now()}\n")
    
    with Session(engine) as session:
        # 1. 展示支持的设备类型
        demo_device_types(session)
        
        # 2. 智能创建设备
        devices = demo_create_devices(session)
        
        if not devices:
            logger.warning("没有创建任何设备，演示结束")
            return
        
        # 3. 统一数据上报
        demo_report_data(session, devices)
        
        # 4. 查询数据
        demo_query_data(session, devices)
        
        # 5. 统计分析
        demo_statistics(session, devices)
        
        # 6. 碳排放追踪
        demo_carbon_tracking(session)
        
        # 7. 设备筛选
        demo_filtering(session)
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 演示完成！")
    logger.info("=" * 60)
    logger.info("\n💡 关键特性:")
    logger.info("  ✅ 统一的设备创建接口 - 智能配置")
    logger.info("  ✅ 统一的数据上报接口 - 自动路由")
    logger.info("  ✅ 多能源类型支持 - 6种能源")
    logger.info("  ✅ 自动碳排放计算")
    logger.info("  ✅ 灵活的筛选和查询")
    logger.info("  ✅ 易于扩展 - 只需配置即可添加新设备类型")
    logger.info(f"\n完成时间: {datetime.now()}")


if __name__ == "__main__":
    main()
