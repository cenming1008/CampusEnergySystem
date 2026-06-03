"""
位置管理服务层
封装位置层级相关的业务逻辑
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, func
from app.core.logger import logger

from app.domain.location_rules import (
    build_location_statistics_payload,
    build_location_tree,
    calculate_location_path_fields,
    resolve_location_reference_match,
)
from app.models.tables import Location, Device, EnergyData, LocationType
from app.core.exceptions import ResourceNotFoundException, DatabaseException


class LocationService:
    """
    位置管理服务类
    
    提供位置层级相关的业务逻辑，包括：
    - 创建和管理位置
    - 查询位置层级
    - 位置下设备管理
    - 位置能耗统计
    """
    
    # ==================== 位置管理 ====================
    
    @staticmethod
    def create_location(
        session: Session,
        name: str,
        location_type: str,
        parent_id: Optional[int] = None,
        code: Optional[str] = None,
        description: Optional[str] = None,
        area_sqm: Optional[float] = None,
        manager: Optional[str] = None,
        contact: Optional[str] = None
    ) -> Location:
        """
        创建位置
        
        Args:
            session: 数据库会话
            name: 位置名称
            location_type: 位置类型
            parent_id: 父级位置ID
            code: 位置编码
            description: 描述
            area_sqm: 面积
            manager: 负责人
            contact: 联系方式
            
        Returns:
            创建的位置对象
        """
        # 验证位置类型
        valid_types = [t.value for t in LocationType]
        if location_type not in valid_types:
            raise ValueError(
                f"无效的位置类型: {location_type}。"
                f"有效值: {', '.join(valid_types)}"
            )
        
        # 验证父位置是否存在
        level = 0
        full_path = f"/{name}"
        
        if parent_id:
            parent = session.get(Location, parent_id)
            if not parent:
                raise ResourceNotFoundException("父级位置", parent_id)
            
            level = parent.level + 1
            full_path = f"{parent.full_path}/{name}"
        
        # 创建位置
        location = Location(
            name=name,
            location_type=location_type,
            parent_id=parent_id,
            code=code,
            description=description,
            area_sqm=area_sqm,
            manager=manager,
            contact=contact,
            level=level,
            full_path=full_path
        )
        
        session.add(location)
        session.commit()
        session.refresh(location)
        
        logger.info(
            f"创建位置: name={name}, type={location_type}, "
            f"id={location.id}, path={full_path}"
        )
        
        return location
    
    @staticmethod
    def get_location_by_id(session: Session, location_id: int) -> Location:
        """根据ID获取位置"""
        location = session.get(Location, location_id)
        if not location:
            raise ResourceNotFoundException("位置", location_id)
        return location
    
    @staticmethod
    def get_location_by_code(session: Session, code: str) -> Optional[Location]:
        """根据编码获取位置"""
        statement = select(Location).where(Location.code == code)
        return session.exec(statement).first()

    @staticmethod
    def resolve_location_reference(session: Session, raw_value: Optional[str]) -> Optional[Location]:
        """根据位置文本解析 Location，优先 full_path / code / name。"""
        normalized = raw_value.strip() if raw_value else ""
        if not normalized:
            return None

        by_full_path = session.exec(
            select(Location).where(Location.full_path == normalized)
        ).first()
        full_path_match = resolve_location_reference_match(
            raw_value=raw_value,
            by_full_path=by_full_path,
            by_code=None,
            by_name=[],
        )
        if full_path_match:
            return full_path_match

        by_code = session.exec(
            select(Location).where(Location.code == normalized)
        ).first()
        code_match = resolve_location_reference_match(
            raw_value=raw_value,
            by_full_path=None,
            by_code=by_code,
            by_name=[],
        )
        if code_match:
            return code_match

        by_name = list(
            session.exec(
                select(Location)
                .where(Location.name == normalized)
                .order_by(Location.level.desc(), Location.id.desc())
            ).all()
        )
        return resolve_location_reference_match(
            raw_value=raw_value,
            by_full_path=None,
            by_code=None,
            by_name=by_name,
        )
    
    @staticmethod
    def get_all_locations(
        session: Session,
        location_type: Optional[str] = None,
        parent_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[Location]:
        """
        获取位置列表
        
        Args:
            session: 数据库会话
            location_type: 位置类型筛选
            parent_id: 父级ID筛选（None表示顶级位置）
            is_active: 状态筛选
        """
        statement = select(Location)
        
        if location_type:
            statement = statement.where(Location.location_type == location_type)
        
        if parent_id is not None:
            statement = statement.where(Location.parent_id == parent_id)
        elif parent_id is None and location_type is None:
            # 如果没有指定 parent_id 且没有 type，默认返回所有
            pass
        
        if is_active is not None:
            statement = statement.where(Location.is_active == is_active)
        
        statement = statement.order_by(Location.level, Location.name)
        return list(session.exec(statement).all())
    
    @staticmethod
    def get_root_locations(session: Session) -> List[Location]:
        """获取所有顶级位置（没有父级的位置）"""
        statement = (
            select(Location)
            .where(Location.parent_id == None)
            .order_by(Location.name)
        )
        return list(session.exec(statement).all())
    
    @staticmethod
    def get_child_locations(
        session: Session, 
        parent_id: int,
        recursive: bool = False
    ) -> List[Location]:
        """
        获取子位置
        
        Args:
            session: 数据库会话
            parent_id: 父级位置ID
            recursive: 是否递归获取所有子孙位置
        """
        if not recursive:
            # 只获取直接子位置
            statement = (
                select(Location)
                .where(Location.parent_id == parent_id)
                .order_by(Location.name)
            )
            return list(session.exec(statement).all())
        else:
            # 递归获取所有子孙位置
            parent = LocationService.get_location_by_id(session, parent_id)
            statement = (
                select(Location)
                .where(Location.full_path.startswith(parent.full_path + "/"))
                .order_by(Location.level, Location.name)
            )
            return list(session.exec(statement).all())
    
    @staticmethod
    def update_location(
        session: Session,
        location_id: int,
        **update_fields
    ) -> Location:
        """
        更新位置信息
        
        Args:
            session: 数据库会话
            location_id: 位置ID
            **update_fields: 要更新的字段
        """
        location = LocationService.get_location_by_id(session, location_id)
        
        # 特殊处理：如果更新了 name 或 parent_id，需要重新计算 full_path
        name_changed = 'name' in update_fields
        parent_changed = 'parent_id' in update_fields
        
        # 更新字段
        for field, value in update_fields.items():
            if hasattr(location, field) and value is not None:
                setattr(location, field, value)
        
        # 重新计算路径
        if name_changed or parent_changed:
            location = LocationService._recalculate_path(session, location)
        
        location.updated_at = datetime.now()
        
        session.add(location)
        session.commit()
        session.refresh(location)
        
        logger.info(f"更新位置: id={location_id}")
        
        return location
    
    @staticmethod
    def _recalculate_path(session: Session, location: Location) -> Location:
        """重新计算位置的 full_path 和 level"""
        parent = session.get(Location, location.parent_id) if location.parent_id else None
        path_fields = calculate_location_path_fields(location.name, parent)
        location.level = path_fields["level"]
        location.full_path = path_fields["full_path"]
        return location
    
    @staticmethod
    def delete_location(
        session: Session,
        location_id: int,
        force: bool = False
    ) -> bool:
        """
        删除位置
        
        Args:
            session: 数据库会话
            location_id: 位置ID
            force: 是否强制删除（包括子位置和设备）
        """
        location = LocationService.get_location_by_id(session, location_id)
        
        # 检查是否有子位置
        children = LocationService.get_child_locations(session, location_id)
        if children and not force:
            raise DatabaseException(
                f"位置 {location.name} 有 {len(children)} 个子位置，"
                "请先删除子位置或使用 force=True 强制删除"
            )
        
        # 检查是否有关联设备
        devices = LocationService.get_devices_by_location(session, location_id)
        if devices and not force:
            raise DatabaseException(
                f"位置 {location.name} 有 {len(devices)} 个设备，"
                "请先移除设备或使用 force=True 强制删除"
            )
        
        # 删除
        if force:
            # 删除所有子位置
            for child in children:
                session.delete(child)
            
            # 解除设备关联
            for device in devices:
                device.location_id = None
                session.add(device)
        
        session.delete(location)
        session.commit()
        
        logger.info(f"删除位置: id={location_id}, name={location.name}")
        return True
    
    # ==================== 设备管理 ====================
    
    @staticmethod
    def get_devices_by_location(
        session: Session,
        location_id: int,
        recursive: bool = False,
        energy_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Device]:
        """
        获取位置下的设备
        
        Args:
            session: 数据库会话
            location_id: 位置ID
            recursive: 是否递归获取子位置的设备
            energy_type: 能源类型筛选
            is_active: 状态筛选
        """
        if not recursive:
            # 只获取当前位置的设备
            statement = select(Device).where(Device.location_id == location_id)
        else:
            # 获取当前位置及所有子位置的设备
            location = LocationService.get_location_by_id(session, location_id)
            
            # 获取所有子位置ID
            child_locations = LocationService.get_child_locations(
                session, location_id, recursive=True
            )
            location_ids = [location.id] + [loc.id for loc in child_locations]
            
            statement = select(Device).where(Device.location_id.in_(location_ids))
        
        # 应用筛选
        if energy_type:
            statement = statement.where(Device.energy_type == energy_type)
        
        if is_active is not None:
            statement = statement.where(Device.is_active == is_active)
        
        statement = statement.order_by(Device.id)
        return list(session.exec(statement).all())
    
    @staticmethod
    def assign_device_to_location(
        session: Session,
        device_id: int,
        location_id: int
    ) -> Device:
        """将设备分配到位置"""
        device = session.get(Device, device_id)
        if not device:
            raise ResourceNotFoundException("设备", device_id)
        
        location = LocationService.get_location_by_id(session, location_id)
        
        device.location_id = location_id
        device.location = location.full_path  # 同时更新字符串字段
        device.updated_at = datetime.now()
        
        session.add(device)
        session.commit()
        session.refresh(device)
        
        logger.info(
            f"设备分配到位置: device_id={device_id}, "
            f"location_id={location_id}, location={location.full_path}"
        )
        
        return device
    
    # ==================== 统计分析 ====================
    
    @staticmethod
    def get_location_statistics(
        session: Session,
        location_id: int,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        获取位置统计信息
        
        Args:
            session: 数据库会话
            location_id: 位置ID
            recursive: 是否包含子位置
        """
        location = LocationService.get_location_by_id(session, location_id)
        
        # 获取设备
        devices = LocationService.get_devices_by_location(
            session, location_id, recursive=recursive
        )
        
        # 子位置统计
        child_locations = LocationService.get_child_locations(
            session, location_id, recursive=False
        )
        return build_location_statistics_payload(location, devices, child_locations)
    
    @staticmethod
    def get_location_tree(
        session: Session,
        root_location_id: Optional[int] = None,
        max_depth: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取位置树形结构
        
        Args:
            session: 数据库会话
            root_location_id: 根位置ID（None表示从顶级开始）
            max_depth: 最大深度
        """
        if root_location_id:
            roots = [LocationService.get_location_by_id(session, root_location_id)]
        else:
            roots = LocationService.get_root_locations(session)
        
        def get_device_count(location: Location) -> int:
            devices = LocationService.get_devices_by_location(
                session, location.id, recursive=False
            )
            return len(devices)

        def get_children(location: Location) -> List[Location]:
            return LocationService.get_child_locations(
                session, location.id, recursive=False
            )

        return build_location_tree(
            roots,
            max_depth=max_depth,
            get_device_count=get_device_count,
            get_child_locations=get_children,
        )
    
    @staticmethod
    def search_locations(
        session: Session,
        keyword: str
    ) -> List[Location]:
        """
        搜索位置（按名称、编码、描述）
        
        Args:
            session: 数据库会话
            keyword: 搜索关键词
        """
        keyword_pattern = f"%{keyword}%"
        statement = select(Location).where(
            (Location.name.like(keyword_pattern)) |
            (Location.code.like(keyword_pattern)) |
            (Location.description.like(keyword_pattern))
        ).order_by(Location.level, Location.name)
        
        return list(session.exec(statement).all())
