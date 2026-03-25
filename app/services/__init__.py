"""
业务服务模块
"""
from app.services import data_cleanup_service, ingestion_health_service
from app.services.alarm_service import AlarmService
from app.services.analysis_service import AnalysisService
from app.services.data_cleanup_service import cleanup_old_data, get_data_statistics
from app.services.device_group_service import DeviceGroupService
from app.services.device_monitor_service import DeviceMonitorService
from app.services.device_service import DeviceService
from app.services.fdd_service import FDDService
from app.services.energy_service import EnergyService
from app.services.ingestion_health_service import IngestionHealthService
from app.services.inspection_service import InspectionService
from app.services.location_service import LocationService
from app.services.maintenance_service import MaintenanceService
from app.services.scheduler_jobs import (
    auto_cleanup_data,
    auto_train_lstm_models,
    auto_update_forecasts,
)


def process_payload(*args, **kwargs):
    from app.services.mqtt_processor import process_payload as _process_payload

    return _process_payload(*args, **kwargs)


def process_payload_dict(*args, **kwargs):
    from app.services.mqtt_processor import process_payload_dict as _process_payload_dict

    return _process_payload_dict(*args, **kwargs)

# 可选服务（预测和深度学习相关）
try:
    from app.integrations.forecasting import ForecastAdapter
    from app.services.scheduler_service import start_scheduler, stop_scheduler, get_jobs
    __all__ = [
        "DeviceService",
        "DeviceMonitorService",
        "AlarmService",
        "AnalysisService",
        "data_cleanup_service",
        "cleanup_old_data",
        "get_data_statistics",
        "FDDService",
        "EnergyService",
        "DeviceGroupService",
        "ingestion_health_service",
        "IngestionHealthService",
        "auto_cleanup_data",
        "auto_train_lstm_models",
        "auto_update_forecasts",
        "LocationService",
        "MaintenanceService",
        "InspectionService",
        "process_payload",
        "process_payload_dict",
        "ForecastAdapter",
        "start_scheduler",
        "stop_scheduler",
        "get_jobs",
    ]
except ImportError:
    __all__ = [
        "DeviceService",
        "DeviceMonitorService",
        "AlarmService",
        "AnalysisService",
        "data_cleanup_service",
        "cleanup_old_data",
        "get_data_statistics",
        "FDDService",
        "EnergyService",
        "DeviceGroupService",
        "ingestion_health_service",
        "IngestionHealthService",
        "auto_cleanup_data",
        "auto_train_lstm_models",
        "auto_update_forecasts",
        "LocationService",
        "MaintenanceService",
        "InspectionService",
        "process_payload",
        "process_payload_dict",
    ]
