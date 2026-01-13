"""
业务服务模块
"""
from app.services.device_service import DeviceService
from app.services.alarm_service import AlarmService
from app.services.analysis_service import AnalysisService
from app.services.fdd_service import FDDService
from app.services.data_processor import process_device_data

# 可选服务（预测和深度学习相关）
try:
    from app.services.forecast_adapter import ForecastAdapter
    from app.services.scheduler_service import start_scheduler, stop_scheduler, get_jobs
    __all__ = [
        "DeviceService",
        "AlarmService",
        "AnalysisService",
        "FDDService",
        "ForecastAdapter",
        "start_scheduler",
        "stop_scheduler",
        "get_jobs",
        "process_device_data",
    ]
except ImportError:
    __all__ = [
        "DeviceService",
        "AlarmService",
        "AnalysisService",
        "FDDService",
        "process_device_data",
    ]

