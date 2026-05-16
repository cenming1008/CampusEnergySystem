"""
设备监控聚合主流程 use case。
"""

from __future__ import annotations

from typing import Any, Optional

from sqlmodel import Session

from app.core.access_control import ensure_device_access
from app.models.tables import User


def get_device_monitor_overview_use_case(
    session: Session,
    device_id: int,
    current_user: Optional[User] = None,
) -> dict[str, Any]:
    """构建设备监控 overview，保持现有接口返回契约。"""
    if current_user is not None:
        ensure_device_access(session, current_user, device_id)

    from app.services.alarm_service import AlarmService
    from app.services.device_monitor_service import DeviceMonitorService
    from app.services.device_service import DeviceService
    from app.services.devices.monitor_plugin_registry import DeviceMonitorContext, DeviceMonitorPluginRegistry
    from app.services.devices.monitor_template_service import MonitorTemplateService
    from app.services.ingestion_health_service import IngestionHealthService

    device = DeviceService.get_device_by_id(session, device_id)
    realtime = DeviceMonitorService.get_latest_realtime(session, device_id)
    runtime_status = DeviceMonitorService.get_runtime_status(session, device_id)
    ingestion_health = IngestionHealthService.get_device_health(session, device_id)
    monitor_context = DeviceMonitorContext(
        session=session,
        device=device,
        realtime=realtime,
        runtime_status=runtime_status,
        ingestion_health=ingestion_health,
    )
    monitor_plugin = DeviceMonitorPluginRegistry.resolve(device)
    specific_monitor = monitor_plugin.build_monitor_payload(monitor_context)
    compensation_monitor = (
        specific_monitor
        if monitor_plugin.plugin_key in {"capacitor_bank_controller", "svg"}
        else None
    )
    storage_monitor = specific_monitor if monitor_plugin.plugin_key == "storage" else None
    archive = {
        "id": device.id,
        "name": device.name,
        "sn": device.sn,
        "device_type": device.device_type,
        "device_subtype": device.device_subtype,
        "device_category": device.device_category,
        "energy_type": device.energy_type,
        "archive_status": device.archive_status,
        "location": device.location,
        "rated_capacity": device.rated_capacity,
        "unit": device.unit,
        "description": device.description,
        "created_at": device.created_at,
        "updated_at": device.updated_at,
    }

    overview = {
        "archive": archive,
        "runtime_status": runtime_status,
        "realtime": realtime,
        "ingestion_health": ingestion_health,
        "recent_alarms": [
            {
                "id": alarm.id,
                "message": alarm.message,
                "severity": alarm.severity,
                "category": alarm.category,
                "source": alarm.source,
                "timestamp": alarm.timestamp,
                "last_seen_at": alarm.last_seen_at,
                "recovered_at": alarm.recovered_at,
                "is_resolved": alarm.is_resolved,
            }
            for alarm in AlarmService.list_alarms(session, device_id=device_id, limit=10)
        ],
        "recent_control_logs": [
            {
                "id": log.id,
                "action": log.action,
                "target_status": log.target_status,
                "previous_status": log.previous_status,
                "operator": log.operator,
                "command_source": log.command_source,
                "result": log.result,
                "reason": log.reason,
                "created_at": log.created_at,
            }
            for log in DeviceMonitorService.get_control_logs(session, device_id, limit=10)
        ],
        "compensation_monitor": compensation_monitor,
        "storage_monitor": storage_monitor,
    }
    overview.update(
        MonitorTemplateService.build_overview_template(
            device=device,
            realtime=realtime,
            runtime_status=runtime_status,
            ingestion_health=ingestion_health,
            compensation_monitor=compensation_monitor,
            storage_monitor=storage_monitor,
            monitor_plugin=monitor_plugin,
            specific_monitor=specific_monitor,
        )
    )
    return overview


__all__ = ["get_device_monitor_overview_use_case"]
