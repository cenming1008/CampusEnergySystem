"""
设备接口聚合入口
"""

from fastapi import APIRouter

from .data import (
    get_device_data,
    get_device_statistics,
    report_device_data,
    router as data_router,
)
from .health import (
    get_device_ingestion_health,
    list_device_ingestion_health,
    router as health_router,
)
from .management import (
    create_device_legacy,
    create_device_smart,
    delete_device,
    get_device,
    get_device_semantic_profile,
    get_device_type_info,
    get_device_types,
    get_devices,
    toggle_device_status,
    update_device,
    router as management_router,
)
from .monitoring import (
    get_device_alarm_history,
    get_device_control_logs,
    get_device_monitor_overview,
    get_device_monitor_trend,
    get_device_realtime,
    get_device_runtime_status,
    get_device_status_history,
    router as monitoring_router,
)

router = APIRouter()
router.include_router(management_router)
router.include_router(data_router)
router.include_router(health_router)
router.include_router(monitoring_router)
