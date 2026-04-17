"""
位置层级管理功能演示脚本

演示如何使用位置管理功能：
1. 创建位置层级（楼栋-单元-房间）
2. 将设备分配到位置
3. 查询位置下的设备
4. 统计位置能耗
5. 展示位置树形结构
"""
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.tables import Location, Device, LocationType
from app.services.location_service import LocationService
from app.services.device_service import DeviceService


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_create_location_hierarchy():
    """演示创建位置层级"""
    print_section("1. 创建位置层级（楼栋-单元-房间）")
    
    with Session(engine) as session:
        # 创建A栋
        building_a = LocationService.create_location(
            session=session,
            name="A栋",
            location_type=LocationType.BUILDING,
            code="BUILD-A",
            description="A栋办公楼",
            area_sqm=5000.0,
            manager="张三",
            contact="13800138000"
        )
        print(f"✅ 创建楼栋: {building_a.name} (ID: {building_a.id})")
        print(f"   路径: {building_a.full_path}")
        print(f"   层级: {building_a.level}")
        
        # 创建3单元
        unit_3 = LocationService.create_location(
            session=session,
            name="3单元",
            location_type=LocationType.UNIT,
            code="BUILD-A-UNIT-3",
            parent_id=building_a.id,
            description="A栋3单元"
        )
        print(f"\n✅ 创建单元: {unit_3.name} (ID: {unit_3.id})")
        print(f"   父级: {building_a.name}")
        print(f"   路径: {unit_3.full_path}")
        print(f"   层级: {unit_3.level}")
        
        # 创建13层
        floor_13 = LocationService.create_location(
            session=session,
            name="13层",
            location_type=LocationType.FLOOR,
            code="BUILD-A-UNIT-3-FLOOR-13",
            parent_id=unit_3.id
        )
        print(f"\n✅ 创建楼层: {floor_13.name} (ID: {floor_13.id})")
        print(f"   路径: {floor_13.full_path}")
        
        # 创建1309房间
        room_1309 = LocationService.create_location(
            session=session,
            name="1309",
            location_type=LocationType.ROOM,
            code="BUILD-A-UNIT-3-FLOOR-13-ROOM-09",
            parent_id=floor_13.id,
            description="1309号房间",
            area_sqm=80.0,
            manager="李四"
        )
        print(f"\n✅ 创建房间: {room_1309.name} (ID: {room_1309.id})")
        print(f"   完整路径: {room_1309.full_path}")
        print(f"   层级深度: {room_1309.level}")
        print(f"   面积: {room_1309.area_sqm} 平方米")
        print(f"   负责人: {room_1309.manager}")
        
        # 创建更多房间
        room_1310 = LocationService.create_location(
            session=session,
            name="1310",
            location_type=LocationType.ROOM,
            code="BUILD-A-UNIT-3-FLOOR-13-ROOM-10",
            parent_id=floor_13.id,
            area_sqm=85.0
        )
        
        # 创建1单元和房间
        unit_1 = LocationService.create_location(
            session=session,
            name="1单元",
            location_type=LocationType.UNIT,
            code="BUILD-A-UNIT-1",
            parent_id=building_a.id
        )
        
        floor_1 = LocationService.create_location(
            session=session,
            name="1层",
            location_type=LocationType.FLOOR,
            parent_id=unit_1.id
        )
        
        room_101 = LocationService.create_location(
            session=session,
            name="101",
            location_type=LocationType.ROOM,
            code="BUILD-A-UNIT-1-FLOOR-1-ROOM-01",
            parent_id=floor_1.id,
            area_sqm=90.0
        )
        
        print(f"\n✅ 同时创建了其他位置:")
        print(f"   - {unit_1.full_path}")
        print(f"   - {floor_1.full_path}")
        print(f"   - {room_101.full_path}")
        print(f"   - {room_1310.full_path}")
        
        return {
            "building_a": building_a,
            "unit_3": unit_3,
            "floor_13": floor_13,
            "room_1309": room_1309,
            "room_1310": room_1310,
            "room_101": room_101
        }


