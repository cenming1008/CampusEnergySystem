"""
API端点模块
"""
from app.api.endpoints import (
    auth,
    devices,
    telemetry,
    alarms,
    analysis,
    fdd,
    reports
)

__all__ = [
    "auth",
    "devices",
    "telemetry",
    "alarms",
    "analysis",
    "fdd",
    "reports",
]

