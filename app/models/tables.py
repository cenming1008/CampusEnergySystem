from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

# --- 设备表 (保持不变) ---
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

# --- 实时数据表 (⚠️ 核心修改) ---
class DeviceData(SQLModel, table=True):
    # 显式指定表名，确保全小写，方便 SQL 语句调用
    __tablename__ = "devicedata"

    # 1. 移除原来的自增 ID 主键 (在大数据量下，自增 ID 会成为写入瓶颈)
    # id: Optional[int] = Field(default=None, primary_key=True)
    
    # 2. 设置联合主键 (Composite Primary Key)
    # TimescaleDB 要求：分区列 (timestamp) 必须是主键的一部分
    device_id: int = Field(primary_key=True, foreign_key="device.id") 
    timestamp: datetime = Field(primary_key=True, index=True, default_factory=datetime.now)
    
    voltage: float 
    current: float 
    power: float 
    energy: float

# --- 报警表 (保持不变) ---
class Alarm(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(index=True, foreign_key="device.id")
    message: str
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    is_resolved: bool = Field(default=False)

# --- 用户表 (保持不变) ---
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)