def demo_assign_devices_to_locations(locations: dict):
    """演示将设备分配到位置"""
    print_section("2. 将设备分配到位置")
    
    with Session(engine) as session:
        room_1309 = locations["room_1309"]
        room_1310 = locations["room_1310"]
        room_101 = locations["room_101"]
        
        # 创建1309的设备
        print(f"\n📍 为 {room_1309.full_path} 创建设备:")
        
        device_1309_meter = DeviceService.create_device_smart(
            session=session,
            name="1309电表",
            sn="METER-1309",
            device_type="load",
            location_id=room_1309.id
        )
        print(f"   ✅ {device_1309_meter.name} (序列号: {device_1309_meter.sn})")
        
        device_1309_water = DeviceService.create_device_smart(
            session=session,
            name="1309水表",
            sn="WATER-1309",
            device_type="water_meter",
            location_id=room_1309.id
        )
        print(f"   ✅ {device_1309_water.name} (序列号: {device_1309_water.sn})")
        
        device_1309_gas = DeviceService.create_device_smart(
            session=session,
            name="1309燃气表",
            sn="GAS-1309",
            device_type="gas_meter",
            location_id=room_1309.id
        )
        print(f"   ✅ {device_1309_gas.name} (序列号: {device_1309_gas.sn})")
        
        # 创建1310的设备
        print(f"\n📍 为 {room_1310.full_path} 创建设备:")
        
        device_1310_meter = DeviceService.create_device_smart(
            session=session,
            name="1310电表",
            sn="METER-1310",
            device_type="load",
            location_id=room_1310.id
        )
        print(f"   ✅ {device_1310_meter.name}")
        
        device_1310_water = DeviceService.create_device_smart(
            session=session,
            name="1310水表",
            sn="WATER-1310",
            device_type="water_meter",
            location_id=room_1310.id
        )
        print(f"   ✅ {device_1310_water.name}")
        
        # 创建101的设备
        print(f"\n📍 为 {room_101.full_path} 创建设备:")
        
        device_101_meter = DeviceService.create_device_smart(
            session=session,
            name="101电表",
            sn="METER-101",
            device_type="load",
            location_id=room_101.id
        )
        print(f"   ✅ {device_101_meter.name}")


def demo_query_devices_by_location(locations: dict):
    """演示查询位置下的设备"""
    print_section("3. 查询位置下的设备")
    
    with Session(engine) as session:
        room_1309 = locations["room_1309"]
        floor_13 = locations["floor_13"]
        building_a = locations["building_a"]
        
        # 查询1309房间的设备
        print(f"\n🔍 查询 {room_1309.full_path} 的设备:")
        devices_1309 = LocationService.get_devices_by_location(
            session=session,
            location_id=room_1309.id
        )
        print(f"   找到 {len(devices_1309)} 个设备:")
        for device in devices_1309:
            print(f"   • {device.name} ({device.energy_type})")
        
        # 查询13层的所有设备（包括所有房间）
        print(f"\n🔍 查询 {floor_13.full_path} 的所有设备（递归）:")
        devices_floor = LocationService.get_devices_by_location(
            session=session,
            location_id=floor_13.id,
            recursive=True
        )
        print(f"   找到 {len(devices_floor)} 个设备")
        
        # 查询A栋的所有设备
        print(f"\n🔍 查询 {building_a.full_path} 的所有设备（递归）:")
        devices_building = LocationService.get_devices_by_location(
            session=session,
            location_id=building_a.id,
            recursive=True
        )
        print(f"   找到 {len(devices_building)} 个设备")
        
        # 按能源类型筛选
        print(f"\n🔍 查询 {building_a.full_path} 的所有电力设备:")
        devices_electricity = LocationService.get_devices_by_location(
            session=session,
            location_id=building_a.id,
            recursive=True,
            energy_type="electricity"
        )
        print(f"   找到 {len(devices_electricity)} 个电力设备:")
        for device in devices_electricity:
            # 获取设备的位置信息
            location = session.get(Location, device.location_id)
            print(f"   • {device.name} - 位于 {location.full_path}")


def demo_location_statistics(locations: dict):
    """演示位置统计"""
    print_section("4. 位置统计信息")
    
    with Session(engine) as session:
        building_a = locations["building_a"]
        room_1309 = locations["room_1309"]
        
        # 统计A栋
        print(f"\n📊 {building_a.full_path} 统计信息:")
        stats_building = LocationService.get_location_statistics(
            session=session,
            location_id=building_a.id,
            recursive=True
        )
        
        print(f"   总设备数: {stats_building['device_count']['total']}")
        print(f"   活跃设备: {stats_building['device_count']['active']}")
        print(f"   子位置数: {stats_building['child_locations_count']}")
        
        print(f"\n   按能源类型统计:")
        for energy_type, count in stats_building['device_count']['by_energy_type'].items():
            print(f"     - {energy_type}: {count} 个")
        
        print(f"\n   按设备类别统计:")
        for category, count in stats_building['device_count']['by_category'].items():
            print(f"     - {category}: {count} 个")
        
        # 统计1309房间
        print(f"\n📊 {room_1309.full_path} 统计信息:")
        stats_room = LocationService.get_location_statistics(
            session=session,
            location_id=room_1309.id
        )
        
        print(f"   设备数: {stats_room['device_count']['total']}")
        print(f"   面积: {stats_room['area_sqm']} 平方米")
        print(f"   负责人: {stats_room['manager']}")
        print(f"\n   设备清单:")
        for energy_type, count in stats_room['device_count']['by_energy_type'].items():
            print(f"     - {energy_type}: {count} 个")


