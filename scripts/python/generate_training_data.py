#!/usr/bin/env python3
"""
数据生成脚本
用于快速生成训练数据

使用方法:
    python scripts/generate_training_data.py --days 60 --device-id 1
    python scripts/generate_training_data.py --all --days 90
"""
import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.services.data_generator import DataGenerator
from app.models.tables import Device
from sqlmodel import select
from app.core.logger import logger


def main():
    parser = argparse.ArgumentParser(description="生成模拟训练数据")
    parser.add_argument("--days", type=int, default=60, help="生成数据的天数（默认60）")
    parser.add_argument("--interval", type=int, default=60, help="数据间隔（分钟，默认60）")
    parser.add_argument("--device-id", type=int, help="设备ID（不提供则生成所有设备）")
    parser.add_argument("--all", action="store_true", help="为所有设备生成数据")
    parser.add_argument("--type", choices=["load", "solar", "wind"], default="load", help="数据类型")
    parser.add_argument("--clear", action="store_true", help="清除现有数据")
    
    args = parser.parse_args()
    
    with SessionLocal() as session:
        if args.all or args.device_id is None:
            # 为所有设备生成
            logger.info("为所有活动设备生成数据...")
            
            devices = session.exec(select(Device).where(Device.is_active == True)).all()
            if not devices:
                logger.error("没有活动设备，请先创建设备")
                return
            
            logger.info(f"找到 {len(devices)} 个活动设备")
            
            if args.clear:
                DataGenerator.clear_device_data(session)
            
            total_count = DataGenerator.generate_system_data(
                session=session,
                days=args.days,
                interval_minutes=args.interval
            )
            
            logger.info(f"✅ 成功生成 {total_count} 条数据")
        else:
            # 为指定设备生成
            device = session.get(Device, args.device_id)
            if not device:
                logger.error(f"设备 {args.device_id} 不存在")
                return
            
            logger.info(f"为设备 {args.device_id} ({device.name}) 生成数据...")
            
            if args.clear:
                DataGenerator.clear_device_data(session, device_id=args.device_id)
            
            count = DataGenerator.generate_device_data(
                session=session,
                device_id=args.device_id,
                days=args.days,
                interval_minutes=args.interval,
                data_type=args.type
            )
            
            logger.info(f"✅ 成功生成 {count} 条数据")


if __name__ == "__main__":
    main()
