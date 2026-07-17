"""储能设备控制命令、回执与超时状态机。"""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime
from typing import Any, Callable, Optional

from sqlmodel import Session, select

from app.models.storage import StorageAssetProfile, StorageTelemetry
from app.models.tables import Device, DeviceControlLog
from app.repositories.device_repository import DeviceRepository
from app.services.devices.storage.specs import (
    CONTROL_COMMAND_MESSAGE_TYPE,
    CONTROL_COMMAND_SOURCE,
    CONTROL_PROTOCOL_VERSION,
    CONTROL_RECEIPT_TIMEOUT,
    PENDING_RESULTS,
    SUPPORTED_COMMAND_SOURCES,
    SUPPORTED_CONTROL_MODES,
    SUPPORTED_RESULTS,
    SUPPORTED_STORAGE_COMMANDS,
    TERMINAL_RESULTS,
)
from app.services.mqtt_publisher import publish_control_payload_async

logger = logging.getLogger(__name__)
ControlEventNotifier = Callable[[dict[str, Any]], None]


class StorageControlCommandService:
    """维护单个储能设备的在途命令和终态回执。"""

    @staticmethod
    def normalize_control_result(result: Optional[str]) -> str:
        return str(result or "").strip().lower()

    @staticmethod
    def _lock_device_row(session: Session, device_id: int) -> Optional[Device]:
        stmt = select(Device).where(Device.id == device_id)
        if hasattr(stmt, "with_for_update"):
            stmt = stmt.with_for_update()
        return session.exec(stmt).first()

    @staticmethod
    def _get_pending_control_log(session: Session, device_id: int) -> Optional[DeviceControlLog]:
        stmt = (
            select(DeviceControlLog)
            .where(DeviceControlLog.device_id == device_id)
            .where(DeviceControlLog.command_source == CONTROL_COMMAND_SOURCE)
            .where(DeviceControlLog.result.in_(tuple(PENDING_RESULTS)))
            .order_by(DeviceControlLog.created_at.desc())
            .limit(1)
        )
        log = session.exec(stmt).first()
        return log if isinstance(log, DeviceControlLog) else None

    @staticmethod
    def _get_profile(session: Session, device_id: int) -> StorageAssetProfile:
        profile = session.get(StorageAssetProfile, device_id)
        if profile is None:
            raise ValueError("储能设备缺少资产能力档案，无法校验控制边界。")
        return profile

    @staticmethod
    def _get_latest_telemetry(session: Session, device_id: int) -> Optional[StorageTelemetry]:
        return session.exec(
            select(StorageTelemetry)
            .where(StorageTelemetry.device_id == device_id)
            .order_by(StorageTelemetry.timestamp.desc())
            .limit(1)
        ).first()

    @staticmethod
    def _validate_active_power(profile: StorageAssetProfile, target: Any) -> float:
        try:
            normalized = float(target)
        except (TypeError, ValueError) as exc:
            raise ValueError("target_active_power 必须是有限数值。") from exc
        if not math.isfinite(normalized):
            raise ValueError("target_active_power 必须是有限数值。")

        if normalized >= 0:
            upper = (
                profile.max_charge_power_kw
                if profile.max_charge_power_kw is not None
                else profile.rated_power_kw
            )
            if normalized > upper:
                raise ValueError(f"充电功率不能超过设备上限 {upper} kW。")
        else:
            upper = (
                profile.max_discharge_power_kw
                if profile.max_discharge_power_kw is not None
                else profile.rated_power_kw
            )
            if abs(normalized) > upper:
                raise ValueError(f"放电功率绝对值不能超过设备上限 {upper} kW。")
        return normalized

    @staticmethod
    def _reason_payload(reason: Optional[str]) -> dict[str, Any]:
        if not reason:
            return {}
        try:
            parsed = json.loads(reason)
        except (TypeError, json.JSONDecodeError):
            return {"legacy_reason": reason}
        return parsed if isinstance(parsed, dict) else {"legacy_reason": reason}

    @staticmethod
    def build_control_log_update_event(control_log: DeviceControlLog) -> dict[str, Any]:
        return {
            "type": "device_control_log_update",
            "data": {
                "device_id": control_log.device_id,
                "command_id": str(control_log.id) if control_log.id is not None else None,
                "action": control_log.action,
                "result": control_log.result,
                "reason": control_log.reason,
                "updated_at": datetime.now().isoformat(),
            },
        }

    @staticmethod
    def publish_control_log_update_event(event: dict[str, Any]) -> None:
        from app.services.mqtt_realtime_bridge import publish_realtime_event

        publish_realtime_event(event)

    @staticmethod
    def _notify_control_log_update(
        control_log: DeviceControlLog,
        control_event_notifier: Optional[ControlEventNotifier],
    ) -> None:
        if control_event_notifier is None:
            return
        try:
            control_event_notifier(StorageControlCommandService.build_control_log_update_event(control_log))
        except Exception as exc:
            logger.warning(
                "storage control notifier failed: device_id=%s command_id=%s err=%s",
                control_log.device_id,
                control_log.id,
                exc,
            )

    @staticmethod
    def queue_command(
        session: Session,
        device: Device,
        *,
        command: str,
        operator: str,
        source: str,
        target_active_power: Optional[float] = None,
        control_mode: Optional[str] = None,
        reason: Optional[str] = None,
        publish_control_payload=None,
    ) -> dict[str, Any]:
        if command not in SUPPORTED_STORAGE_COMMANDS:
            raise ValueError(f"不支持储能控制命令 `{command}`。")
        if source not in SUPPORTED_COMMAND_SOURCES:
            raise ValueError("source 仅支持 manual/rule/day_ahead。")
        if str(device.device_category) != "storage":
            raise ValueError("目标设备不是储能设备。")

        profile = StorageControlCommandService._get_profile(session, device.id)
        normalized_power: Optional[float] = None
        normalized_mode: Optional[str] = None
        if command == "set_active_power":
            normalized_power = StorageControlCommandService._validate_active_power(profile, target_active_power)
        elif command == "set_control_mode":
            normalized_mode = str(control_mode or "").strip().lower()
            if normalized_mode not in SUPPORTED_CONTROL_MODES:
                raise ValueError("control_mode 仅支持 auto/manual。")

        StorageControlCommandService._lock_device_row(session, device.id)
        StorageControlCommandService.expire_pending_control_logs(session, device_id=device.id)
        if StorageControlCommandService._get_pending_control_log(session, device.id) is not None:
            raise ValueError("当前储能设备已有待完成的控制命令。")

        telemetry = StorageControlCommandService._get_latest_telemetry(session, device.id)
        reason_payload = {
            "command": command,
            "target_active_power": normalized_power,
            "control_mode": normalized_mode,
            "source": source,
            "data_source": getattr(telemetry, "data_source", None),
            "simulation_run_id": getattr(telemetry, "simulation_run_id", None),
        }
        if reason and reason.strip():
            reason_payload["operator_reason"] = reason.strip()
        control_log = DeviceControlLog(
            device_id=device.id,
            action=command,
            target_status=command != "stop",
            previous_status=device.is_active,
            operator=operator,
            command_source=CONTROL_COMMAND_SOURCE,
            result="accepted",
            reason=json.dumps(reason_payload, ensure_ascii=False, separators=(",", ":")),
        )
        session.add(control_log)
        session.commit()
        session.refresh(control_log)

        payload: dict[str, Any] = {
            "message_type": CONTROL_COMMAND_MESSAGE_TYPE,
            "protocol_version": CONTROL_PROTOCOL_VERSION,
            "timestamp": datetime.now().isoformat(),
            "device_id": device.id,
            "device_code": device.sn,
            "command": command,
            "command_id": str(control_log.id),
            "source": source,
        }
        if normalized_power is not None:
            payload["target_active_power"] = normalized_power
        if normalized_mode is not None:
            payload["control_mode"] = normalized_mode
        if reason and reason.strip():
            payload["reason"] = reason.strip()

        publisher = publish_control_payload or publish_control_payload_async
        publisher(
            device.id,
            payload,
            device_code=device.sn,
            worker_name=f"mqtt-storage-{command}",
        )
        return {
            "accepted": True,
            "status": "accepted",
            "message": "储能控制命令已入队",
            "command_id": str(control_log.id),
            "payload": payload,
            "log": control_log,
        }

    @staticmethod
    def apply_control_receipt(
        session: Session,
        *,
        device_id: int,
        command_id: str | int,
        result: str,
        detail: Optional[str] = None,
        device_repository=None,
        control_event_notifier: Optional[ControlEventNotifier] = None,
    ) -> DeviceControlLog:
        try:
            log_id = int(command_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("控制回执缺少有效 command_id。") from exc

        repository = device_repository or DeviceRepository
        control_log = repository.get_control_log_by_id(session, log_id)
        if (
            control_log is None
            or control_log.device_id != device_id
            or control_log.command_source != CONTROL_COMMAND_SOURCE
        ):
            raise ValueError(f"控制回执找不到匹配的储能控制日志：device_id={device_id}, command_id={command_id}")

        normalized = StorageControlCommandService.normalize_control_result(result)
        if normalized not in SUPPORTED_RESULTS - {"accepted"}:
            raise ValueError("控制回执 result 仅支持 running/success/failed/timeout/rejected。")

        current = StorageControlCommandService.normalize_control_result(control_log.result)
        if current in TERMINAL_RESULTS:
            if current == normalized:
                return control_log
            reason = StorageControlCommandService._reason_payload(control_log.reason)
            ignored = reason.setdefault("ignored_receipts", [])
            incoming = {"result": normalized, "detail": (detail or "").strip() or None}
            if incoming not in ignored:
                ignored.append(incoming)
                control_log.reason = json.dumps(reason, ensure_ascii=False, separators=(",", ":"))
                session.add(control_log)
                session.flush()
            return control_log

        control_log.result = normalized
        reason = StorageControlCommandService._reason_payload(control_log.reason)
        if detail:
            reason["receipt_detail"] = detail.strip()
        control_log.reason = json.dumps(reason, ensure_ascii=False, separators=(",", ":"))
        session.add(control_log)
        session.flush()
        StorageControlCommandService._notify_control_log_update(control_log, control_event_notifier)
        return control_log

    @staticmethod
    def expire_pending_control_logs(
        session: Session,
        *,
        device_id: Optional[int] = None,
        now: Optional[datetime] = None,
        control_event_notifier: Optional[ControlEventNotifier] = None,
    ) -> list[DeviceControlLog]:
        cutoff = (now or datetime.now()) - CONTROL_RECEIPT_TIMEOUT
        stmt = (
            select(DeviceControlLog)
            .where(DeviceControlLog.command_source == CONTROL_COMMAND_SOURCE)
            .where(DeviceControlLog.result.in_(tuple(PENDING_RESULTS)))
            .where(DeviceControlLog.created_at <= cutoff)
        )
        if device_id is not None:
            stmt = stmt.where(DeviceControlLog.device_id == device_id)
        logs = list(session.exec(stmt).all())
        for log in logs:
            log.result = "timeout"
            reason = StorageControlCommandService._reason_payload(log.reason)
            reason["timeout_detail"] = "在约定等待时间内未收到设备回执"
            log.reason = json.dumps(reason, ensure_ascii=False, separators=(",", ":"))
            session.add(log)
        if logs:
            session.commit()
            for log in logs:
                StorageControlCommandService._notify_control_log_update(log, control_event_notifier)
        return logs
