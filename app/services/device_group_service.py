"""
设备分组管理服务层
封装设备分组相关的业务逻辑
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, func
from app.core.logger import logger

from app.models.tables import Device, DeviceGroup, DeviceGroupMembership
from app.core.exceptions import ResourceNotFoundException, DatabaseException


class DeviceGroupService:
    """
    设备分组管理服务类
    
    提供设备分组相关的业务逻辑，包括：
    - 创建和管理分组
    - 添加/移除设备到分组
    - 查询分组设备
    - 分组统计分析
    """
    
    # ==================== 分组管理 ====================
    
    @staticmethod
    def create_group(
        session: Session,
        name: str,
        code: Optional[str] = None,
        description: Optional[str] = None,
        group_type: Optional[str] = None,
        parent_id: Optional[int] = None,
        manager: Optional[str] = None,
        contact: Optional[str] = None
    ) -> DeviceGroup:
        """
        创建设备分组
        
        Args:
            session: 数据库会话
            name: 分组名称
            code: 分组编码
            description: 分组描述
            group_type: 分组类型（production/office/critical/backup）
            parent_id: 父分组ID
            manager: 负责人
            contact: 联系方式
            
        Returns:
            创建的分组对象
        """
        # 验证父分组是否存在
        if parent_id:
            parent = session.get(DeviceGroup, parent_id)
            if not parent:
                raise ResourceNotFoundException("父分组", parent_id)
        
        # 创建分组
        group = DeviceGroup(
            name=name,
            code=code,
            description=description,
            group_type=group_type,
            parent_id=parent_id,
            manager=manager,
            contact=contact
        )
        
        session.add(group)
        session.commit()
        session.refresh(group)
        
        logger.info(f"创建设备分组: name={name}, id={group.id}")
        
        return group
    
    @staticmethod
    def get_group_by_id(session: Session, group_id: int) -> DeviceGroup:
        """根据ID获取分组"""
        group = session.get(DeviceGroup, group_id)
        if not group:
            raise ResourceNotFoundException("设备分组", group_id)
        return group
    
    @staticmethod
    def get_group_by_code(session: Session, code: str) -> Optional[DeviceGroup]:
        """根据编码获取分组"""
        statement = select(DeviceGroup).where(DeviceGroup.code == code)
        return session.exec(statement).first()
    
    @staticmethod
    def get_all_groups(
        session: Session,
        group_type: Optional[str] = None,
        parent_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[DeviceGroup]:
        """
        获取分组列表
        
        Args:
            session: 数据库会话
            group_type: 分组类型筛选
            parent_id: 父分组ID筛选
            is_active: 状态筛选
        """
        statement = select(DeviceGroup)
        
        if group_type:
            statement = statement.where(DeviceGroup.group_type == group_type)
        
        if parent_id is not None:
            statement = statement.where(DeviceGroup.parent_id == parent_id)
        
        if is_active is not None:
            statement = statement.where(DeviceGroup.is_active == is_active)
        
        statement = statement.order_by(DeviceGroup.name)
        return list(session.exec(statement).all())
    
    @staticmethod
    def update_group(
        session: Session,
        group_id: int,
        **update_fields
    ) -> DeviceGroup:
        """
        更新分组信息
        
        Args:
            session: 数据库会话
            group_id: 分组ID
            **update_fields: 要更新的字段
        """
        group = DeviceGroupService.get_group_by_id(session, group_id)
        
        # 更新字段
        for field, value in update_fields.items():
            if hasattr(group, field) and value is not None:
                setattr(group, field, value)
        
        group.updated_at = datetime.now()
        
        session.add(group)
        session.commit()
        session.refresh(group)
        
        logger.info(f"更新设备分组: id={group_id}")
        
        return group
    
    @staticmethod
    def delete_group(
        session: Session,
        group_id: int,
        force: bool = False
    ) -> bool:
        """
        删除分组
        
        Args:
            session: 数据库会话
            group_id: 分组ID
            force: 是否强制删除（包括关联的设备）
        """
        group = DeviceGroupService.get_group_by_id(session, group_id)
        
        # 检查是否有设备
        device_count = DeviceGroupService.get_device_count(session, group_id)
        if device_count > 0 and not force:
            raise DatabaseException(
                f"分组 {group.name} 有 {device_count} 个设备，"
                "请先移除设备或使用 force=True 强制删除"
            )
        
        # 删除所有关联关系
        if force:
            statement = select(DeviceGroupMembership).where(
                DeviceGroupMembership.group_id == group_id
            )
            memberships = session.exec(statement).all()
            for membership in memberships:
                session.delete(membership)
        
        # 删除分组
        session.delete(group)
        session.commit()
        
        logger.info(f"删除设备分组: id={group_id}, name={group.name}")
        return True
    
    # ==================== 设备-分组关联管理 ====================
    
    @staticmethod
    def add_device_to_group(
        session: Session,
        device_id: int,
        group_id: int,
        note: Optional[str] = None
    ) -> DeviceGroupMembership:
        """
        将设备添加到分组
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            group_id: 分组ID
            note: 备注
            
        Returns:
            创建的关联记录
        """
        # 验证设备是否存在
        device = session.get(Device, device_id)
        if not device:
            raise ResourceNotFoundException("设备", device_id)
        
        # 验证分组是否存在
        group = DeviceGroupService.get_group_by_id(session, group_id)
        
        # 检查是否已经在分组中
        existing = session.exec(
            select(DeviceGroupMembership).where(
                DeviceGroupMembership.device_id == device_id,
                DeviceGroupMembership.group_id == group_id
            )
        ).first()
        
        if existing:
            raise DatabaseException(f"设备 {device.name} 已经在分组 {group.name} 中")
        
        # 创建关联
        membership = DeviceGroupMembership(
            device_id=device_id,
            group_id=group_id,
            note=note
        )
        
        session.add(membership)
        session.commit()
        session.refresh(membership)
        
        logger.info(
            f"设备加入分组: device_id={device_id}, group_id={group_id}"
        )
        
        return membership
    
    @staticmethod
    def remove_device_from_group(
        session: Session,
        device_id: int,
        group_id: int
    ) -> bool:
        """
        将设备从分组中移除
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            group_id: 分组ID
        """
        membership = session.exec(
            select(DeviceGroupMembership).where(
                DeviceGroupMembership.device_id == device_id,
                DeviceGroupMembership.group_id == group_id
            )
        ).first()
        
        if not membership:
            raise ResourceNotFoundException(
                f"设备 {device_id} 不在分组 {group_id} 中"
            )
        
        session.delete(membership)
        session.commit()
        
        logger.info(
            f"设备移出分组: device_id={device_id}, group_id={group_id}"
        )
        
        return True
    
    @staticmethod
    def batch_add_devices_to_group(
        session: Session,
        device_ids: List[int],
        group_id: int
    ) -> int:
        """
        批量添加设备到分组
        
        Args:
            session: 数据库会话
            device_ids: 设备ID列表
            group_id: 分组ID
            
        Returns:
            成功添加的数量
        """
        # 验证分组存在
        group = DeviceGroupService.get_group_by_id(session, group_id)
        
        count = 0
        for device_id in device_ids:
            try:
                DeviceGroupService.add_device_to_group(
                    session, device_id, group_id
                )
                count += 1
            except Exception as e:
                logger.warning(f"添加设备 {device_id} 到分组失败: {e}")
                continue
        
        logger.info(f"批量添加设备到分组: 成功 {count}/{len(device_ids)}")
        return count
    
    # ==================== 查询 ====================
    
    @staticmethod
    def get_devices_in_group(
        session: Session,
        group_id: int,
        energy_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Device]:
        """
        获取分组中的所有设备
        
        Args:
            session: 数据库会话
            group_id: 分组ID
            energy_type: 能源类型筛选
            is_active: 状态筛选
        """
        statement = (
            select(Device)
            .join(DeviceGroupMembership)
            .where(DeviceGroupMembership.group_id == group_id)
        )
        
        if energy_type:
            statement = statement.where(Device.energy_type == energy_type)
        
        if is_active is not None:
            statement = statement.where(Device.is_active == is_active)
        
        statement = statement.order_by(Device.id)
        return list(session.exec(statement).all())
    
    @staticmethod
    def get_device_groups(
        session: Session,
        device_id: int
    ) -> List[DeviceGroup]:
        """
        获取设备所属的所有分组
        
        Args:
            session: 数据库会话
            device_id: 设备ID
        """
        statement = (
            select(DeviceGroup)
            .join(DeviceGroupMembership)
            .where(DeviceGroupMembership.device_id == device_id)
            .order_by(DeviceGroup.name)
        )
        return list(session.exec(statement).all())
    
    @staticmethod
    def is_device_in_group(
        session: Session,
        device_id: int,
        group_id: int
    ) -> bool:
        """
        检查设备是否在分组中
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            group_id: 分组ID
        """
        membership = session.exec(
            select(DeviceGroupMembership).where(
                DeviceGroupMembership.device_id == device_id,
                DeviceGroupMembership.group_id == group_id
            )
        ).first()
        
        return membership is not None
    
    @staticmethod
    def get_device_count(session: Session, group_id: int) -> int:
        """获取分组中的设备数量"""
        statement = (
            select(func.count(DeviceGroupMembership.device_id))
            .where(DeviceGroupMembership.group_id == group_id)
        )
        return session.exec(statement).one()
    
    # ==================== 统计分析 ====================
    
    @staticmethod
    def get_group_statistics(
        session: Session,
        group_id: int
    ) -> Dict[str, Any]:
        """
        获取分组统计信息
        
        Args:
            session: 数据库会话
            group_id: 分组ID
        """
        group = DeviceGroupService.get_group_by_id(session, group_id)
        devices = DeviceGroupService.get_devices_in_group(session, group_id)
        
        # 按能源类型统计
        device_count_by_energy = {}
        for device in devices:
            energy_type = device.energy_type
            device_count_by_energy[energy_type] = \
                device_count_by_energy.get(energy_type, 0) + 1
        
        # 按设备类别统计
        device_count_by_category = {}
        for device in devices:
            category = device.device_category
            device_count_by_category[category] = \
                device_count_by_category.get(category, 0) + 1
        
        return {
            "group": {
                "id": group.id,
                "name": group.name,
                "code": group.code,
                "type": group.group_type,
                "description": group.description
            },
            "device_count": {
                "total": len(devices),
                "active": sum(1 for d in devices if d.is_active),
                "by_energy_type": device_count_by_energy,
                "by_category": device_count_by_category
            },
            "manager": group.manager,
            "contact": group.contact
        }
    
    @staticmethod
    def get_all_group_statistics(
        session: Session
    ) -> List[Dict[str, Any]]:
        """获取所有分组的统计信息"""
        groups = DeviceGroupService.get_all_groups(session)
        
        stats = []
        for group in groups:
            device_count = DeviceGroupService.get_device_count(
                session, group.id
            )
            stats.append({
                "id": group.id,
                "name": group.name,
                "code": group.code,
                "type": group.group_type,
                "device_count": device_count,
                "manager": group.manager
            })
        
        return stats
    
    @staticmethod
    def search_groups(
        session: Session,
        keyword: str
    ) -> List[DeviceGroup]:
        """
        搜索分组（按名称、编码、描述）
        
        Args:
            session: 数据库会话
            keyword: 搜索关键词
        """
        keyword_pattern = f"%{keyword}%"
        statement = select(DeviceGroup).where(
            (DeviceGroup.name.like(keyword_pattern)) |
            (DeviceGroup.code.like(keyword_pattern)) |
            (DeviceGroup.description.like(keyword_pattern))
        ).order_by(DeviceGroup.name)
        
        return list(session.exec(statement).all())
