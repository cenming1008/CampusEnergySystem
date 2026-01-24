"""
数据库模型定义（SQLModel）
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlmodel import Field, SQLModel


class EnergyType(str, Enum):
    """能源类型枚举"""
    ELECTRICITY = "electricity"  # 电力
    WATER = "water"              # 水
    GAS = "gas"                  # 燃气
    HEAT = "heat"                # 热力
    COOLING = "cooling"          # 冷气
    STEAM = "steam"              # 蒸汽


class DeviceCategory(str, Enum):
    """设备类别枚举"""
    LOAD = "load"                # 用电设备
    SOLAR = "solar"              # 光伏发电
    WIND = "wind"                # 风力发电
    WATER_METER = "water_meter"  # 水表
    GAS_METER = "gas_meter"      # 燃气表
    HEAT_METER = "heat_meter"    # 热量表
    COOLING_METER = "cooling_meter"  # 冷量表
    STORAGE = "storage"          # 储能设备
    CHARGER = "charger"          # 充电桩


class MaintenanceType(str, Enum):
    """维护类型枚举"""
    ROUTINE = "routine"          # 日常维护
    REPAIR = "repair"            # 故障维修
    INSPECTION = "inspection"    # 定期巡检
    UPGRADE = "upgrade"          # 设备升级
    CALIBRATION = "calibration"  # 校准调试


class MaintenanceStatus(str, Enum):
    """维护状态枚举"""
    SCHEDULED = "scheduled"      # 已计划
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"      # 已完成
    CANCELLED = "cancelled"      # 已取消


class LocationType(str, Enum):
    """位置类型枚举"""
    BUILDING = "building"    # 楼栋
    UNIT = "unit"           # 单元
    FLOOR = "floor"         # 楼层
    ROOM = "room"           # 房间
    WORKSHOP = "workshop"   # 车间
    AREA = "area"           # 区域
    ZONE = "zone"           # 分区


class Location(SQLModel, table=True):
    """位置表（支持层级结构）"""
    
    __tablename__ = "location"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 层级关系
    parent_id: Optional[int] = Field(
        default=None, 
        foreign_key="location.id",
        description="父级位置ID（NULL表示顶级）"
    )
    
    # 位置信息
    name: str = Field(index=True, description="位置名称（如：A栋、3单元、1309）")
    location_type: str = Field(index=True, description="位置类型")
    code: Optional[str] = Field(default=None, unique=True, index=True, description="位置编码")
    
    # 完整路径（冗余字段，提升查询性能）
    full_path: Optional[str] = Field(
        default=None, 
        index=True,
        description="完整路径（如：/A栋/3单元/1309）"
    )
    
    # 层级深度（冗余字段，提升查询性能）
    level: int = Field(default=0, description="层级深度（0=顶级）")
    
    # 额外信息
    description: Optional[str] = Field(default=None, description="描述")
    area_sqm: Optional[float] = Field(default=None, description="面积（平方米）")
    manager: Optional[str] = Field(default=None, description="负责人")
    contact: Optional[str] = Field(default=None, description="联系方式")
    
    # 状态
    is_active: bool = Field(default=True, description="是否启用")
    
    # 时间
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Device(SQLModel, table=True):
    """设备表。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="设备名称")
    sn: str = Field(index=True, unique=True, description="设备序列号")
    device_type: str = Field(index=True, description="设备类型（兼容旧字段）")
    device_category: str = Field(default=DeviceCategory.LOAD, index=True, description="设备类别")
    energy_type: str = Field(default=EnergyType.ELECTRICITY, index=True, description="能源类型")
    
    # 位置信息
    location_id: Optional[int] = Field(
        default=None, 
        foreign_key="location.id",
        index=True,
        description="物理位置ID（关联Location表）"
    )
    location: Optional[str] = Field(default=None, description="设备位置（兼容旧版，字符串描述）")
    
    is_active: bool = Field(default=True, description="是否启用")
    description: Optional[str] = Field(default=None, description="设备描述")
    rated_capacity: Optional[float] = Field(default=None, description="额定容量/流量")
    unit: Optional[str] = Field(default=None, description="单位（kW/m³/m³等）")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class EnergyData(SQLModel, table=True):
    """
    通用能源数据表（时序表）- 支持多种能源类型。
    
    字段说明：
    - consumption: 累计消耗量/电表读数（类似里程表，只增不减）
                   单位根据能源类型不同：电力(kWh)、水(m³)、气(m³)、热(GJ)
    - flow_rate: 瞬时流量/功率（瞬时值，会上下波动）
                 单位根据能源类型不同：电力(kW)、水(m³/h)、气(m³/h)、热(GJ/h)
    
    向后兼容说明（废弃字段映射）：
    - 旧字段 power → 新字段 flow_rate
    - 旧字段 energy → 新字段 consumption
    """
    
    __tablename__ = "energydata"
    
    # 联合主键
    device_id: int = Field(primary_key=True, foreign_key="device.id", description="设备ID")
    timestamp: datetime = Field(primary_key=True, index=True, default_factory=datetime.now, description="时间戳")
    
    energy_type: str = Field(index=True, description="能源类型")
    
    # 通用字段
    consumption: float = Field(description="累计消耗量（电表读数/累计值，单位：kWh/m³/GJ）")
    flow_rate: Optional[float] = Field(default=None, description="瞬时流量/功率（瞬时值，单位：kW/m³/h/GJ/h）")
    
    # 电力专用字段
    voltage: Optional[float] = Field(default=None, description="电压(V)")
    current: Optional[float] = Field(default=None, description="电流(A)")
    power_factor: Optional[float] = Field(default=None, description="功率因数")
    
    # 水/气专用字段
    pressure: Optional[float] = Field(default=None, description="压力(MPa/kPa)")
    temperature: Optional[float] = Field(default=None, description="温度(℃)")
    
    # 热力专用字段
    supply_temp: Optional[float] = Field(default=None, description="供水温度(℃)")
    return_temp: Optional[float] = Field(default=None, description="回水温度(℃)")
    heat_flow: Optional[float] = Field(default=None, description="热流量(GJ/h)")
    
    # 质量指标
    quality_index: Optional[float] = Field(default=None, description="质量指标（如水质、气质等）")
    
    # 向后兼容属性（旧代码仍可使用旧字段名）
    @property
    def power(self) -> Optional[float]:
        """向后兼容：power字段映射到flow_rate"""
        return self.flow_rate
    
    @property
    def energy(self) -> float:
        """向后兼容：energy字段映射到consumption"""
        return self.consumption


