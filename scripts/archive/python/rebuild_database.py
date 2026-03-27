#!/usr/bin/env python3
"""
数据库重建脚本 - 全新系统使用

清空数据库并重新创建所有表（基于统一架构 v2.2.0）

⚠️  警告：此脚本会删除所有数据！仅用于全新系统或开发环境。

执行方式:
    python scripts/archive/python/rebuild_database.py

参数:
    --confirm: 确认执行（必需，防止误操作）
    --keep-users: 保留用户表数据
    --demo-data: 创建演示数据
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from sqlmodel import Session, SQLModel, select
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import engine
from app.models.tables import (
    Device, EnergyData, CarbonEmission, EnergyStatistics,
    Alarm, User, Prediction
)
from app.services.device_service import DeviceService
from app.core.security import get_password_hash


def drop_all_tables(keep_users: bool = False):
    """删除所有表"""
    logger.warning("🗑️  准备删除所有表...")
    
    if keep_users:
        logger.info("📌 将保留用户表数据")
        # 保存用户数据
        with Session(engine) as session:
            users = session.exec(select(User)).all()
            user_data = [
                {
                    "username": u.username,
                    "hashed_password": u.hashed_password,
                    "is_active": u.is_active
                }
                for u in users
            ]
    
    # 删除所有表
    SQLModel.metadata.drop_all(engine)
    logger.info("✅ 所有表已删除")
    
    return user_data if keep_users else None


def create_all_tables():
    """创建所有表"""
    logger.info("🔨 创建数据库表...")
    
    # 创建所有表
    SQLModel.metadata.create_all(engine)
    
    logger.info("✅ 数据库表创建完成")
    logger.info("\n📊 已创建的表:")
    logger.info("  - Device (设备表)")
    logger.info("  - EnergyData (能源数据表 - 时序)")
    logger.info("  - CarbonEmission (碳排放表 - 时序)")
    logger.info("  - EnergyStatistics (能源统计表)")
    logger.info("  - Alarm (报警表)")
    logger.info("  - User (用户表)")
    logger.info("  - Prediction (预测表)")


def create_default_user():
    """创建默认管理员用户"""
    logger.info("\n👤 创建默认用户...")
    
    with Session(engine) as session:
        # 检查是否已存在
        existing = session.exec(
            select(User).where(User.username == "admin")
        ).first()
        
        if existing:
            logger.info("  ℹ️  用户 'admin' 已存在，跳过创建")
            return
        
        admin_password = os.environ.get("ADMIN_PASSWORD", "")
        if not admin_password:
            logger.warning("  ⚠️ 未设置 ADMIN_PASSWORD 环境变量，使用临时密码")
            admin_password = "change-me-immediately-2026!"
        admin = User(
            username="admin",
            hashed_password=get_password_hash(admin_password),
            is_active=True
        )
        
        session.add(admin)
        session.commit()
        
        logger.info("✅ 默认用户创建成功:")
        logger.info("  - 用户名: admin")
        logger.info("  - 密码: <ADMIN_PASSWORD 环境变量值>")
        logger.info("  ⚠️  请在生产环境中修改密码！")


def restore_users(user_data: list):
    """恢复用户数据"""
    if not user_data:
        return
    
    logger.info(f"\n👥 恢复 {len(user_data)} 个用户...")
    
    with Session(engine) as session:
        for data in user_data:
            user = User(**data)
            session.add(user)
        
        session.commit()
        
        logger.info(f"✅ 已恢复 {len(user_data)} 个用户")


def create_demo_devices():
    """创建演示设备"""
    logger.info("\n📦 创建演示设备...")
    
    demo_devices = [
        # 电力系统
        {
            "name": "1号配电柜",
            "sn": "LOAD001",
            "device_type": "load",
            "location": "A栋配电室",
            "description": "主配电柜，供应整栋楼用电"
        },
        {
            "name": "屋顶光伏阵列",
            "sn": "SOLAR001",
            "device_type": "solar",
            "location": "A栋屋顶",
            "description": "100kW光伏发电系统"
        },
        {
            "name": "储能柜A",
            "sn": "STORAGE001",
            "device_type": "storage",
            "location": "储能室",
            "description": "500kWh锂电池储能系统"
        },
        
        # 水系统
        {
            "name": "1号水表",
            "sn": "WATER001",
            "device_type": "water_meter",
            "location": "A栋1层水泵房",
            "description": "生活用水总表"
        },
        
        # 燃气系统
        {
            "name": "1号燃气表",
            "sn": "GAS001",
            "device_type": "gas_meter",
            "location": "锅炉房",
            "description": "供暖锅炉燃气表"
        },
        
        # 热力系统
        {
            "name": "1号热量表",
            "sn": "HEAT001",
            "device_type": "heat_meter",
            "location": "换热站",
            "description": "集中供暖热量计量"
        },
        
        # 制冷系统
        {
            "name": "中央空调冷量表",
            "sn": "COOLING001",
            "device_type": "cooling_meter",
            "location": "制冷机房",
            "description": "中央空调系统冷量计量"
        },
    ]
    
    with Session(engine) as session:
        created_devices = []
        
        for device_data in demo_devices:
            try:
                device = DeviceService.create_device_smart(
                    session,
                    **device_data
                )
                created_devices.append(device)
                logger.info(f"  ✅ {device.name} ({device.device_type})")
            except Exception as e:
                logger.error(f"  ❌ 创建失败: {device_data['name']} - {e}")
        
        logger.info(f"\n✅ 共创建 {len(created_devices)} 个演示设备")
        
        return created_devices


def create_demo_data(devices: list):
    """为演示设备创建一些初始数据"""
    logger.info("\n📊 创建演示数据...")
    
    import random
    
    with Session(engine) as session:
        total_records = 0
        
        for device in devices:
            # 为每个设备创建 5 条历史数据
            for i in range(5):
                try:
                    # 根据设备类型生成不同的数据
                    if device.device_type in ["load", "solar", "wind", "storage", "charger"]:
                        data = {
                            "consumption": random.uniform(50, 200),
                            "power": random.uniform(20, 80),
                            "voltage": random.uniform(215, 225),
                            "current": random.uniform(10, 30)
                        }
                    elif device.device_type == "water_meter":
                        data = {
                            "consumption": random.uniform(5, 20),
                            "flow_rate": random.uniform(1, 5),
                            "pressure": random.uniform(0.2, 0.4),
                            "temperature": random.uniform(15, 25)
                        }
                    elif device.device_type == "gas_meter":
                        data = {
                            "consumption": random.uniform(10, 30),
                            "flow_rate": random.uniform(5, 15),
                            "pressure": random.uniform(0.1, 0.3),
                            "temperature": random.uniform(10, 20)
                        }
                    elif device.device_type == "heat_meter":
                        data = {
                            "consumption": random.uniform(3, 10),
                            "heat_flow": random.uniform(1, 5),
                            "supply_temp": random.uniform(60, 80),
                            "return_temp": random.uniform(40, 60),
                            "flow_rate": random.uniform(10, 30)
                        }
                    elif device.device_type == "cooling_meter":
                        data = {
                            "consumption": random.uniform(50, 150),
                            "flow_rate": random.uniform(20, 50),
                            "supply_temp": random.uniform(5, 10),
                            "return_temp": random.uniform(12, 18)
                        }
                    else:
                        continue
                    
                    DeviceService.report_device_data(
                        session,
                        device_id=device.id,
                        data=data
                    )
                    total_records += 1
                    
                except Exception as e:
                    logger.error(f"  ❌ 创建数据失败: {device.name} - {e}")
        
        logger.info(f"✅ 共创建 {total_records} 条演示数据")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="数据库重建脚本 - 全新系统使用"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="确认执行（必需，防止误操作）"
    )
    parser.add_argument(
        "--keep-users",
        action="store_true",
        help="保留用户表数据"
    )
    parser.add_argument(
        "--demo-data",
        action="store_true",
        help="创建演示数据"
    )
    
    args = parser.parse_args()
    
    # 安全检查
    if not args.confirm:
        logger.error("❌ 必须使用 --confirm 参数确认执行")
        logger.error("⚠️  此操作会删除所有数据！")
        logger.error("\n执行命令:")
        logger.error("  python scripts/archive/python/rebuild_database.py --confirm")
        logger.error("\n如需创建演示数据:")
        logger.error("  python scripts/archive/python/rebuild_database.py --confirm --demo-data")
        return
    
    logger.info("=" * 60)
    logger.info("🔄 数据库重建 - 统一架构 v2.2.0")
    logger.info("=" * 60)
    logger.info(f"⏰ 开始时间: {datetime.now()}")
    logger.info("")
    
    # 最后确认
    logger.warning("⚠️  警告：此操作将删除所有数据！")
    logger.warning("⚠️  5秒后开始执行...")
    
    import time
    for i in range(5, 0, -1):
        logger.warning(f"  {i}...")
        time.sleep(1)
    
    logger.info("")
    
    try:
        # 步骤 1: 删除所有表
        user_data = drop_all_tables(keep_users=args.keep_users)
        
        # 步骤 2: 创建所有表
        create_all_tables()
        
        # 步骤 3: 恢复用户数据（如果需要）
        if user_data:
            restore_users(user_data)
        else:
            # 创建默认用户
            create_default_user()
        
        # 步骤 4: 创建演示数据（如果需要）
        if args.demo_data:
            devices = create_demo_devices()
            if devices:
                create_demo_data(devices)
        
        # 完成
        logger.info("\n" + "=" * 60)
        logger.info("✅ 数据库重建完成！")
        logger.info("=" * 60)
        logger.info(f"⏰ 完成时间: {datetime.now()}")
        logger.info("")
        logger.info("📋 后续步骤:")
        logger.info("  1. 访问 API 文档: http://localhost:8088/docs")
        logger.info("  2. 使用 admin/<ADMIN_PASSWORD> 登录")
        logger.info("  3. 开始使用统一设备管理系统")
        logger.info("")
        logger.info("💡 提示:")
        logger.info("  - 查看文档: docs/02-功能使用/统一设备管理指南.md")
        logger.info("  - 运行演示: python scripts/python/demo_unified_system.py")
        
    except Exception as e:
        logger.error(f"\n❌ 数据库重建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
