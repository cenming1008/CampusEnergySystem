"""
电容补偿控制器参数写入服务。

负责参数值归一、写入前置条件、控制日志留痕与 MQTT 参数写入下发。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlmodel import Session

from app.models.tables import Device, DeviceControlLog
from app.services.devices.compensation.capacitor_bank.control_profile_service import CapacitorBankControlProfileService
from app.services.devices.compensation.capacitor_bank.specs import (
    CONTROL_COMMAND_MESSAGE_TYPE,
    CONTROL_PROTOCOL_VERSION,
    CONTROL_RESULT_ACCEPTED,
    PARAMETER_WRITE_SPECS,
    CapacitorBankControlParameterSpec,
    ControlProfileWritePreconditionError,
)
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_publisher import publish_parameter_write_async


class CapacitorBankParameterWriteService:
    """电容补偿控制器参数写入层。"""

    @staticmethod
    def get_parameter_spec(parameter_key: str) -> CapacitorBankControlParameterSpec:
        spec = PARAMETER_WRITE_SPECS.get(parameter_key)
        if spec is None:
            raise ValueError(f"当前不支持参数 `{parameter_key}` 的写入。")
        return spec

    @staticmethod
    def normalize_write_value(parameter_key: str, target_value: Any) -> Any:
        spec = CapacitorBankParameterWriteService.get_parameter_spec(parameter_key)

        if spec.value_kind == "pf":
            try:
                parsed = float(target_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{spec.label} 必须是数值。") from exc
            if 0.7 <= parsed <= 1.3:
                parsed = round(parsed * 100)
            else:
                parsed = round(parsed)
            if spec.min_value is not None and parsed < spec.min_value:
                raise ValueError(f"{spec.label} 不能小于 {spec.min_value}。")
            if spec.max_value is not None and parsed > spec.max_value:
                raise ValueError(f"{spec.label} 不能大于 {spec.max_value}。")
            return int(parsed)

        if spec.value_kind == "int":
            try:
                parsed = int(float(target_value))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{spec.label} 必须是整数。") from exc
            if spec.min_value is not None and parsed < spec.min_value:
                raise ValueError(f"{spec.label} 不能小于 {spec.min_value}。")
            if spec.max_value is not None and parsed > spec.max_value:
                raise ValueError(f"{spec.label} 不能大于 {spec.max_value}。")
            return parsed

        if spec.value_kind == "float":
            try:
                parsed = float(target_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{spec.label} 必须是数值。") from exc
            if spec.min_value is not None and parsed < spec.min_value:
                raise ValueError(f"{spec.label} 不能小于 {spec.min_value}。")
            if spec.max_value is not None and parsed > spec.max_value:
                raise ValueError(f"{spec.label} 不能大于 {spec.max_value}。")
            return round(parsed, 2)

        if spec.value_kind == "enum":
            try:
                parsed = int(float(target_value))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{spec.label} 必须是数值。") from exc
            if spec.allowed_values is not None and parsed not in spec.allowed_values:
                raise ValueError(f"{spec.label} 仅支持 {', '.join(str(item) for item in spec.allowed_values)}。")
            return parsed

        if spec.value_kind == "bool":
            if isinstance(target_value, bool):
                return 0 if target_value else 1
            if isinstance(target_value, (int, float)) and target_value in {0, 1}:
                return int(target_value)
            normalized = str(target_value).strip().lower()
            if normalized in {"1", "true", "on", "yes", "enable", "enabled"}:
                return 0
            if normalized in {"0", "false", "off", "no", "disable", "disabled"}:
                return 1
            raise ValueError(f"{spec.label} 仅支持 true/false 或 1/0。")

        normalized = str(target_value).strip()
        if not normalized:
            raise ValueError(f"{spec.label} 不能为空。")
        if spec.max_length is not None and len(normalized) > spec.max_length:
            raise ValueError(f"{spec.label} 长度不能超过 {spec.max_length} 个字符。")
        return normalized

    @staticmethod
    def submit_control_profile_write(
        session: Session,
        device: Device,
        *,
        parameter_key: str,
        target_value: Any,
        operator: str,
        reason: Optional[str] = None,
        health_service=None,
        publish_parameter_write=None,
        get_control_profile=None,
        get_profile_source_status=None,
    ) -> dict[str, Any]:
        health_service = health_service or IngestionHealthService
        publish_parameter_write = publish_parameter_write or publish_parameter_write_async
        get_control_profile = get_control_profile or CapacitorBankControlProfileService.get_control_profile
        get_profile_source_status = (
            get_profile_source_status or CapacitorBankControlProfileService.get_profile_source_status
        )

        health = health_service.get_device_health(session, device.id)
        if health.get("is_online") is False:
            raise ControlProfileWritePreconditionError("当前设备离线，暂不允许下发参数写入。")

        profile = get_control_profile(session, device.id)
        source_status = get_profile_source_status(profile)
        if source_status in {"empty", "unknown"}:
            raise ControlProfileWritePreconditionError("当前设备尚未完成真实参数回读，暂不允许下发参数写入。")

        spec = CapacitorBankParameterWriteService.get_parameter_spec(parameter_key)
        normalized_value = CapacitorBankParameterWriteService.normalize_write_value(parameter_key, target_value)
        normalized_reason = reason.strip() if reason else ""

        log_reason_parts = [f"{spec.label} -> {normalized_value}"]
        if normalized_reason:
            log_reason_parts.append(normalized_reason)
        control_log = DeviceControlLog(
            device_id=device.id,
            action=f"write:{parameter_key}",
            target_status=device.is_active,
            previous_status=device.is_active,
            operator=operator,
            command_source="control-profile-api",
            result=CONTROL_RESULT_ACCEPTED,
            reason=" | ".join(log_reason_parts),
        )
        session.add(control_log)
        session.commit()
        session.refresh(control_log)

        publish_parameter_write(
            device.id,
            parameter_key,
            normalized_value,
            device_code=device.sn,
            command_id=str(control_log.id),
            reason=normalized_reason or None,
            register=spec.register,
            protocol_version=CONTROL_PROTOCOL_VERSION,
            message_type=CONTROL_COMMAND_MESSAGE_TYPE,
            sent_at=datetime.now().isoformat(),
        )

        message = f"参数写入指令已入队：{spec.label} -> {normalized_value}"
        if source_status == "stale":
            message += "（注意：当前参数快照已过期，请在设备回读后再次核对）"
        return {
            "accepted": True,
            "status": "accepted",
            "message": message,
            "command_id": str(control_log.id),
        }