class Alarm(SQLModel, table=True):
    """报警记录表。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(index=True, foreign_key="device.id")
    message: str
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    is_resolved: bool = Field(default=False)


class User(SQLModel, table=True):
    """用户表。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)


class CarbonEmission(SQLModel, table=True):
    """碳排放记录表（时序表）。"""
    
    __tablename__ = "carbon_emission"
    
    # 联合主键
    device_id: int = Field(primary_key=True, foreign_key="device.id", description="设备ID")
    timestamp: datetime = Field(primary_key=True, index=True, default_factory=datetime.now, description="时间戳")
    
    energy_type: str = Field(index=True, description="能源类型")
    energy_consumption: float = Field(description="能源消耗量")
    consumption_unit: str = Field(default="kWh", description="消耗量单位")
    
    # 碳排放计算
    carbon_factor: float = Field(description="碳排放因子 (kg CO2/单位)")
    carbon_emission: float = Field(description="碳排放量 (kg CO2)")
    
    # 可选：碳排放分类
    scope: Optional[int] = Field(default=1, description="范围(1:直接排放, 2:间接排放, 3:其他间接)")
    calculation_method: Optional[str] = Field(default="standard", description="计算方法")


class EnergyStatistics(SQLModel, table=True):
    """能源统计表 - 按时间段汇总。"""
    
    __tablename__ = "energy_statistics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: Optional[int] = Field(default=None, index=True, foreign_key="device.id", description="设备ID，None表示系统级")
    energy_type: str = Field(index=True, description="能源类型")
    
    # 时间维度
    stat_time: datetime = Field(index=True, description="统计时间")
    period_type: str = Field(index=True, description="统计周期：hour/day/month/year")
    
    # 统计数据
    total_consumption: float = Field(description="总消耗量")
    avg_flow_rate: Optional[float] = Field(default=None, description="平均流量/功率")
    peak_flow_rate: Optional[float] = Field(default=None, description="峰值流量/功率")
    
    # 成本相关
    unit_price: Optional[float] = Field(default=None, description="单价")
    total_cost: Optional[float] = Field(default=None, description="总成本")
    
    # 碳排放
    total_carbon: Optional[float] = Field(default=None, description="总碳排放 (kg CO2)")
    
    created_at: datetime = Field(default_factory=datetime.now)


