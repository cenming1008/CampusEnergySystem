"""
电容补偿控制器 facade。

保留历史调用入口，内部委托给更细的子型专属服务：
- 参数快照层：CapacitorBankControlProfileService
- 参数写入层：CapacitorBankParameterWriteService
- 控制命令层：CapacitorBankControlCommandService
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlmodel import Session, select

from app.core.settings import settings
from app.models.tables import CapacitorBankControlProfile, CapacitorBankTelemetry, Device, DeviceControlLog
from app.repositories.device_repository import DeviceRepository
from app.services.devices.compensation.capacitor_bank.control_command_service import CapacitorBankControlCommandService
from app.services.devices.compensation.capacitor_bank.control_profile_service import CapacitorBankControlProfileService
from app.services.devices.compensation.capacitor_bank.specs import (
    CONTROL_COMMAND_MESSAGE_TYPE,
    CONTROL_PROTOCOL_VERSION,
    CONTROL_RECEIPT_MESSAGE_TYPE,
    CONTROL_RECEIPT_TIMEOUT,
    CONTROL_RESULT_ACCEPTED,
    CONTROL_RESULT_FAILED,
    CONTROL_RESULT_REJECTED,
    CONTROL_RESULT_RUNNING,
    CONTROL_RESULT_SUCCESS,
    CONTROL_RESULT_TIMEOUT,
    GATEWAY_UAT_WRITABLE_PARAMETERS,
    PARAMETER_WRITE_SPECS,
    SUPPORTED_CONTROL_RESULTS,
    CapacitorBankControlParameterSpec,
    ControlProfileWritePreconditionError,
    PendingParameterWriteConflictError,
    get_control_receipt_timeout,
)
from app.services.devices.compensation.capacitor_bank.parameter_write_service import CapacitorBankParameterWriteService
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_publisher import publish_control_payload_async, publish_parameter_write_async


class CapacitorBankService:
    """传统电容补偿控制器兼容 facade。"""

    CONTROL_ACTION_LABELS = CapacitorBankControlCommandService.CONTROL_ACTION_LABELS
    CONTROL_RESULT_LABELS = CapacitorBankControlCommandService.CONTROL_RESULT_LABELS

    @staticmethod
    def _sample_history_records(records: list, limit: int):
        if len(records) <= limit or limit < 3:
            return records

        sampled = [records[0]]
        interior_target = limit - 2
        last_index = len(records) - 1

        for index in range(1, interior_target + 1):
            point_index = round((index * last_index) / (interior_target + 1))
            point = records[min(last_index - 1, max(1, point_index))]
            if sampled[-1] is not point:
                sampled.append(point)

        if sampled[-1] is not records[last_index]:
            sampled.append(records[last_index])

        return sampled

    @staticmethod
    def get_latest_telemetry(session: Session, device_id: int) -> Optional[CapacitorBankTelemetry]:
        return session.exec(
            select(CapacitorBankTelemetry)
            .where(CapacitorBankTelemetry.device_id == device_id)
            .order_by(CapacitorBankTelemetry.timestamp.desc())
            .limit(1)
        ).first()

    @staticmethod
    def list_telemetry_history(
        session: Session,
        device_id: int,
        *,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 200,
    ) -> list[CapacitorBankTelemetry]:
        stmt = select(CapacitorBankTelemetry).where(CapacitorBankTelemetry.device_id == device_id)
        if start_time:
            stmt = stmt.where(CapacitorBankTelemetry.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(CapacitorBankTelemetry.timestamp <= end_time)
        records = list(session.exec(stmt.order_by(CapacitorBankTelemetry.timestamp.asc())).all())
        return CapacitorBankService._sample_history_records(records, limit)

    @staticmethod
    def get_parameter_spec(parameter_key: str) -> CapacitorBankControlParameterSpec:
        return CapacitorBankParameterWriteService.get_parameter_spec(parameter_key)

    @staticmethod
    def get_control_profile(session: Session, device_id: int) -> Optional[CapacitorBankControlProfile]:
        return CapacitorBankControlProfileService.get_control_profile(session, device_id)

    @staticmethod
    def upsert_control_profile(
        session: Session,
        device_id: int,
        payload: dict[str, Any],
        *,
        snapshot_timestamp: Optional[Any] = None,
        source: str = "telemetry",
    ) -> CapacitorBankControlProfile:
        return CapacitorBankControlProfileService.upsert_control_profile(
            session,
            device_id,
            payload,
            snapshot_timestamp=snapshot_timestamp,
            source=source,
        )

    @staticmethod
    def get_profile_source_status(profile: Optional[CapacitorBankControlProfile]) -> str:
        return CapacitorBankControlProfileService.get_profile_source_status(profile)

    @staticmethod
    def _serialize_capacity_steps(value: Any) -> Optional[str]:
        return CapacitorBankControlProfileService._serialize_capacity_steps(value)

    @staticmethod
    def _parse_capacity_steps(value: Any) -> list[float]:
        return CapacitorBankControlProfileService._parse_capacity_steps(value)

    @staticmethod
    def build_direct_capacity_steps_payload(profile: Optional[CapacitorBankControlProfile]) -> dict[str, list[float]]:
        return CapacitorBankControlProfileService.build_direct_capacity_steps_payload(profile)

    @staticmethod
    def build_capacity_expansion_payload(profile: Optional[CapacitorBankControlProfile]) -> dict[str, Any]:
        return CapacitorBankControlProfileService.build_capacity_expansion_payload(profile)

    @staticmethod
    def get_control_capabilities() -> dict[str, Any]:
        return {
            "supports_read": True,
            "supports_write": True,
            "supports_remote_control": True,
            "write_status_message": "参数写入已接入正式控制链路，仅管理员可发起；accepted 仅表示指令入队，仍需结合设备回执与最新回读确认。",
            "remote_control_status_message": "远程控制已收敛到正式控制链路：命令下发到 campus/control/{device_code}，设备通过 control_receipt 回执执行状态。",
            "protocol_version": CONTROL_PROTOCOL_VERSION,
            "command_message_type": CONTROL_COMMAND_MESSAGE_TYPE,
            "receipt_message_type": CONTROL_RECEIPT_MESSAGE_TYPE,
            "control_topic_template": f"{settings.mqtt_control_topic_prefix}{{device_code}}",
            "receipt_topic": settings.mqtt_topic,
            "receipt_timeout_seconds": int(get_control_receipt_timeout().total_seconds()),
            "supported_results": list(SUPPORTED_CONTROL_RESULTS),
            "remote_commands": CapacitorBankControlCommandService.get_remote_command_capabilities(),
            "writable_parameters": list(GATEWAY_UAT_WRITABLE_PARAMETERS),
        }

    @staticmethod
    def get_remote_command_spec(action: str) -> dict[str, Any]:
        return CapacitorBankControlCommandService.get_remote_command_spec(action)

    @staticmethod
    def get_action_label(action: str) -> str:
        return CapacitorBankControlCommandService.get_action_label(action)

    @staticmethod
    def normalize_control_result(result: Optional[str]) -> str:
        return CapacitorBankControlCommandService.normalize_control_result(result)

    @staticmethod
    def get_result_label(result: Optional[str]) -> str:
        return CapacitorBankControlCommandService.get_result_label(result)

    @staticmethod
    def build_command_payload(
        device_id: int,
        *,
        device_code: Optional[str],
        command: str,
        command_id: str,
        reason: Optional[str] = None,
        extras: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return CapacitorBankControlCommandService.build_command_payload(
            device_id,
            device_code=device_code,
            command=command,
            command_id=command_id,
            reason=reason,
            extras=extras,
        )

    @staticmethod
    def publish_control_log_update_event(event: dict[str, Any]) -> None:
        return CapacitorBankControlCommandService.publish_control_log_update_event(event)

    @staticmethod
    def build_manual_switch_command_args(command_args: Optional[dict[str, Any]]) -> dict[str, Any]:
        return CapacitorBankControlCommandService.build_manual_switch_command_args(command_args)

    @staticmethod
    def build_control_mode_switch_command_args(reason: Optional[str]) -> dict[str, Any]:
        return CapacitorBankControlCommandService.build_control_mode_switch_command_args(reason)

    @staticmethod
    def expire_pending_control_logs(
        session: Session,
        *,
        device_id: Optional[int] = None,
        now: Optional[Any] = None,
        control_event_notifier: Optional[Any] = None,
    ) -> list[DeviceControlLog]:
        return CapacitorBankControlCommandService.expire_pending_control_logs(
            session,
            device_id=device_id,
            now=now,
            control_event_notifier=control_event_notifier,
        )

    @staticmethod
    def normalize_write_value(parameter_key: str, target_value: Any) -> Any:
        return CapacitorBankParameterWriteService.normalize_write_value(parameter_key, target_value)

    @staticmethod
    def submit_control_profile_write(
        session: Session,
        device: Device,
        *,
        parameter_key: str,
        target_value: Any,
        operator: str,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        return CapacitorBankParameterWriteService.submit_control_profile_write(
            session,
            device,
            parameter_key=parameter_key,
            target_value=target_value,
            operator=operator,
            reason=reason,
            health_service=IngestionHealthService,
            publish_parameter_write=publish_parameter_write_async,
            get_control_profile=CapacitorBankService.get_control_profile,
            get_profile_source_status=CapacitorBankService.get_profile_source_status,
        )

    @staticmethod
    def submit_remote_control_command(
        session: Session,
        device: Device,
        *,
        action: str,
        operator: str,
        reason: Optional[str] = None,
        command_args: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return CapacitorBankControlCommandService.submit_remote_control_command(
            session,
            device,
            action=action,
            operator=operator,
            reason=reason,
            command_args=command_args,
            publish_control_payload=publish_control_payload_async,
        )

    @staticmethod
    def apply_control_receipt(
        session: Session,
        *,
        device_id: int,
        command_id: str | int,
        result: str,
        detail: Optional[str] = None,
        control_event_notifier: Optional[Any] = None,
    ) -> DeviceControlLog:
        return CapacitorBankControlCommandService.apply_control_receipt(
            session,
            device_id=device_id,
            command_id=command_id,
            result=result,
            detail=detail,
            device_repository=DeviceRepository,
            control_event_notifier=control_event_notifier,
        )
