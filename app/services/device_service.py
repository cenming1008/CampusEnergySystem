"""
设备管理服务层 - 统一的设备和能源数据管理
封装设备相关的业务逻辑，整合能源数据处理
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select
from loguru import logger

from app.models.tables import Device, EnergyData, DeviceCategory, EnergyType
from app.core.exceptions import ResourceNotFoundException, DatabaseException
from app.core.device_registry import device_registry
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
        statement = select(Device)
        
        if energy_type:
            statement = statement.where(Device.energy_type == energy_type)
        
        if category:
            statement = statement.where(Device.device_category == category)
        
        if is_active is not None:
            statement = statement.where(Device.is_active == is_active)
        
        statement = statement.order_by(Device.id)
        return list(session.exec(statement).all())
    
    @staticmethod
    def get_device_by_id(session: Session, device_id: int) -> Device:
        """根据ID获取设备"""
        device = session.get(Device, device_id)
        if not device:
            raise ResourceNotFoundException("设备", device_id)
        return device
    
    @staticmethod
    def get_device_by_sn(session: Session, sn: str) -> Optional[Device]:
        """根据序列号获取设备"""
        statement = select(Device).where(Device.sn == sn)
        return session.exec(statement).first()
    
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
        # 检查设备类型是否在注册表中
        config = device_registry.get(device_type)
        if not config:
            available_types = device_registry.list_device_types()
            raise ValueError(
                f"不支持的设备类型: {device_type}。"
                f"支持的类型: {', '.join(available_types)}"
            )
        
        # 检查序列号是否已存在
        existing = DeviceService.get_device_by_sn(session, sn)
        if existing:
            logger.warning(f"设备序列号 {sn} 已存在，返回现有设备")
            return existing
        
        # 使用配置自动填充字段
        device = Device(
            name=name,
            sn=sn,
            device_type=device_type,
            device_category=config.category.value,
            energy_type=config.energy_type.value,
            location=location,
            description=description or f"{config.name_zh}设备",
            rated_capacity=rated_capacity or config.default_capacity,
            unit=config.unit,
            is_active=True,
            **extra_fields
        )
        
        try:
            session.add(device)
            session.commit()
            session.refresh(device)
            
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
        device.updated_at = datetime.now()
        session.add(device)
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
        
        # 获取设备类型配置
        config = device_registry.get(device.device_type)
        
        # ========== 字段映射（在验证之前进行） ==========
        # 1. flow_rate 字段映射：power 可以作为 flow_rate 的替代
        if "flow_rate" not in data and "power" in data:
            data["flow_rate"] = data["power"]
        
        # 2. heat_flow 字段映射：heat_power 可以作为 heat_flow 的替代
        if "heat_flow" not in data and "heat_power" in data:
            data["heat_flow"] = data["heat_power"]
        
        # ========== 验证必需字段 ==========
        if config:
            for field in config.required_fields:
                if field not in data or data[field] is None:
                    raise ValueError(f"缺少必需字段: {field}")
        
        # 提取通用字段
        consumption = data.get("consumption")
        if consumption is None:
            raise ValueError("consumption 字段是必需的")
        
        flow_rate = data.get("flow_rate")
        
        # 提取可选字段
        optional_fields = {}
        optional_field_names = [
            "voltage", "current", "power_factor",
            "pressure", "temperature",
            "supply_temp", "return_temp", "heat_flow",
            "quality_index"
        ]
        
        for field in optional_field_names:
            if field in data and data[field] is not None:
                optional_fields[field] = data[field]
        
        # 调用 EnergyService 保存数据
        energy_data = EnergyService.save_energy_data(
            session=session,
            device_id=device_id,
            energy_type=device.energy_type,
            consumption=consumption,
            flow_rate=flow_rate,
            timestamp=timestamp,
            **optional_fields
        )
        
        logger.info(
            f"📊 设备数据上报成功: 设备ID={device_id}, "
            f"类型={device.device_type}, 消耗={consumption}"
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
            "device_type": config.device_type,
            "category": config.category.value,
            "energy_type": config.energy_type.value,
            "name_zh": config.name_zh,
            "name_en": config.name_en,
            "unit": config.unit,
            "default_capacity": config.default_capacity,
            "required_fields": config.required_fields,
            "optional_fields": config.optional_fields,
            "icon": config.icon,
            "color": config.color,
        }

