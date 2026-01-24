"""
API端点模块
"""
from app.api.endpoints import (
    auth,
    devices,
    alarms,
    analysis,
    fdd,
    reports,
    health,
    forecast,
    data_generator,
    energy,
    maintenance,
    locations,
    device_groups,
    data_cleanup,
)

__all__ = [
    "auth",
    "devices",
    "alarms",
    "analysis",
    "fdd",
    "reports",
    "health",
    "forecast",
    "data_generator",
    "energy",
    "maintenance",
    "locations",
    "device_groups",
    "data_cleanup",
]

