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


class InspectionStatus(str, Enum):
    """巡检任务状态枚举"""
    PENDING = "pending"           # 待执行
    IN_PROGRESS = "in_progress"   # 进行中
    COMPLETED = "completed"       # 已完成
    OVERDUE = "overdue"           # 已逾期
    CANCELLED = "cancelled"       # 已取消


class InspectionResult(str, Enum):
    """巡检结果枚举"""
    NORMAL = "normal"             # 正常
    ABNORMAL = "abnormal"         # 异常
    DEFECT = "defect"             # 缺陷
    SERIOUS = "serious"           # 严重


class UserRole(str, Enum):
    """用户角色枚举"""

    ADMIN = "admin"
    OPERATOR = "operator"
    MAINTAINER = "maintainer"
    VIEWER = "viewer"


class AuditOutcome(str, Enum):
    """审计结果枚举。"""

    SUCCESS = "success"
    FAILED = "failed"
    DENIED = "denied"


class MqttIngestionStatus(str, Enum):
    """MQTT 接入处理状态。"""

    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    DUPLICATE = "duplicate"
    DEAD_LETTER = "dead_letter"


# ==================== 表模型 ====================


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
    """设备表"""

    __tablename__ = "device"
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


class DeviceIngestionHealth(SQLModel, table=True):
    """设备接入健康状态表。"""

    __tablename__ = "device_ingestion_health"

    device_id: int = Field(primary_key=True, foreign_key="device.id", description="设备ID")
    last_message_at: Optional[datetime] = Field(default=None, index=True, description="最近一次接收到消息的时间")
    last_success_at: Optional[datetime] = Field(default=None, index=True, description="最近一次成功入库时间")
    last_failure_at: Optional[datetime] = Field(default=None, index=True, description="最近一次失败时间")
    last_failure_reason: Optional[str] = Field(default=None, description="最近一次失败原因")
    consecutive_failures: int = Field(default=0, description="连续失败次数")
    total_messages: int = Field(default=0, description="累计接收消息数")
    total_failures: int = Field(default=0, description="累计失败次数")
    updated_at: datetime = Field(default_factory=datetime.now, description="最后更新时间")


class AuditEvent(SQLModel, table=True):
    """安全与运维关键操作审计事件。"""

    __tablename__ = "audit_event"

    id: Optional[int] = Field(default=None, primary_key=True)
    action: str = Field(index=True, description="操作标识")
    actor: str = Field(index=True, description="执行人")
    target: str = Field(index=True, description="目标资源")
    outcome: str = Field(default=AuditOutcome.SUCCESS, index=True, description="执行结果")
    actor_role: Optional[str] = Field(default=None, index=True, description="执行人角色")
    details: Optional[str] = Field(default=None, description="审计细节(JSON)")
    created_at: datetime = Field(default_factory=datetime.now, index=True, description="记录时间")


class MqttIngestionRecord(SQLModel, table=True):
    """MQTT 消息接入台账，用于幂等、防重和失败留痕。"""

    __tablename__ = "mqtt_ingestion_record"

    id: Optional[int] = Field(default=None, primary_key=True)
    fingerprint: str = Field(index=True, unique=True, description="消息指纹")
    payload_hash: str = Field(index=True, description="标准化 payload 哈希")
    raw_payload: Optional[str] = Field(default=None, description="原始消息体")
    device_id: int = Field(index=True, foreign_key="device.id", description="设备ID")
    topic: Optional[str] = Field(default=None, index=True, description="消息主题")
    telemetry_timestamp: Optional[datetime] = Field(default=None, index=True, description="设备时间戳")
    received_at: datetime = Field(default_factory=datetime.now, index=True, description="首次接收时间")
    last_seen_at: datetime = Field(default_factory=datetime.now, index=True, description="最近一次看到该消息的时间")
    status: str = Field(default=MqttIngestionStatus.PROCESSING, index=True, description="处理状态")
    error_reason: Optional[str] = Field(default=None, description="失败原因")
    duplicate_count: int = Field(default=0, description="重复收到次数")
    retry_count: int = Field(default=0, description="自动/人工累计重试次数")
    next_retry_at: Optional[datetime] = Field(default=None, index=True, description="下一次允许重试时间")
    replay_count: int = Field(default=0, description="人工重放次数")
    last_replayed_at: Optional[datetime] = Field(default=None, index=True, description="最近一次重放时间")


