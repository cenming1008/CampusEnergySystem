"""
设备类型注册表
统一管理所有设备类型的元数据和配置
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from app.models.tables import EnergyType, DeviceCategory


@dataclass
class DeviceTypeConfig:
    """设备类型配置"""
    device_type: str  # 设备类型标识（如 "water_meter"）
    category: DeviceCategory  # 设备类别枚举
    energy_type: EnergyType  # 能源类型枚举
    name_zh: str  # 中文名称
    name_en: str  # 英文名称
    unit: str  # 单位
    default_capacity: Optional[float] = None  # 默认额定容量
    
    # 数据字段配置
    required_fields: List[str] = None  # 必需字段
    optional_fields: List[str] = None  # 可选字段
    
    # 图标和颜色（用于前端展示）
    icon: Optional[str] = None
    color: Optional[str] = None
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = []
        if self.optional_fields is None:
            self.optional_fields = []


class DeviceRegistry:
    """设备类型注册表 - 单例模式"""
    
    _instance = None
    _registry: Dict[str, DeviceTypeConfig] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_registry()
        return cls._instance
    
    def _init_registry(self):
        """初始化设备类型注册表"""
        
        # ==================== 电力设备 ====================
        
        # 用电负荷设备
        self.register(DeviceTypeConfig(
            device_type="load",
            category=DeviceCategory.LOAD,
            energy_type=EnergyType.ELECTRICITY,
            name_zh="用电设备",
            name_en="Load Device",
            unit="kW",
            default_capacity=100.0,
            required_fields=["consumption", "power"],
            optional_fields=["voltage", "current", "power_factor"],
            icon="⚡",
            color="#FFB800"
        ))
        
        # 光伏发电
        self.register(DeviceTypeConfig(
            device_type="solar",
            category=DeviceCategory.SOLAR,
            energy_type=EnergyType.ELECTRICITY,
            name_zh="光伏发电",
            name_en="Solar Panel",
            unit="kW",
            default_capacity=50.0,
            required_fields=["consumption", "power"],  # consumption 为负值表示发电
            optional_fields=["voltage", "current", "irradiance", "temperature"],
            icon="☀️",
            color="#FFA500"
        ))
        
        # 风力发电
        self.register(DeviceTypeConfig(
            device_type="wind",
            category=DeviceCategory.WIND,
            energy_type=EnergyType.ELECTRICITY,
            name_zh="风力发电",
            name_en="Wind Turbine",
            unit="kW",
            default_capacity=200.0,
            required_fields=["consumption", "power"],
            optional_fields=["voltage", "current", "wind_speed"],
            icon="💨",
            color="#00BFFF"
        ))
        
        # 储能设备
        self.register(DeviceTypeConfig(
            device_type="storage",
            category=DeviceCategory.STORAGE,
            energy_type=EnergyType.ELECTRICITY,
            name_zh="储能设备",
            name_en="Energy Storage",
            unit="kWh",
            default_capacity=500.0,
            required_fields=["consumption", "power"],
            optional_fields=["voltage", "current", "temperature", "soc"],  # soc: 荷电状态（可选）
            icon="🔋",
            color="#4CAF50"
        ))
        
        # 充电桩
        self.register(DeviceTypeConfig(
            device_type="charger",
            category=DeviceCategory.CHARGER,
            energy_type=EnergyType.ELECTRICITY,
            name_zh="充电桩",
            name_en="EV Charger",
            unit="kW",
            default_capacity=60.0,
            required_fields=["consumption", "power"],
            optional_fields=["voltage", "current", "charging_status"],
            icon="🔌",
            color="#9C27B0"
        ))
        
        # ==================== 水系统 ====================
        
        # 水表
        self.register(DeviceTypeConfig(
            device_type="water_meter",
            category=DeviceCategory.WATER_METER,
            energy_type=EnergyType.WATER,
            name_zh="水表",
            name_en="Water Meter",
            unit="m³/h",
            default_capacity=50.0,
            required_fields=["consumption", "flow_rate"],
            optional_fields=["pressure", "temperature", "quality_index"],
            icon="💧",
            color="#2196F3"
        ))
        
        # ==================== 燃气系统 ====================
        
        # 燃气表
        self.register(DeviceTypeConfig(
            device_type="gas_meter",
            category=DeviceCategory.GAS_METER,
            energy_type=EnergyType.GAS,
            name_zh="燃气表",
            name_en="Gas Meter",
            unit="m³/h",
            default_capacity=100.0,
            required_fields=["consumption", "flow_rate"],
            optional_fields=["pressure", "temperature", "quality_index"],
            icon="🔥",
            color="#FF5722"
        ))
        
        # ==================== 热力系统 ====================
        
        # 热量表
        self.register(DeviceTypeConfig(
            device_type="heat_meter",
            category=DeviceCategory.HEAT_METER,
            energy_type=EnergyType.HEAT,
            name_zh="热量表",
            name_en="Heat Meter",
            unit="GJ/h",
            default_capacity=10.0,
            required_fields=["consumption", "heat_flow"],
            optional_fields=["supply_temp", "return_temp", "flow_rate", "pressure"],
            icon="🌡️",
            color="#E91E63"
        ))
        
        # ==================== 制冷系统 ====================
        
        # 冷量表
        self.register(DeviceTypeConfig(
            device_type="cooling_meter",
            category=DeviceCategory.COOLING_METER,
            energy_type=EnergyType.COOLING,
            name_zh="冷量表",
            name_en="Cooling Meter",
            unit="kW",
            default_capacity=200.0,
            required_fields=["consumption", "flow_rate"],
            optional_fields=["supply_temp", "return_temp", "pressure"],
            icon="❄️",
            color="#00BCD4"
        ))
        
        # ==================== 蒸汽系统 ====================
        
        # 蒸汽表
        self.register(DeviceTypeConfig(
            device_type="steam_meter",
            category=DeviceCategory.HEAT_METER,  # 复用热量表类别
            energy_type=EnergyType.STEAM,
            name_zh="蒸汽表",
            name_en="Steam Meter",
            unit="t/h",
            default_capacity=5.0,
            required_fields=["consumption", "flow_rate"],
            optional_fields=["pressure", "temperature", "quality_index"],
            icon="💨",
            color="#607D8B"
        ))
    
    def register(self, config: DeviceTypeConfig):
        """注册设备类型"""
        self._registry[config.device_type] = config
    
    def get(self, device_type: str) -> Optional[DeviceTypeConfig]:
        """获取设备类型配置"""
        return self._registry.get(device_type)
    
    def get_all(self) -> Dict[str, DeviceTypeConfig]:
        """获取所有设备类型配置"""
        return self._registry.copy()
    
    def get_by_category(self, category: DeviceCategory) -> List[DeviceTypeConfig]:
        """按设备类别获取配置"""
        return [
            config for config in self._registry.values()
            if config.category == category
        ]
    
    def get_by_energy_type(self, energy_type: EnergyType) -> List[DeviceTypeConfig]:
        """按能源类型获取配置"""
        return [
            config for config in self._registry.values()
            if config.energy_type == energy_type
        ]
    
    def exists(self, device_type: str) -> bool:
        """检查设备类型是否存在"""
        return device_type in self._registry
    
    def get_energy_type_for_device(self, device_type: str) -> Optional[EnergyType]:
        """获取设备类型对应的能源类型"""
        config = self.get(device_type)
        return config.energy_type if config else None
    
    def get_category_for_device(self, device_type: str) -> Optional[DeviceCategory]:
        """获取设备类型对应的设备类别"""
        config = self.get(device_type)
        return config.category if config else None
    
    def get_unit_for_device(self, device_type: str) -> Optional[str]:
        """获取设备类型对应的单位"""
        config = self.get(device_type)
        return config.unit if config else None
    
    def list_device_types(self) -> List[str]:
        """列出所有设备类型"""
        return list(self._registry.keys())
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """导出为字典列表（用于API响应）"""
        return [
            {
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
            for config in self._registry.values()
        ]


# 全局单例
device_registry = DeviceRegistry()
