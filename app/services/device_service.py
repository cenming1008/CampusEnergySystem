"""
设备管理服务层 - 统一的设备和能源数据管理
封装设备相关的业务逻辑，整合能源数据处理
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select
from app.core.logger import logger

from app.domain.device_payloads import (
    build_device_create_fields,
    describe_device_type_semantics,
    describe_energy_data_fields,
    get_device_type_config,
    normalize_device_report_payload,
)
from app.models.tables import Device, EnergyData, DeviceCategory, EnergyType, DeviceControlLog
from app.core.exceptions import ResourceNotFoundException, DatabaseException
from app.core.device_registry import device_registry
from app.repositories.device_repository import DeviceRepository
from app.services.energy_service import EnergyService


class DeviceService:
    """设备服务类 - 统一管理设备和能源数据"""
    
    # ==================== 设备管理 ====================
    
    @staticmethod
    def get_all_devices(
        session: Session,
        energy_type: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Device]:
        """
        获取设备列表，支持多种筛选条件
        
        Args:
            session: 数据库会话
            energy_type: 能源类型筛选
            category: 设备类别筛选
            is_active: 状态筛选
        """
        return DeviceRepository.list_devices(
            session,
            energy_type=energy_type,
            category=category,
            is_active=is_active,
        )
    
    @staticmethod
    def get_device_by_id(session: Session, device_id: int) -> Device:
        """根据ID获取设备"""
        device = DeviceRepository.get_by_id(session, device_id)
        if not device:
            raise ResourceNotFoundException("设备", device_id)
        return device
    
    @staticmethod
    def get_device_by_sn(session: Session, sn: str) -> Optional[Device]:
        """根据序列号获取设备"""
        return DeviceRepository.get_by_sn(session, sn)
    
    @staticmethod
    def create_device_smart(
        session: Session,
        name: str,
        sn: str,
        device_type: str,
        location: Optional[str] = None,
        description: Optional[str] = None,
        rated_capacity: Optional[float] = None,
        **extra_fields
    ) -> Device:
        """
        智能创建设备 - 根据设备类型自动配置
        
        Args:
            session: 数据库会话
            name: 设备名称
            sn: 设备序列号
            device_type: 设备类型（如 "water_meter", "solar"）
            location: 位置
            description: 描述
            rated_capacity: 额定容量（可选，不提供则使用默认值）
            **extra_fields: 其他字段
        
        Returns:
            创建的设备对象
        """
        config = get_device_type_config(device_type)
        
        # 检查序列号是否已存在
        existing = DeviceService.get_device_by_sn(session, sn)
        if existing:
            logger.warning(f"设备序列号 {sn} 已存在，返回现有设备")
            return existing
        
        device = Device(
            **build_device_create_fields(
                name=name,
                sn=sn,
                device_type=device_type,
                location=location,
                description=description,
                rated_capacity=rated_capacity,
                **extra_fields,
            )
        )
        
        try:
            DeviceRepository.save(session, device)
            
            logger.info(
                f"✅ 创建设备成功: {name} (类型={device_type}, "
                f"能源={config.energy_type.value}, 类别={config.category.value})"
            )
            
            return device
        except Exception as e:
            session.rollback()
            raise DatabaseException(f"创建设备失败: {str(e)}")
    
    @staticmethod
    def create_device(session: Session, device: Device) -> Device:
        """
        创建新设备（传统方式）
        保留此方法用于向后兼容
        """
        try:
            # 如果提供了 device_type，尝试自动配置
            if device.device_type:
                config = device_registry.get(device.device_type)
                if config:
                    # 自动填充未设置的字段
                    if not device.device_category:
                        device.device_category = config.category.value
                    if not device.energy_type:
                        device.energy_type = config.energy_type.value
                    if not device.unit:
                        device.unit = config.unit
                    if not device.rated_capacity and config.default_capacity:
                        device.rated_capacity = config.default_capacity
            
            DeviceRepository.save(session, device)
            return device
        except Exception as e:
            session.rollback()
            # 检查是否是重复的SN
            existing = DeviceRepository.get_by_sn(session, device.sn)
            if existing:
                return existing
            raise DatabaseException(f"创建设备失败: {str(e)}")
    
    @staticmethod
    def update_device(
        session: Session,
        device_id: int,
        name: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        rated_capacity: Optional[float] = None
    ) -> Device:
        """更新设备信息"""
        device = DeviceService.get_device_by_id(session, device_id)
        
        if name is not None:
            device.name = name
        if location is not None:
            device.location = location
        if description is not None:
            device.description = description
        if rated_capacity is not None:
            device.rated_capacity = rated_capacity
        
        device.updated_at = datetime.now()
        
        return DeviceRepository.save(session, device)
    
    @staticmethod
    def delete_device(session: Session, device_id: int) -> None:
        """删除设备"""
        device = DeviceService.get_device_by_id(session, device_id)
        DeviceRepository.delete(session, device)
    
    @staticmethod
    def toggle_device_status(
        session: Session,
        device_id: int,
        active: bool,
        operator: Optional[str] = None,
        reason: Optional[str] = None,
        command_source: str = "api",
    ) -> Device:
        """切换设备状态"""
        device = DeviceService.get_device_by_id(session, device_id)
        previous_status = device.is_active
        device.is_active = active
        device.updated_at = datetime.now()
        session.add(device)

        control_log = DeviceControlLog(
            device_id=device.id,
            action="start" if active else "stop",
            target_status=active,
            previous_status=previous_status,
            operator=operator,
            command_source=command_source,
            result="success",
            reason=reason,
        )
        session.add(control_log)
        session.commit()
        session.refresh(device)
        return device
    
    # ==================== 能源数据管理（整合） ====================
    
    @staticmethod
    def report_device_data(
        session: Session,
        device_id: int,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> EnergyData:
        """
        统一的设备数据上报接口
        根据设备类型自动处理数据字段
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            data: 数据字典，包含 consumption, flow_rate 等字段
            timestamp: 时间戳
        
        Returns:
            保存的能源数据对象
        
        示例:
            # 电力设备
            report_device_data(session, 1, {
                "consumption": 100.5,
                "power": 50.2,
                "voltage": 220,
                "current": 15.5
            })
            
            # 水表
            report_device_data(session, 2, {
                "consumption": 10.5,
                "flow_rate": 2.3,
                "pressure": 0.3
            })
        """
        # 获取设备信息
        device = DeviceService.get_device_by_id(session, device_id)
        payload = normalize_device_report_payload(device.device_type, data)
        
        # 调用 EnergyService 保存数据
        energy_data = EnergyService.save_energy_data(
            session=session,
            device_id=device_id,
            energy_type=device.energy_type,
            consumption=payload.consumption,
            flow_rate=payload.flow_rate,
            timestamp=timestamp,
            **payload.optional_fields
        )
        
        logger.info(
            f"📊 设备数据上报成功: 设备ID={device_id}, "
            f"类型={device.device_type}, 消耗={payload.consumption}"
        )
        
        return energy_data
    
    @staticmethod
    def get_device_data(
        session: Session,
        device_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[EnergyData]:
        """
        获取设备的能源数据
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回条数限制
        """
        device = DeviceService.get_device_by_id(session, device_id)
        
        return EnergyService.get_energy_data(
            session=session,
            device_id=device_id,
            energy_type=device.energy_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
    
    @staticmethod
    def get_device_statistics(
        session: Session,
        device_id: int,
        start_time: datetime,
        end_time: datetime,
        period_type: str = "day"
    ) -> Dict:
        """
        获取设备的统计数据
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            start_time: 开始时间
            end_time: 结束时间
            period_type: 统计周期
        """
        device = DeviceService.get_device_by_id(session, device_id)
        
        return EnergyService.calculate_statistics(
            session=session,
            device_id=device_id,
            energy_type=device.energy_type,
            start_time=start_time,
            end_time=end_time,
            period_type=period_type
        )
    
    # ==================== 设备类型信息 ====================
    
    @staticmethod
    def get_device_types() -> List[Dict[str, Any]]:
        """获取所有支持的设备类型"""
        return device_registry.to_dict()
    
    @staticmethod
    def get_device_type_info(device_type: str) -> Optional[Dict[str, Any]]:
        """获取指定设备类型的信息"""
        config = device_registry.get(device_type)
        if not config:
            return None
        
        return {
            **describe_device_type_semantics(device_type),
            "energy_data_fields": describe_energy_data_fields(device_type),
        }

    @staticmethod
    def get_device_semantic_profile(session: Session, device_id: int) -> Dict[str, Any]:
        """返回单个设备的第一批兼容语义。"""
        device = DeviceService.get_device_by_id(session, device_id)
        device_type_profile = describe_device_type_semantics(device.device_type)
        return {
            "device_id": device.id,
            "name": device.name,
            "device_type": device.device_type,
            "device_category": device.device_category,
            "energy_type": device.energy_type,
            "unit": device.unit,
            "rated_capacity": device.rated_capacity,
            "object_role": device_type_profile["object_role"],
            "metering_role": device_type_profile["metering_role"],
            "point_kind": device_type_profile["point_kind"],
            "measurement_subject": device_type_profile["measurement_subject"],
            "consumption_unit": device_type_profile["consumption_unit"],
            "flow_unit": device_type_profile["flow_unit"],
            "energy_data_fields": describe_energy_data_fields(device.device_type),
        }
