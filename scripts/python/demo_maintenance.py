"""
设备维护功能演示脚本

演示如何使用维护管理功能：
1. 创建维护记录
2. 开始维护
3. 完成维护
4. 查询维护历史
5. 统计维护信息
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.tables import Device, DeviceMaintenance, MaintenanceType
from app.services.maintenance_service import MaintenanceService


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_create_maintenance():
    """演示创建维护记录"""
    print_section("1. 创建维护记录")
    
    with Session(engine) as session:
        # 获取第一个设备
        device = session.exec(select(Device)).first()
        if not device:
            print("❌ 没有找到设备，请先创建设备")
            return None
        
        print(f"📌 选择设备: {device.name} (ID: {device.id})")
        
        # 创建不同类型的维护记录
        maintenance_records = []
        
        # 1. 日常维护
        m1 = MaintenanceService.create_maintenance(
            session=session,
            device_id=device.id,
            maintenance_type=MaintenanceType.ROUTINE,
            scheduled_time=datetime.now() + timedelta(days=1),
            title="月度例行维护",
            description="检查设备运行状态，清洁设备，更换滤芯",
            operator="张三",
            created_by="系统管理员"
        )
        maintenance_records.append(m1)
        print(f"✅ 创建日常维护记录: {m1.title} (ID: {m1.id})")
        
        # 2. 故障维修
        m2 = MaintenanceService.create_maintenance(
            session=session,
            device_id=device.id,
            maintenance_type=MaintenanceType.REPAIR,
            scheduled_time=datetime.now(),
            title="电压波动故障修复",
            description="设备出现电压波动异常，需要检查电路",
            operator="李四",
            created_by="运维经理"
        )
        maintenance_records.append(m2)
        print(f"✅ 创建故障维修记录: {m2.title} (ID: {m2.id})")
        
        # 3. 定期巡检
        m3 = MaintenanceService.create_maintenance(
            session=session,
            device_id=device.id,
            maintenance_type=MaintenanceType.INSPECTION,
            scheduled_time=datetime.now() + timedelta(days=7),
            title="季度安全巡检",
            description="检查安全防护装置、接地线、绝缘性能",
            operator="王五",
            created_by="安全主管"
        )
        maintenance_records.append(m3)
        print(f"✅ 创建巡检记录: {m3.title} (ID: {m3.id})")
        
        return maintenance_records


def demo_maintenance_workflow(maintenance_id: int):
    """演示维护工作流程"""
    print_section("2. 维护工作流程演示")
    
    with Session(engine) as session:
        # 查看初始状态
        maintenance = MaintenanceService.get_maintenance_by_id(session, maintenance_id)
        print(f"📋 维护任务: {maintenance.title}")
        print(f"   状态: {maintenance.status}")
        print(f"   计划时间: {maintenance.scheduled_time}")
        
        # 开始维护
        print("\n🔧 开始维护...")
        maintenance = MaintenanceService.start_maintenance(
            session, maintenance_id, operator="技术员-张三"
        )
        print(f"✅ 维护已开始")
        print(f"   状态: {maintenance.status}")
        print(f"   开始时间: {maintenance.actual_start_time}")
        
        # 模拟维护过程（实际场景中这里会有实际工作）
        import time
        print("   ⏳ 维护进行中...")
        time.sleep(2)  # 模拟2秒的维护时间
        
        # 完成维护
        print("\n✅ 完成维护...")
        maintenance = MaintenanceService.complete_maintenance(
            session=session,
            maintenance_id=maintenance_id,
            result="设备运行正常，已更换空气滤芯和机油，所有参数在正常范围内",
            cost=350.00,
            parts_replaced='["空气滤芯", "机油5L"]',
            next_maintenance_date=datetime.now() + timedelta(days=30)
        )
        print(f"✅ 维护已完成")
        print(f"   状态: {maintenance.status}")
        print(f"   结束时间: {maintenance.actual_end_time}")
        print(f"   耗时: {maintenance.duration_minutes} 分钟")
        print(f"   成本: ¥{maintenance.cost}")
        print(f"   更换部件: {maintenance.parts_replaced}")
        print(f"   下次维护: {maintenance.next_maintenance_date}")


def demo_query_maintenance():
    """演示查询维护记录"""
    print_section("3. 查询维护记录")
    
    with Session(engine) as session:
        # 查询所有维护记录
        all_records = MaintenanceService.get_maintenance_list(session, limit=10)
        print(f"📊 系统中共有 {len(all_records)} 条维护记录\n")
        
        for record in all_records[:5]:  # 只显示前5条
            print(f"ID: {record.id} | {record.title}")
            print(f"   类型: {record.maintenance_type} | 状态: {record.status}")
            print(f"   计划时间: {record.scheduled_time}")
            if record.cost:
                print(f"   成本: ¥{record.cost}")
            print()


def demo_upcoming_and_overdue():
    """演示即将到来和逾期的维护"""
    print_section("4. 维护提醒")
    
    with Session(engine) as session:
        # 即将到来的维护
        upcoming = MaintenanceService.get_upcoming_maintenance(session, days=30)
        print(f"📅 未来30天内的维护计划 ({len(upcoming)} 条):")
        for m in upcoming:
            days_left = (m.scheduled_time - datetime.now()).days
            print(f"   • {m.title} - 还有 {days_left} 天")
        
        # 逾期的维护
        overdue = MaintenanceService.get_overdue_maintenance(session)
        if overdue:
            print(f"\n⚠️  逾期未完成的维护 ({len(overdue)} 条):")
            for m in overdue:
                days_overdue = (datetime.now() - m.scheduled_time).days
                print(f"   • {m.title} - 已逾期 {days_overdue} 天")
        else:
            print("\n✅ 没有逾期的维护任务")


def demo_statistics():
    """演示维护统计"""
    print_section("5. 维护统计分析")
    
    with Session(engine) as session:
        # 获取统计信息
        stats = MaintenanceService.get_maintenance_statistics(session)
        
        print(f"📈 维护统计总览:")
        print(f"   总记录数: {stats['total_count']}")
        
        print(f"\n📊 按状态统计:")
        for status, count in stats['status_breakdown'].items():
            print(f"   {status}: {count} 条")
        
        print(f"\n📊 按类型统计:")
        for mtype, count in stats['type_breakdown'].items():
            print(f"   {mtype}: {count} 条")
        
        print(f"\n💰 成本统计:")
        cost_stats = stats['cost_statistics']
        print(f"   总成本: ¥{cost_stats['total_cost']}")
        print(f"   平均成本: ¥{cost_stats['average_cost']}")
        print(f"   最高成本: ¥{cost_stats['max_cost']}")
        
        print(f"\n⏱️  时长统计:")
        duration_stats = stats['duration_statistics']
        print(f"   已完成: {duration_stats['completed_count']} 条")
        print(f"   总耗时: {duration_stats['total_duration_minutes']} 分钟")
        print(f"   平均耗时: {duration_stats['average_duration_minutes']} 分钟")


def demo_device_history():
    """演示设备维护历史"""
    print_section("6. 设备维护历史")
    
    with Session(engine) as session:
        # 获取第一个设备
        device = session.exec(select(Device)).first()
        if not device:
            print("❌ 没有找到设备")
            return
        
        print(f"🔍 查询设备维护历史: {device.name}")
        
        history = MaintenanceService.get_device_maintenance_history(
            session, device.id, limit=10
        )
        
        if not history:
            print("   该设备暂无维护记录")
            return
        
        print(f"   共找到 {len(history)} 条维护记录\n")
        
        for i, record in enumerate(history, 1):
            print(f"   {i}. {record.title}")
            print(f"      时间: {record.scheduled_time}")
            print(f"      类型: {record.maintenance_type}")
            print(f"      状态: {record.status}")
            if record.cost:
                print(f"      成本: ¥{record.cost}")
            print()


def main():
    """主函数"""
    print("\n" + "🔧" * 30)
    print("  设备维护管理功能演示")
    print("🔧" * 30)
    
    try:
        # 1. 创建维护记录
        records = demo_create_maintenance()
        if not records:
            print("⚠️  无法继续演示，请先创建设备")
            return
        
        # 2. 演示完整的维护工作流程
        demo_maintenance_workflow(records[0].id)
        
        # 3. 查询维护记录
        demo_query_maintenance()
        
        # 4. 维护提醒
        demo_upcoming_and_overdue()
        
        # 5. 统计分析
        demo_statistics()
        
        # 6. 设备历史
        demo_device_history()
        
        print("\n" + "=" * 60)
        print("  ✅ 演示完成！")
        print("=" * 60)
        
        print("\n📚 API使用说明:")
        print("   • GET    /maintenance/              - 获取维护列表")
        print("   • POST   /maintenance/              - 创建维护记录")
        print("   • GET    /maintenance/{id}          - 获取维护详情")
        print("   • PUT    /maintenance/{id}          - 更新维护记录")
        print("   • POST   /maintenance/{id}/start    - 开始维护")
        print("   • POST   /maintenance/{id}/complete - 完成维护")
        print("   • POST   /maintenance/{id}/cancel   - 取消维护")
        print("   • DELETE /maintenance/{id}          - 删除维护记录")
        print("   • GET    /maintenance/upcoming/list - 即将到来的维护")
        print("   • GET    /maintenance/overdue/list  - 逾期的维护")
        print("   • GET    /maintenance/statistics/summary - 统计信息")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
