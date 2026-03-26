"""
Repository 层
封装数据库访问细节。
"""

from app.repositories.base import BaseRepository
from app.repositories.device_repository import DeviceRepository
from app.repositories.energy_repository import EnergyRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "DeviceRepository",
    "EnergyRepository",
    "UserRepository",
]
