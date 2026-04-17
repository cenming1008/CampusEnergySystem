"""
设备分组功能演示脚本

演示如何使用设备分组功能（多对多关系）：
1. 创建分组
2. 添加设备到分组
3. 查询设备的分组
4. 查询分组的设备
5. 统计分组信息
6. 实际应用场景
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.tables import Device, DeviceGroup, DeviceGroupMembership
from app.services.device_group_service import DeviceGroupService
from app.services.device_service import DeviceService


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_create_groups():
    """演示创建分组"""
    print_section("1. 创建设备分组")
    
    with Session(engine) as session:
        # 创建关键设备组
        group_critical = DeviceGroupService.create_group(
            session=session,
            name="关键设备",
            code="GROUP-CRITICAL",
            description="需要重点监控的关键设备",
            group_type="critical",
            manager="张三",
            contact="13800138000"
        )
        print(f"✅ 创建分组: {group_critical.name} (ID: {group_critical.id})")
        print(f"   编码: {group_critical.code}")
        print(f"   类型: {group_critical.group_type}")
        
        # 创建生产设备组
        group_production = DeviceGroupService.create_group(
            session=session,
            name="生产设备",
            code="GROUP-PRODUCTION",
            description="生产线相关设备",
            group_type="production",
            manager="李四"
        )
        print(f"\n✅ 创建分组: {group_production.name} (ID: {group_production.id})")
        
        # 创建办公设备组
        group_office = DeviceGroupService.create_group(
            session=session,
            name="办公设备",
            code="GROUP-OFFICE",
            description="办公区域设备",
            group_type="office",
            manager="王五"
        )
        print(f"\n✅ 创建分组: {group_office.name} (ID: {group_office.id})")
        
        # 创建备用设备组
        group_backup = DeviceGroupService.create_group(
            session=session,
            name="备用设备",
            code="GROUP-BACKUP",
            description="备用或待机设备",
            group_type="backup"
        )
        print(f"\n✅ 创建分组: {group_backup.name} (ID: {group_backup.id})")
        
        return {
            "critical": group_critical,
            "production": group_production,
            "office": group_office,
            "backup": group_backup
        }


def demo_add_devices_to_groups(groups: dict):
    """演示添加设备到分组（多对多关系）"""
    print_section("2. 添加设备到分组（一个设备可以属于多个分组）")
    
    with Session(engine) as session:
        # 获取一些设备
        devices = session.exec(select(Device).limit(5)).all()
        
        if len(devices) < 3:
            print("⚠️  设备数量不足，请先运行 demo_location.py 创建设备")
            return
        
        device1 = devices[0]
        device2 = devices[1]
        device3 = devices[2]
        
        # 设备1：既是关键设备，又是生产设备
        print(f"\n📍 设备1: {device1.name}")
        
        DeviceGroupService.add_device_to_group(
            session=session,
            device_id=device1.id,
            group_id=groups["critical"].id,
            note="主生产线关键设备"
        )
        print(f"   ✅ 加入分组: {groups['critical'].name}")
        
        DeviceGroupService.add_device_to_group(
            session=session,
            device_id=device1.id,
            group_id=groups["production"].id,
            note="主生产设备"
        )
        print(f"   ✅ 加入分组: {groups['production'].name}")
        
        # 设备2：既是关键设备，又是办公设备
        print(f"\n📍 设备2: {device2.name}")
        
        DeviceGroupService.add_device_to_group(
            session=session,
            device_id=device2.id,
            group_id=groups["critical"].id,
            note="办公区关键电表"
        )
        print(f"   ✅ 加入分组: {groups['critical'].name}")
        
        DeviceGroupService.add_device_to_group(
            session=session,
            device_id=device2.id,
            group_id=groups["office"].id
        )
        print(f"   ✅ 加入分组: {groups['office'].name}")
        
        # 设备3：备用设备
        print(f"\n📍 设备3: {device3.name}")
        
        DeviceGroupService.add_device_to_group(
            session=session,
            device_id=device3.id,
            group_id=groups["backup"].id
        )
        print(f"   ✅ 加入分组: {groups['backup'].name}")
        
        print("\n💡 多对多关系示例:")
        print(f"   • {device1.name} 属于 2 个分组")
        print(f"   • {device2.name} 属于 2 个分组")
        print(f"   • {device3.name} 属于 1 个分组")


def demo_query_device_groups():
    """演示查询设备所属的分组"""
    print_section("3. 查询设备属于哪些分组")
    
    with Session(engine) as session:
        # 获取前3个设备
        devices = session.exec(select(Device).limit(3)).all()
        
        for device in devices:
            print(f"\n🔍 设备: {device.name} (ID: {device.id})")
            
            # 查询设备所属的所有分组
            groups = DeviceGroupService.get_device_groups(
                session=session,
                device_id=device.id
            )
            
            if groups:
                print(f"   属于 {len(groups)} 个分组:")
                for group in groups:
                    print(f"   • {group.name} ({group.group_type})")
            else:
                print("   不属于任何分组")


def demo_query_group_devices(groups: dict):
    """演示查询分组包含的设备"""
    print_section("4. 查询分组包含哪些设备")
    
    with Session(engine) as session:
        # 查询关键设备组
        print(f"\n🔍 分组: {groups['critical'].name}")
        devices = DeviceGroupService.get_devices_in_group(
            session=session,
            group_id=groups["critical"].id
        )
        
        print(f"   包含 {len(devices)} 个设备:")
        for device in devices:
            print(f"   • {device.name} ({device.energy_type})")
        
        # 查询生产设备组
        print(f"\n🔍 分组: {groups['production'].name}")
        devices = DeviceGroupService.get_devices_in_group(
            session=session,
            group_id=groups["production"].id
        )
        
        print(f"   包含 {len(devices)} 个设备:")
        for device in devices:
            print(f"   • {device.name}")


def demo_group_statistics(groups: dict):
    """演示分组统计"""
    print_section("5. 分组统计信息")
    
    with Session(engine) as session:
        # 统计关键设备组
        print(f"\n📊 {groups['critical'].name} 统计:")
        stats = DeviceGroupService.get_group_statistics(
            session=session,
            group_id=groups["critical"].id
        )
        
        print(f"   总设备数: {stats['device_count']['total']}")
        print(f"   活跃设备: {stats['device_count']['active']}")
        print(f"   负责人: {stats['manager']}")
        
        if stats['device_count']['by_energy_type']:
            print(f"\n   按能源类型统计:")
            for energy_type, count in stats['device_count']['by_energy_type'].items():
                print(f"     - {energy_type}: {count} 个")
        
        # 统计所有分组
        print(f"\n📊 所有分组汇总:")
        all_stats = DeviceGroupService.get_all_group_statistics(session)
        
        for stat in all_stats:
            print(f"   • {stat['name']}: {stat['device_count']} 个设备")


def demo_membership_table():
    """演示中间表的数据"""
    print_section("6. 查看中间表数据（多对多关系的实现）")
    
    with Session(engine) as session:
        # 查询所有关联关系
        statement = select(DeviceGroupMembership).limit(10)
        memberships = session.exec(statement).all()
        
        print("\n📋 DeviceGroupMembership 中间表数据:")
        print(f"   (这就是多对多关系的核心！)\n")
        
        if memberships:
            print("   device_id | group_id | joined_at            | note")
            print("   ----------|----------|----------------------|-------------")
            
            for m in memberships:
                # 获取设备和分组名称
                device = session.get(Device, m.device_id)
                group = session.get(DeviceGroup, m.group_id)
                
                device_name = device.name if device else "?"
                group_name = group.name if group else "?"
                note = m.note or ""
                
                print(f"   {m.device_id:9d} | {m.group_id:8d} | "
                      f"{m.joined_at.strftime('%Y-%m-%d %H:%M:%S')} | {note[:20]}")
                print(f"             ({device_name} ↔ {group_name})")
        else:
            print("   暂无数据")
        
        print("\n💡 解读:")
        print("   • 每一行 = 一个设备-分组关系")
        print("   • 同一个设备可以有多行（属于多个分组）")
        print("   • 同一个分组可以有多行（包含多个设备）")
        print("   • 这就是多对多关系的实现原理！")


def demo_practical_scenarios(groups: dict):
    """演示实际应用场景"""
    print_section("7. 实际应用场景")
    
    with Session(engine) as session:
        # 场景1：监控所有关键设备
        print("\n📝 场景1: 监控中心需要查看所有关键设备")
        critical_devices = DeviceGroupService.get_devices_in_group(
            session=session,
            group_id=groups["critical"].id
        )
        
        print(f"   找到 {len(critical_devices)} 个关键设备:")
        for device in critical_devices:
            print(f"   • {device.name} - {device.sn}")
        
        # 场景2：查找某设备是否是关键设备
        print("\n📝 场景2: 检查设备是否是关键设备")
        
        if critical_devices:
            device = critical_devices[0]
            is_critical = DeviceGroupService.is_device_in_group(
                session=session,
                device_id=device.id,
                group_id=groups["critical"].id
            )
            
            print(f"   设备 {device.name}:")
            print(f"   是否为关键设备? {'✅ 是' if is_critical else '❌ 否'}")
        
        # 场景3：批量添加设备到分组
        print("\n📝 场景3: 批量将设备加入办公设备组")
        
        # 获取前3个设备
        devices = session.exec(select(Device).limit(3)).all()
        device_ids = [d.id for d in devices]
        
        try:
            count = DeviceGroupService.batch_add_devices_to_group(
                session=session,
                device_ids=device_ids,
                group_id=groups["office"].id
            )
            print(f"   成功添加 {count}/{len(device_ids)} 个设备到办公设备组")
        except Exception as e:
            print(f"   部分设备已在分组中（这是正常的）")


def demo_remove_device():
    """演示移除设备"""
    print_section("8. 移除设备分组关系")
    
    with Session(engine) as session:
        # 获取第一个设备
        device = session.exec(select(Device)).first()
        
        if not device:
            print("⚠️  没有设备")
            return
        
        # 查看设备当前的分组
        groups_before = DeviceGroupService.get_device_groups(
            session=session,
            device_id=device.id
        )
        
        print(f"\n📍 设备: {device.name}")
        print(f"   当前属于 {len(groups_before)} 个分组:")
        for g in groups_before:
            print(f"   • {g.name}")
        
        if groups_before:
            # 从第一个分组中移除
            group_to_remove = groups_before[0]
            
            print(f"\n🗑️  从分组 '{group_to_remove.name}' 中移除...")
            DeviceGroupService.remove_device_from_group(
                session=session,
                device_id=device.id,
                group_id=group_to_remove.id
            )
            print(f"   ✅ 已移除")
            
            # 查看移除后的分组
            groups_after = DeviceGroupService.get_device_groups(
                session=session,
                device_id=device.id
            )
            
            print(f"\n   现在属于 {len(groups_after)} 个分组:")
            for g in groups_after:
                print(f"   • {g.name}")


def main():
    """主函数"""
    print("\n" + "🏷️" * 35)
    print("  设备分组管理功能演示（多对多关系）")
    print("🏷️" * 35)
    
    try:
        # 1. 创建分组
        groups = demo_create_groups()
        
        # 2. 添加设备到分组
        demo_add_devices_to_groups(groups)
        
        # 3. 查询设备的分组
        demo_query_device_groups()
        
        # 4. 查询分组的设备
        demo_query_group_devices(groups)
        
        # 5. 分组统计
        demo_group_statistics(groups)
        
        # 6. 查看中间表
        demo_membership_table()
        
        # 7. 实际应用场景
        demo_practical_scenarios(groups)
        
        # 8. 移除设备
        demo_remove_device()
        
        print("\n" + "=" * 70)
        print("  ✅ 演示完成！")
        print("=" * 70)
        
        print("\n📚 API使用说明:")
        print("   • GET    /device-groups/              - 获取分组列表")
        print("   • POST   /device-groups/              - 创建分组")
        print("   • GET    /device-groups/{id}          - 获取分组详情")
        print("   • PUT    /device-groups/{id}          - 更新分组")
        print("   • DELETE /device-groups/{id}          - 删除分组")
        print("   • GET    /device-groups/{id}/devices  - 获取分组设备")
        print("   • POST   /device-groups/{id}/devices  - 添加设备到分组")
        print("   • DELETE /device-groups/{id}/devices/{device_id} - 移除设备")
        print("   • GET    /device-groups/{id}/statistics - 分组统计")
        
        print("\n💡 多对多关系的优势:")
        print("   1. 一个设备可以属于多个分组（如：既是关键设备，又是生产设备）")
        print("   2. 一个分组可以包含多个设备")
        print("   3. 灵活管理，易于查询和统计")
        print("   4. 通过中间表实现，数据结构清晰")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
