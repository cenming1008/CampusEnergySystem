"""
业务服务模块
"""
from app.services.device_service import DeviceService
from app.services.alarm_service import AlarmService
from app.services.analysis_service import AnalysisService
from app.services.fdd_service import FDDService
from app.services.energy_service import EnergyService
from app.services.device_group_service import DeviceGroupService
from app.services.location_service import LocationService
from app.services.maintenance_service import MaintenanceService

# 可选服务（预测和深度学习相关）
try:
    from app.services.forecast_adapter import ForecastAdapter
    from app.services.scheduler_service import start_scheduler, stop_scheduler, get_jobs
    __all__ = [
        "DeviceService",
        "AlarmService",
        "AnalysisService",
        "FDDService",
        "EnergyService",
        "DeviceGroupService",
        "LocationService",
        "MaintenanceService",
        "ForecastAdapter",
        "start_scheduler",
        "stop_scheduler",
        "get_jobs",
    ]
except ImportError:
    __all__ = [
        "DeviceService",
        "AlarmService",
        "AnalysisService",
        "FDDService",
        "EnergyService",
        "DeviceGroupService",
        "LocationService",
        "MaintenanceService",
    ]

