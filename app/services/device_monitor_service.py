"""
设备监控聚合服务
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from sqlmodel import Session

from app.domain.device_payloads import normalize_device_type_alias, resolve_compensation_subtype
from app.models.tables import Device, DeviceControlLog
from app.repositories.device_repository import DeviceRepository
from app.repositories.energy_repository import EnergyRepository
from app.services.alarm_service import AlarmService
from app.services.device_service import DeviceService
from app.services.devices.compensation.capacitor_bank.control_command_service import (
    CapacitorBankControlCommandService,
)
from app.services.ingestion_health_service import IngestionHealthService


class DeviceMonitorService:
    """聚合设备监控页所需的状态、实时值、趋势、告警与控制记录。"""
    _COMPENSATOR_REALTIME_FIELDS = (
        "flow_rate",
        "reactive_power",
        "power_factor",
        "voltage",
        "current",
        "timestamp",
    )

    @staticmethod
    def _effective_device_type(device: Device) -> Optional[str]:
        subtype = resolve_compensation_subtype(
            getattr(device, "device_type", None),
            getattr(device, "device_subtype", None),
        )
        if subtype:
            return subtype
        return normalize_device_type_alias(getattr(device, "device_type", None))

    @staticmethod
    def _build_empty_realtime(device: Device, device_id: int) -> dict[str, Any]:
        payload = {
            "device_id": device_id,
            "timestamp": None,
            "energy_type": device.energy_type,
            "consumption": None,
            "flow_rate": None,
            "voltage": None,
            "current": None,
            "power_factor": None,
            "pressure": None,
            "temperature": None,
            "supply_temp": None,
            "return_temp": None,
            "heat_flow": None,
            "temperature_delta": None,
        }
        if resolve_compensation_subtype(getattr(device, "device_type", None), getattr(device, "device_subtype", None)):
            payload["reactive_power"] = None
        return payload

    @staticmethod
    def _build_realtime_payload(device: Device, latest) -> dict[str, Any]:
        payload = {
            "device_id": latest.device_id,
            "timestamp": latest.timestamp,
            "energy_type": latest.energy_type,
            "consumption": latest.consumption,
            "flow_rate": latest.flow_rate,
            "voltage": latest.voltage,
            "current": latest.current,
            "power_factor": latest.power_factor,
            "pressure": latest.pressure,
            "temperature": latest.temperature,
            "supply_temp": latest.supply_temp,
            "return_temp": latest.return_temp,
            "heat_flow": latest.heat_flow,
            "temperature_delta": DeviceMonitorService._temperature_delta(
                latest.supply_temp,
                latest.return_temp,
            ),
        }
        if resolve_compensation_subtype(getattr(device, "device_type", None), getattr(device, "device_subtype", None)):
            payload["reactive_power"] = latest.reactive_power
        return payload

    @staticmethod
    def _temperature_delta(supply_temp: Optional[float], return_temp: Optional[float]) -> Optional[float]:
        if supply_temp is None or return_temp is None:
            return None
        return round(abs(float(supply_temp) - float(return_temp)), 2)

    @staticmethod
    def record_control_action(
        session: Session,
        device_id: int,
        active: bool,
        operator: Optional[str] = None,
        command_source: str = "api",
        reason: Optional[str] = None,
        commit: bool = True,
    ) -> DeviceControlLog:
        device = DeviceService.get_device_by_id(session, device_id)
        log = DeviceControlLog(
            device_id=device_id,
            action="start" if active else "stop",
            target_status=active,
            previous_status=device.is_active,
            operator=operator,
            command_source=command_source,
            result="success",
            reason=reason,
        )
        return DeviceRepository.save_control_log(session, log, commit=commit)

    @staticmethod
    def get_latest_realtime(session: Session, device_id: int) -> dict[str, Any]:
        device = DeviceService.get_device_by_id(session, device_id)
        latest = EnergyRepository.get_latest_energy_data(session, device_id, device.energy_type)
        if latest is None:
            return DeviceMonitorService._build_empty_realtime(device, device_id)

        return DeviceMonitorService._build_realtime_payload(device, latest)

    @staticmethod
    def get_runtime_status(session: Session, device_id: int) -> dict[str, Any]:
        device = DeviceService.get_device_by_id(session, device_id)
        ingestion = IngestionHealthService.get_device_health(session, device_id)
        active_alarm_count = AlarmService.get_active_alarm_count(session, device_id=device_id)
        latest = DeviceMonitorService.get_latest_realtime(session, device_id)

        if not device.is_active:
            code = "stopped"
            label = "已停机"
        elif ingestion["status"] == "offline":
            code = "offline"
            label = "离线"
        elif active_alarm_count > 0:
            code = "alarm"
            label = "告警中"
        elif ingestion["status"] == "degraded":
            code = "degraded"
            label = "运行波动"
        elif ingestion["status"] == "online":
            code = "running"
            label = "运行中"
        else:
            code = "unknown"
            label = "状态未知"

        return {
            "device_id": device_id,
            "code": code,
            "label": label,
            "is_active": device.is_active,
            "is_online": ingestion.get("is_online", False),
            "ingestion_status": ingestion.get("status"),
            "unresolved_alarm_count": active_alarm_count,
            "last_message_at": ingestion.get("last_message_at"),
            "last_success_at": ingestion.get("last_success_at"),
            "latest_timestamp": latest.get("timestamp"),
        }

    @staticmethod
    def get_control_logs(
        session: Session,
        device_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50,
    ) -> list[DeviceControlLog]:
        DeviceService.get_device_by_id(session, device_id)
        CapacitorBankControlCommandService.expire_pending_control_logs(session, device_id=device_id)
        return DeviceRepository.list_control_logs(
            session,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    @staticmethod
    def get_trend_summary(
        session: Session,
        device_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        end_at = end_time or datetime.now()
        start_at = start_time or (end_at - timedelta(hours=24))
        points = DeviceService.get_device_data(
            session,
            device_id=device_id,
            start_time=start_at,
            end_time=end_at,
            limit=limit,
        )
        values = [float(point.flow_rate or 0) for point in points]
        latest_value = values[-1] if values else 0.0
        peak_value = max(values) if values else 0.0
        valley_value = min(values) if values else 0.0
        avg_value = sum(values) / len(values) if values else 0.0

        return {
            "device_id": device_id,
            "start_time": start_at,
            "end_time": end_at,
            "points": [
                {
                    "timestamp": point.timestamp,
                    "value": point.flow_rate,
                    "consumption": point.consumption,
                    "voltage": point.voltage,
                    "current": point.current,
                    "reactive_power": point.reactive_power,
                    "power_factor": point.power_factor,
                }
                for point in points
            ],
            "summary": {
                "latest": round(latest_value, 2),
                "peak": round(peak_value, 2),
                "valley": round(valley_value, 2),
                "average": round(avg_value, 2),
            },
        }

    @staticmethod
    def get_status_history(
        session: Session,
        device_id: int,
        hours: int = 72,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        since = datetime.now() - timedelta(hours=max(1, hours))
        alarms = AlarmService.list_alarms(
            session,
            device_id=device_id,
            start_time=since,
            limit=limit,
        )
        control_logs = DeviceMonitorService.get_control_logs(
            session,
            device_id=device_id,
            start_time=since,
            limit=limit,
        )

        events: list[dict[str, Any]] = []
        for alarm in alarms:
            alarm_status = "resolved" if alarm.is_resolved or alarm.recovered_at else "active"
            events.append(
                {
                    "timestamp": alarm.timestamp,
                    "event_type": "alarm",
                    "status": alarm_status,
                    "title": alarm.message,
                    "detail": f"级别: {alarm.severity}",
                }
            )
            if alarm.recovered_at:
                events.append(
                    {
                        "timestamp": alarm.recovered_at,
                        "event_type": "alarm_recovery",
                        "status": "resolved",
                        "title": f"告警已恢复: {alarm.message}",
                        "detail": "系统检测到告警条件已解除",
                    }
                )
            if alarm.is_resolved and alarm.resolved_at:
                events.append(
                    {
                        "timestamp": alarm.resolved_at,
                        "event_type": "alarm_resolution",
                        "status": "resolved",
                        "title": f"告警已处理: {alarm.message}",
                        "detail": alarm.resolved_by or "系统/未知用户",
                    }
                )

        for record in control_logs:
            events.append(
                {
                    "timestamp": record.created_at,
                    "event_type": "control",
                    "status": DeviceMonitorService._control_event_status(record),
                    "title": DeviceMonitorService._control_event_title(record),
                    "detail": DeviceMonitorService._control_event_detail(record),
                }
            )

        events.sort(key=lambda item: item["timestamp"], reverse=True)
        return events[:limit]

    @staticmethod
    def get_monitor_overview(session: Session, device_id: int) -> dict[str, Any]:
        from app.application.device_monitoring import get_device_monitor_overview_use_case

        return get_device_monitor_overview_use_case(session=session, device_id=device_id)

    @staticmethod
    def _control_event_status(record: DeviceControlLog) -> str:
        return CapacitorBankControlCommandService.normalize_control_result(record.result)

    @staticmethod
    def _control_event_title(record: DeviceControlLog) -> str:
        return CapacitorBankControlCommandService.get_action_label(record.action)

    @staticmethod
    def _control_event_detail(record: DeviceControlLog) -> str:
        detail_parts = [CapacitorBankControlCommandService.get_result_label(record.result)]
        if record.operator:
            detail_parts.append(record.operator)
        if record.reason:
            detail_parts.append(record.reason)
        return " | ".join(detail_parts)
