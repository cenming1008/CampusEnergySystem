"""
设备管理服务层
封装设备相关的业务逻辑
"""
from typing import List, Optional
from sqlmodel import Session, select

from app.models.tables import Device
from app.core.exceptions import ResourceNotFoundException, DatabaseException


class DeviceService:
    """设备服务类"""
    
    @staticmethod
    def get_all_devices(session: Session) -> List[Device]:
        """获取所有设备列表"""
        statement = select(Device).order_by(Device.id)
        return list(session.exec(statement).all())
    
    @staticmethod
    def get_device_by_id(session: Session, device_id: int) -> Device:
        """根据ID获取设备"""
        device = session.get(Device, device_id)
        if not device:
            raise ResourceNotFoundException("设备", device_id)
        return device
    
    @staticmethod
    def create_device(session: Session, device: Device) -> Device:
        """创建新设备"""
        try:
            session.add(device)
            session.commit()
            session.refresh(device)
            return device
        except Exception as e:
            session.rollback()
            # 检查是否是重复的SN
            existing = session.exec(
                select(Device).where(Device.sn == device.sn)
            ).first()
            if existing:
                return existing
            raise DatabaseException(f"创建设备失败: {str(e)}")
    
    @staticmethod
    def update_device(
        session: Session,
        device_id: int,
        name: str,
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> Device:
        """更新设备信息"""
        device = DeviceService.get_device_by_id(session, device_id)
        
        device.name = name
        if location is not None:
            device.location = location
        if description is not None:
            device.description = description
        
        session.add(device)
        session.commit()
        session.refresh(device)
        return device
    
    @staticmethod
    def delete_device(session: Session, device_id: int) -> None:
        """删除设备"""
        device = DeviceService.get_device_by_id(session, device_id)
        session.delete(device)
        session.commit()
    
    @staticmethod
    def toggle_device_status(session: Session, device_id: int, active: bool) -> Device:
        """切换设备状态"""
        device = DeviceService.get_device_by_id(session, device_id)
        device.is_active = active
        session.add(device)
        session.commit()
        session.refresh(device)
        return device