def demo_location_tree():
    """演示位置树形结构"""
    print_section("5. 位置树形结构")
    
    with Session(engine) as session:
        # 获取完整的位置树
        tree = LocationService.get_location_tree(session)
        
        print("\n🌳 完整位置树:")
        
        def print_tree(nodes, indent=0):
            """递归打印树"""
            for node in nodes:
                prefix = "  " * indent
                icon = "📍" if indent == 0 else "└─"
                print(f"{prefix}{icon} {node['name']} "
                      f"({node['type']}) "
                      f"[{node['device_count']} 设备]")
                
                if node['children']:
                    print_tree(node['children'], indent + 1)
        
        print_tree(tree)


def demo_search_locations():
    """演示位置搜索"""
    print_section("6. 位置搜索")
    
    with Session(engine) as session:
        # 搜索包含"1309"的位置
        print("\n🔍 搜索关键词: '1309'")
        results = LocationService.search_locations(session, "1309")
        print(f"   找到 {len(results)} 个结果:")
        for loc in results:
            print(f"   • {loc.full_path} ({loc.location_type})")
        
        # 搜索包含"单元"的位置
        print("\n🔍 搜索关键词: '单元'")
        results = LocationService.search_locations(session, "单元")
        print(f"   找到 {len(results)} 个结果:")
        for loc in results:
            print(f"   • {loc.full_path}")


def demo_practical_scenario():
    """演示实际应用场景"""
    print_section("7. 实际应用场景")
    
    with Session(engine) as session:
        # 场景：物业管理需要知道A栋3单元1309的用电情况
        print("\n📝 场景: 查询 A栋3单元1309 的所有能源设备")
        
        # 方法1：通过编码精确查找
        location = LocationService.get_location_by_code(
            session, "BUILD-A-UNIT-3-FLOOR-13-ROOM-09"
        )
        
        if location:
            print(f"   位置: {location.full_path}")
            print(f"   面积: {location.area_sqm} 平方米")
            print(f"   负责人: {location.manager}")
            
            # 获取设备
            devices = LocationService.get_devices_by_location(
                session, location.id
            )
            
            print(f"\n   该房间的能源设备:")
            for device in devices:
                print(f"   • {device.name} ({device.energy_type})")
                print(f"     序列号: {device.sn}")
                print(f"     类别: {device.device_category}")
        
        # 场景：统计整栋楼的设备情况
        print("\n📝 场景: 统计 A栋 的设备配置")
        
        building = LocationService.get_location_by_code(session, "BUILD-A")
        if building:
            stats = LocationService.get_location_statistics(
                session, building.id, recursive=True
            )
            
            print(f"   楼栋: {building.name}")
            print(f"   总设备: {stats['device_count']['total']} 个")
            print(f"   子位置: {stats['child_locations_count']} 个")
            print(f"\n   能源类型分布:")
            for energy_type, count in stats['device_count']['by_energy_type'].items():
                print(f"     {energy_type}: {count} 个")


def main():
    """主函数"""
    print("\n" + "🏢" * 35)
    print("  位置层级管理功能演示")
    print("🏢" * 35)
    
    try:
        # 1. 创建位置层级
        locations = demo_create_location_hierarchy()
        
        # 2. 分配设备到位置
        demo_assign_devices_to_locations(locations)
        
        # 3. 查询位置下的设备
        demo_query_devices_by_location(locations)
        
        # 4. 位置统计
        demo_location_statistics(locations)
        
        # 5. 位置树形结构
        demo_location_tree()
        
        # 6. 位置搜索
        demo_search_locations()
        
        # 7. 实际应用场景
        demo_practical_scenario()
        
        print("\n" + "=" * 70)
        print("  ✅ 演示完成！")
        print("=" * 70)
        
        print("\n📚 API使用说明:")
        print("   • GET    /locations/                - 获取位置列表")
        print("   • POST   /locations/                - 创建位置")
        print("   • GET    /locations/{id}            - 获取位置详情")
        print("   • PUT    /locations/{id}            - 更新位置")
        print("   • DELETE /locations/{id}            - 删除位置")
        print("   • GET    /locations/tree            - 获取位置树")
        print("   • GET    /locations/search          - 搜索位置")
        print("   • GET    /locations/{id}/children   - 获取子位置")
        print("   • GET    /locations/{id}/devices    - 获取位置设备")
        print("   • POST   /locations/{id}/devices    - 分配设备到位置")
        print("   • GET    /locations/{id}/statistics - 位置统计")
        
        print("\n💡 现在你可以:")
        print("   1. 轻松查询 'A栋3单元1309' 的所有设备")
        print("   2. 统计任意位置的能耗数据")
        print("   3. 按楼栋/单元/房间管理设备")
        print("   4. 展示完整的位置层级树")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
