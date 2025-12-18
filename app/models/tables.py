from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

# --- 设备表 ---
class Device(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sn: str = Field(index=True, unique=True)
    device_type: str = Field(index=True)
    location: Optional[str] = None
    is_active: bool = Field(default=True)
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# --- 实时数据表 ---
class DeviceData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(index=True, foreign_key="device.id") 
    timestamp: datetime = Field(index=True, default_factory=datetime.now)
    voltage: float 
    current: float 
    power: float 
    energy: float

# --- 报警表 ---
class Alarm(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(index=True, foreign_key="device.id")
    message: str
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    is_resolved: bool = Field(default=False)

# --- 用户表 ---
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str # 注意：永远不要存明文密码！
    is_active: bool = Field(default=True)