class Prediction(SQLModel, table=True):
    """预测结果表（负荷预测、风光预测等）。"""
    
    __tablename__ = "prediction"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    prediction_type: str = Field(index=True, description="预测类型：load(负荷)、solar(光伏)、wind(风电)")
    device_id: Optional[int] = Field(default=None, index=True, foreign_key="device.id", description="设备ID，None表示系统级预测")
    forecast_time: datetime = Field(index=True, description="预测时间点")
    predicted_value: float = Field(description="预测值（功率，单位：kW）")
    confidence: Optional[float] = Field(default=None, description="置信度（0-1）")
    actual_value: Optional[float] = Field(default=None, description="实际值（用于评估预测准确性）")
    algorithm: str = Field(default="moving_average", description="使用的预测算法")
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    meta_info: Optional[str] = Field(default=None, description="额外元数据（JSON字符串）")


class DeviceMaintenance(SQLModel, table=True):
    """设备维护记录表"""
    
    __tablename__ = "device_maintenance"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(index=True, foreign_key="device.id", description="设备ID")
    maintenance_type: str = Field(index=True, description="维护类型")
    
    # 时间信息
    scheduled_time: datetime = Field(index=True, description="计划维护时间")
    actual_start_time: Optional[datetime] = Field(default=None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(default=None, description="实际结束时间")
    duration_minutes: Optional[int] = Field(default=None, description="维护时长（分钟）")
    
    # 维护详情
    title: str = Field(description="维护标题")
    description: Optional[str] = Field(default=None, description="维护描述")
    operator: Optional[str] = Field(default=None, description="维护人员")
    status: str = Field(default=MaintenanceStatus.SCHEDULED, index=True, description="状态")
    
    # 成本
    cost: Optional[float] = Field(default=None, description="维护成本（元）")
    parts_replaced: Optional[str] = Field(default=None, description="更换部件清单（JSON数组）")
    
    # 结果
    result: Optional[str] = Field(default=None, description="维护结果/备注")
    next_maintenance_date: Optional[datetime] = Field(default=None, description="建议下次维护日期")
    
    # 审计字段
    created_by: Optional[str] = Field(default=None, description="创建人")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DeviceGroup(SQLModel, table=True):
    """设备分组表（用于业务逻辑分组）"""
    
    __tablename__ = "device_group"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="分组名称")
    code: Optional[str] = Field(default=None, unique=True, index=True, description="分组编码")
    description: Optional[str] = Field(default=None, description="分组描述")
    
    # 分组类型
    group_type: Optional[str] = Field(
        default=None,
        index=True,
        description="分组类型（production/office/critical/backup）"
    )
    
    # 层级关系（可选）
    parent_id: Optional[int] = Field(
        default=None,
        foreign_key="device_group.id",
        description="父分组ID"
    )
    
    # 额外信息
    manager: Optional[str] = Field(default=None, description="负责人")
    contact: Optional[str] = Field(default=None, description="联系方式")
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DeviceGroupMembership(SQLModel, table=True):
    """设备-分组关联表（多对多）"""
    
    __tablename__ = "device_group_membership"
    
    device_id: int = Field(primary_key=True, foreign_key="device.id")
    group_id: int = Field(primary_key=True, foreign_key="device_group.id")
    joined_at: datetime = Field(default_factory=datetime.now)
    note: Optional[str] = Field(default=None, description="备注")