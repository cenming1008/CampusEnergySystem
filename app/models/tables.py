"""
数据库模型定义（SQLModel）
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Device(SQLModel, table=True):
    """设备表。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sn: str = Field(index=True, unique=True)
    device_type: str = Field(index=True)
    location: Optional[str] = None
    is_active: bool = Field(default=True)
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DeviceData(SQLModel, table=True):
    """设备遥测数据（时序表）。"""

    __tablename__ = "devicedata"

    # 联合主键：TimescaleDB hypertable 要求时间列参与主键
    device_id: int = Field(primary_key=True, foreign_key="device.id")
    timestamp: datetime = Field(primary_key=True, index=True, default_factory=datetime.now)

    voltage: float
    current: float
    power: float
    energy: float


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