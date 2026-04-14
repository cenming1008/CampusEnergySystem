"""
设备类型注册表。

第一批设备建模收敛仍保留统一 `Device` 对象，
但通过 registry 显式补齐“设备对象 / 计量对象 / 点位对象”的兼容语义。
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
    unit: str  # 兼容旧字段：设备额定容量/主要瞬时量单位
    default_capacity: Optional[float] = None  # 默认额定容量
    subtype_name_zh: Optional[str] = None  # 面向技术人员的子类型名称
    subtype_name_en: Optional[str] = None

    # 第一批对象语义
    object_role: str = "equipment"  # equipment / meter
    metering_role: str = "embedded_measurement"  # embedded_measurement / dedicated_meter
    point_kind: str = "energy_point_series"
    measurement_subject: str = "energy"
    rated_capacity_unit: Optional[str] = None
    consumption_unit: Optional[str] = None
    flow_unit: Optional[str] = None
    
    # 数据字段配置
    required_fields: List[str] = None  # 必需字段
    optional_fields: List[str] = None  # 可选字段
    public_data_fields: List[str] = None  # EnergyData 公共层字段
    specialized_fields: List[str] = None  # EnergyData / payload 专属字段
    compatible_aliases: Dict[str, str] = None  # 上报兼容别名
    
    # 图标和颜色（用于前端展示）
    icon: Optional[str] = None
    color: Optional[str] = None
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = []
        if self.optional_fields is None:
            self.optional_fields = []
        if self.public_data_fields is None:
            self.public_data_fields = ["consumption", "flow_rate"]
        if self.specialized_fields is None:
            self.specialized_fields = []
        if self.compatible_aliases is None:
            self.compatible_aliases = {}
        if self.rated_capacity_unit is None:
            self.rated_capacity_unit = self.unit
        if self.consumption_unit is None:
            self.consumption_unit = self.unit
        if self.flow_unit is None:
            self.flow_unit = self.unit
        if self.subtype_name_zh is None:
            self.subtype_name_zh = self.name_zh
        if self.subtype_name_en is None:
            self.subtype_name_en = self.name_en

    def to_semantic_dict(self) -> Dict[str, Any]:
        return {
            "device_type": self.device_type,
            "category": self.category.value,
            "energy_type": self.energy_type.value,
            "name_zh": self.name_zh,
            "name_en": self.name_en,
            "subtype_name_zh": self.subtype_name_zh,
            "subtype_name_en": self.subtype_name_en,
            "unit": self.unit,
            "default_capacity": self.default_capacity,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "object_role": self.object_role,
            "metering_role": self.metering_role,
            "point_kind": self.point_kind,
            "measurement_subject": self.measurement_subject,
            "rated_capacity_unit": self.rated_capacity_unit,
            "consumption_unit": self.consumption_unit,
            "flow_unit": self.flow_unit,
            "public_data_fields": self.public_data_fields,
            "specialized_fields": self.specialized_fields,
            "compatible_aliases": self.compatible_aliases,
            "icon": self.icon,
            "color": self.color,
        }


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
            object_role="equipment",
            metering_role="embedded_measurement",
            point_kind="equipment_energy_point",
            measurement_subject="electric_power",
            rated_capacity_unit="kW",
            consumption_unit="kWh",
            flow_unit="kW",
            required_fields=["consumption", "power"],
            optional_fields=["voltage", "current", "power_factor"],
            specialized_fields=["voltage", "current", "power_factor"],
            compatible_aliases={"power": "flow_rate"},
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
            object_role="equipment",
            metering_role="embedded_measurement",
            point_kind="generation_energy_point",
            measurement_subject="electric_generation",
            rated_capacity_unit="kW",
            consumption_unit="kWh",
            flow_unit="kW",
            required_fields=["consumption", "power"],  # consumption 为负值表示发电
            optional_fields=["voltage", "current", "irradiance", "temperature"],
            specialized_fields=["voltage", "current", "temperature"],
            compatible_aliases={"power": "flow_rate"},
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
            object_role="equipment",
            metering_role="embedded_measurement",
            point_kind="generation_energy_point",
            measurement_subject="electric_generation",
            rated_capacity_unit="kW",
            consumption_unit="kWh",
            flow_unit="kW",
            required_fields=["consumption", "power"],
            optional_fields=["voltage", "current", "wind_speed"],
            specialized_fields=["voltage", "current"],
            compatible_aliases={"power": "flow_rate"},
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
            object_role="equipment",
            metering_role="embedded_measurement",
            point_kind="storage_energy_point",
            measurement_subject="electric_storage",
            rated_capacity_unit="kWh",
            consumption_unit="kWh",
            flow_unit="kW",
            required_fields=["consumption", "power"],
            optional_fields=["voltage", "current", "temperature", "soc"],  # soc: 荷电状态（可选）
            specialized_fields=["voltage", "current", "temperature"],
            compatible_aliases={"power": "flow_rate"},
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
            object_role="equipment",
            metering_role="embedded_measurement",
            point_kind="charging_energy_point",
            measurement_subject="electric_charge",
            rated_capacity_unit="kW",
            consumption_unit="kWh",
            flow_unit="kW",
            required_fields=["consumption", "power"],
            optional_fields=["voltage", "current", "charging_status"],
            specialized_fields=["voltage", "current"],
            compatible_aliases={"power": "flow_rate"},
            icon="🔌",
            color="#9C27B0"
        ))
        
        # 静止无功发生器（SVG）
        self.register(DeviceTypeConfig(
            device_type="svg",
            category=DeviceCategory.COMPENSATION,
            energy_type=EnergyType.ELECTRICITY,
            name_zh="无功功率补偿设备",
            name_en="Static Var Generator",
            subtype_name_zh="SVG",
            subtype_name_en="Static Var Generator",
            unit="kVAR",
            default_capacity=200.0,
            object_role="equipment",
            metering_role="embedded_measurement",
            point_kind="power_quality_point",
            measurement_subject="reactive_power_compensation",
            rated_capacity_unit="kVAR",
            consumption_unit="kWh",
            flow_unit="kW",
            required_fields=["reactive_power"],
            optional_fields=["consumption", "flow_rate", "voltage", "current", "power_factor"],
            specialized_fields=["voltage", "current", "power_factor", "reactive_power"],
            compatible_aliases={"kvar": "reactive_power", "power": "flow_rate", "active_power": "flow_rate"},
            icon="⚡",
            color="#FF6F00"
        ))

        # 电容补偿控制器 / 电容补偿柜
        self.register(DeviceTypeConfig(
            device_type="capacitor_bank_controller",
            category=DeviceCategory.COMPENSATION,
            energy_type=EnergyType.ELECTRICITY,
            name_zh="无功功率补偿设备",
            name_en="Capacitor Bank Controller",
            subtype_name_zh="电容补偿控制器",
            subtype_name_en="Capacitor Bank Controller",
            unit="kVAR",
            default_capacity=200.0,
            object_role="equipment",
            metering_role="embedded_measurement",
            point_kind="power_quality_point",
            measurement_subject="reactive_power_compensation",
            rated_capacity_unit="kVAR",
            consumption_unit="kWh",
            flow_unit="kW",
            required_fields=["reactive_power"],
            optional_fields=["consumption", "flow_rate", "voltage", "current", "power_factor", "temperature"],
            specialized_fields=["voltage", "current", "power_factor", "reactive_power", "temperature"],
            compatible_aliases={"kvar": "reactive_power", "power": "flow_rate", "active_power": "flow_rate"},
            icon="⚙️",
            color="#D97706"
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
            object_role="meter",
            metering_role="dedicated_meter",
            point_kind="meter_reading_point",
            measurement_subject="water_volume",
            rated_capacity_unit="m³/h",
            consumption_unit="m³",
            flow_unit="m³/h",
            required_fields=["consumption", "flow_rate"],
            optional_fields=["pressure", "temperature", "quality_index"],
            specialized_fields=["pressure", "temperature", "quality_index"],
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
            object_role="meter",
            metering_role="dedicated_meter",
            point_kind="meter_reading_point",
            measurement_subject="gas_volume",
            rated_capacity_unit="m³/h",
            consumption_unit="m³",
            flow_unit="m³/h",
            required_fields=["consumption", "flow_rate"],
            optional_fields=["pressure", "temperature", "quality_index"],
            specialized_fields=["pressure", "temperature", "quality_index"],
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
            object_role="meter",
            metering_role="dedicated_meter",
            point_kind="meter_reading_point",
            measurement_subject="heat_energy",
            rated_capacity_unit="GJ/h",
            consumption_unit="GJ",
            flow_unit="GJ/h",
            required_fields=["consumption", "heat_flow"],
            optional_fields=["supply_temp", "return_temp", "flow_rate", "pressure"],
            specialized_fields=["heat_flow", "supply_temp", "return_temp", "pressure"],
            compatible_aliases={"heat_power": "heat_flow", "heat_flow": "flow_rate"},
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
            object_role="meter",
            metering_role="dedicated_meter",
            point_kind="meter_reading_point",
            measurement_subject="cooling_energy",
            rated_capacity_unit="kW",
            consumption_unit="kWh",
            flow_unit="kW",
            required_fields=["consumption", "flow_rate"],
            optional_fields=["supply_temp", "return_temp", "pressure"],
            specialized_fields=["supply_temp", "return_temp", "pressure"],
            compatible_aliases={"cooling_power": "flow_rate"},
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
            object_role="meter",
            metering_role="dedicated_meter",
            point_kind="meter_reading_point",
            measurement_subject="steam_mass",
            rated_capacity_unit="t/h",
            consumption_unit="t",
            flow_unit="t/h",
            required_fields=["consumption", "flow_rate"],
            optional_fields=["pressure", "temperature", "quality_index"],
            specialized_fields=["pressure", "temperature", "quality_index"],
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
        return [config.to_semantic_dict() for config in self._registry.values()]


# 全局单例
device_registry = DeviceRegistry()