class EnergyData(SQLModel, table=True):
    """
    通用能源数据表（时序表）- 支持多种能源类型。

    字段说明：
    - consumption: 累计消耗量/电表读数（类似里程表，只增不减）
                   单位根据能源类型不同：电力(kWh)、水(m³)、气(m³)、热(GJ)
    - flow_rate: 瞬时流量/功率（瞬时值，会上下波动）
                 单位根据能源类型不同：电力(kW)、水(m³/h)、气(m³/h)、热(GJ/h)
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


class Alarm(SQLModel, table=True):
    """报警记录表"""

    __tablename__ = "alarm"
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(index=True, foreign_key="device.id")
    message: str
    severity: str = Field(default="warning", index=True, description="报警级别：info/warning/critical")
    category: str = Field(default="threshold", index=True, description="报警类别")
    source: str = Field(default="telemetry", description="报警来源")
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    is_resolved: bool = Field(default=False)
    resolved_at: Optional[datetime] = Field(default=None, index=True, description="解决时间")
    resolved_by: Optional[str] = Field(default=None, description="解决人")
    handling_note: Optional[str] = Field(default=None, description="处理备注")


class DeviceControlLog(SQLModel, table=True):
    """设备控制/启停记录表。"""

    __tablename__ = "device_control_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(index=True, foreign_key="device.id", description="设备ID")
    action: str = Field(index=True, description="动作：start/stop/toggle")
    target_status: bool = Field(description="目标状态")
    previous_status: Optional[bool] = Field(default=None, description="变更前状态")
    operator: Optional[str] = Field(default=None, description="操作人")
    command_source: str = Field(default="api", description="来源：api/system/mqtt")
    result: str = Field(default="success", index=True, description="执行结果")
    reason: Optional[str] = Field(default=None, description="备注/原因")
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class User(SQLModel, table=True):
    """用户表"""

    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: str = Field(default=UserRole.VIEWER, index=True, description="用户角色")
    location_scope: Optional[str] = Field(default=None, description="可访问位置ID列表，逗号分隔；为空表示不限制")
    is_active: bool = Field(default=True)
    must_change_password: bool = Field(default=False, description="是否必须在下次登录后修改密码")
    failed_login_attempts: int = Field(default=0, description="连续登录失败次数")
    locked_until: Optional[datetime] = Field(default=None, index=True, description="账户锁定截止时间")
    token_version: int = Field(default=0, description="令牌版本号，用于强制下线")
    last_login_at: Optional[datetime] = Field(default=None, index=True, description="最近登录时间")
    last_password_changed_at: Optional[datetime] = Field(default=None, description="最近密码修改时间")


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


class InspectionRoute(SQLModel, table=True):
    """巡检路线表 - 定义巡检路径"""
    
    __tablename__ = "inspection_route"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="路线名称")
    code: Optional[str] = Field(default=None, unique=True, description="路线编码")
    description: Optional[str] = Field(default=None, description="路线描述")
    
    # 路线配置
    estimated_duration: Optional[int] = Field(default=30, description="预计耗时（分钟）")
    device_count: int = Field(default=0, description="包含设备数量")
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class InspectionPoint(SQLModel, table=True):
    """巡检点表 - 路线中的检查点"""
    
    __tablename__ = "inspection_point"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    route_id: int = Field(index=True, foreign_key="inspection_route.id", description="所属路线")
    device_id: Optional[int] = Field(default=None, foreign_key="device.id", description="关联设备")
    
    # 巡检点信息
    name: str = Field(description="巡检点名称")
    location: Optional[str] = Field(default=None, description="位置描述")
    sequence: int = Field(default=0, description="巡检顺序")
    
    # 检查项目（JSON数组）
    check_items: Optional[str] = Field(
        default='["外观检查", "运行状态", "仪表读数"]',
        description="检查项目列表（JSON）"
    )
    
    # QR码/NFC标签
    qr_code: Optional[str] = Field(default=None, unique=True, description="二维码编号")
    
    is_required: bool = Field(default=True, description="是否必检")
    is_active: bool = Field(default=True)


class InspectionPlan(SQLModel, table=True):
    """巡检计划表 - 定期巡检任务"""
    
    __tablename__ = "inspection_plan"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    route_id: int = Field(index=True, foreign_key="inspection_route.id", description="巡检路线")
    
    # 计划信息
    name: str = Field(description="计划名称")
    plan_type: str = Field(default="daily", description="计划类型: daily/weekly/monthly")
    
    # 执行时间
    start_date: datetime = Field(description="开始日期")
    end_date: Optional[datetime] = Field(default=None, description="结束日期")
    execution_time: Optional[str] = Field(default="08:00", description="执行时间 HH:MM")
    
    # 周期配置（JSON）
    schedule_config: Optional[str] = Field(
        default=None,
        description="周期配置（如周几执行、每月几号等）"
    )
    
    # 责任人
    assigned_to: Optional[str] = Field(default=None, description="负责人")
    department: Optional[str] = Field(default=None, description="负责部门")
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)


class InspectionTask(SQLModel, table=True):
    """巡检任务表 - 具体的巡检执行记录"""
    
    __tablename__ = "inspection_task"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: Optional[int] = Field(default=None, foreign_key="inspection_plan.id", description="关联计划")
    route_id: int = Field(index=True, foreign_key="inspection_route.id", description="巡检路线")
    
    # 任务信息
    task_no: str = Field(unique=True, index=True, description="任务编号")
    task_date: datetime = Field(index=True, description="任务日期")
    status: str = Field(default=InspectionStatus.PENDING, index=True, description="任务状态")
    
    # 执行信息
    inspector: Optional[str] = Field(default=None, description="巡检员")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    duration_minutes: Optional[int] = Field(default=None, description="耗时（分钟）")
    
    # 完成情况
    total_points: int = Field(default=0, description="总巡检点数")
    completed_points: int = Field(default=0, description="已完成点数")
    abnormal_count: int = Field(default=0, description="异常数量")
    
    # 备注
    remark: Optional[str] = Field(default=None, description="备注")
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class InspectionRecord(SQLModel, table=True):
    """巡检记录表 - 每个巡检点的检查结果"""
    
    __tablename__ = "inspection_record"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(index=True, foreign_key="inspection_task.id", description="关联任务")
    point_id: int = Field(index=True, foreign_key="inspection_point.id", description="巡检点")
    device_id: Optional[int] = Field(default=None, foreign_key="device.id", description="关联设备")
    
    # 检查结果
    result: str = Field(default=InspectionResult.NORMAL, description="检查结果")
    check_time: datetime = Field(default_factory=datetime.now, description="检查时间")
    
    # 详细记录（JSON）
    check_details: Optional[str] = Field(
        default=None,
        description="检查项目详情（JSON: {item: result}）"
    )
    
    # 读数记录
    meter_reading: Optional[float] = Field(default=None, description="仪表读数")
    
    # 异常信息
    abnormal_description: Optional[str] = Field(default=None, description="异常描述")
    abnormal_level: Optional[str] = Field(default=None, description="异常等级")
    
    # 图片附件（JSON数组）
    images: Optional[str] = Field(default=None, description="图片URL列表（JSON）")
    
    # 处理情况
    is_handled: bool = Field(default=False, description="是否已处理")
    handle_result: Optional[str] = Field(default=None, description="处理结果")
    
    inspector: Optional[str] = Field(default=None, description="巡检员")


class DeviceGroupMembership(SQLModel, table=True):
    """设备-分组关联表（多对多）"""
    
    __tablename__ = "device_group_membership"
    
    device_id: int = Field(primary_key=True, foreign_key="device.id")
    group_id: int = Field(primary_key=True, foreign_key="device_group.id")
    joined_at: datetime = Field(default_factory=datetime.now)
    note: Optional[str] = Field(default=None, description="备注")
