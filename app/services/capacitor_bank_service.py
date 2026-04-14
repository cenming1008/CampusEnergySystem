"""
电容补偿控制器参数服务。

当前阶段提供：
- 参数快照回读写入
- 控制台只读参数档案
- 写入接口占位
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlmodel import Session, select

from app.models.tables import CapacitorBankControlProfile, Device, DeviceControlLog
from app.services.mqtt_publisher import publish_parameter_write_async

CONTROL_PROFILE_STALE_AFTER = timedelta(hours=1)


class ControlProfileWritePreconditionError(RuntimeError):
    """参数写入前置条件不满足。"""


@dataclass(frozen=True)
class CapacitorBankControlParameterSpec:
    key: str
    register: str
    label: str
    value_kind: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[tuple[Any, ...]] = None
    max_length: Optional[int] = None


PARAMETER_WRITE_SPECS: dict[str, CapacitorBankControlParameterSpec] = {
    "switch_on_power_factor": CapacitorBankControlParameterSpec("switch_on_power_factor", "0xD2", "投入功率因数", "pf", 70, 125),
    "switch_off_power_factor": CapacitorBankControlParameterSpec("switch_off_power_factor", "0xD3", "切除功率因数", "pf", 75, 130),
    "switch_on_delay_seconds": CapacitorBankControlParameterSpec("switch_on_delay_seconds", "0xD4", "投入延时时间", "int", 0, 300),
    "switch_off_delay_seconds": CapacitorBankControlParameterSpec("switch_off_delay_seconds", "0xD5", "切除延时时间", "int", 0, 100),
    "common_output_circuit_count": CapacitorBankControlParameterSpec("common_output_circuit_count", "0xD6", "共补输出回路", "int", 0, 24),
    "split_output_circuit_count": CapacitorBankControlParameterSpec("split_output_circuit_count", "0xD7", "分补输出回路", "int", 0, 8),
    "common_capacity_code": CapacitorBankControlParameterSpec("common_capacity_code", "0xD8", "共补容量编码", "string", max_length=32),
    "split_capacity_code": CapacitorBankControlParameterSpec("split_capacity_code", "0xD9", "分补容量编码", "string", max_length=32),
    "common_step_capacity_kvar": CapacitorBankControlParameterSpec("common_step_capacity_kvar", "0xDA", "共补阶梯容量", "float", 0.1, 150.0),
    "split_step_capacity_kvar": CapacitorBankControlParameterSpec("split_step_capacity_kvar", "0xDB", "分补阶梯容量", "float", 0.1, 50.0),
    "ct_primary_current": CapacitorBankControlParameterSpec("ct_primary_current", "0xDC", "互感器一次值", "int", 1, 1600),
    "overvoltage_threshold": CapacitorBankControlParameterSpec("overvoltage_threshold", "0xDD", "过压保护门限", "float", 230.0, 265.0),
    "voltage_harmonic_threshold": CapacitorBankControlParameterSpec("voltage_harmonic_threshold", "0xDE", "电压谐波门限", "float", 0.0, 50.0),
    "current_harmonic_threshold": CapacitorBankControlParameterSpec("current_harmonic_threshold", "0xDF", "电流谐波门限", "float", 0.0, 200.0),
    "temperature_upper_limit": CapacitorBankControlParameterSpec("temperature_upper_limit", "0xE0", "温度上限门限", "float", 50.0, 100.0),
    "alarm_drive_event": CapacitorBankControlParameterSpec("alarm_drive_event", "0xE1", "报警驱动事件", "string", max_length=32),
    "baud_rate": CapacitorBankControlParameterSpec(
        "baud_rate",
        "0xE2",
        "通讯速率",
        "enum",
        allowed_values=(2400, 9600, 19200, 38400, 115200),
    ),
    "terminal_assignment_scheme": CapacitorBankControlParameterSpec("terminal_assignment_scheme", "0xE3", "端子分配方案", "string", max_length=32),
    "current_polarity_identification_enabled": CapacitorBankControlParameterSpec(
        "current_polarity_identification_enabled",
        "0xE4",
        "电流极性识别",
        "bool",
    ),
}


class CapacitorBankService:
    """传统电容补偿控制器控制台参数服务。"""

    @staticmethod
    def get_parameter_spec(parameter_key: str) -> CapacitorBankControlParameterSpec:
        spec = PARAMETER_WRITE_SPECS.get(parameter_key)
        if spec is None:
            raise ValueError(f"当前不支持参数 `{parameter_key}` 的写入。")
        return spec

    @staticmethod
    def get_control_profile(session: Session, device_id: int) -> Optional[CapacitorBankControlProfile]:
        return session.exec(
            select(CapacitorBankControlProfile).where(CapacitorBankControlProfile.device_id == device_id)
        ).first()

    @staticmethod
    def upsert_control_profile(
        session: Session,
        device_id: int,
        payload: dict[str, Any],
        *,
        snapshot_timestamp: Optional[datetime] = None,
        source: str = "telemetry",
    ) -> CapacitorBankControlProfile:
        profile = CapacitorBankService.get_control_profile(session, device_id)
        if profile is None:
            profile = CapacitorBankControlProfile(device_id=device_id)

        for field, value in payload.items():
            if value is None or not hasattr(profile, field):
                continue
            setattr(profile, field, value)

        profile.source = source
        profile.snapshot_timestamp = snapshot_timestamp or datetime.now()
        profile.updated_at = datetime.now()
        session.add(profile)
        return profile

    @staticmethod
    def get_profile_source_status(profile: Optional[CapacitorBankControlProfile]) -> str:
        if profile is None:
            return "empty"
        snapshot = profile.snapshot_timestamp or profile.updated_at
        if snapshot is None:
            return "unknown"
        if datetime.now() - snapshot > CONTROL_PROFILE_STALE_AFTER:
            return "stale"
        return "fresh"

    @staticmethod
    def get_control_capabilities() -> dict[str, Any]:
        return {
            "supports_read": True,
            "supports_write": True,
            "supports_remote_control": True,
            "write_status_message": "当前已开放后端参数写入受控链路，前端编辑入口仍保持关闭。",
            "remote_control_status_message": "当前已开放启用/停用控制动作，其他高风险控制仍未开通。",
        }

    @staticmethod
    def normalize_write_value(parameter_key: str, target_value: Any) -> Any:
        spec = CapacitorBankService.get_parameter_spec(parameter_key)

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
                return target_value
            if isinstance(target_value, (int, float)) and target_value in {0, 1}:
                return bool(target_value)
            normalized = str(target_value).strip().lower()
            if normalized in {"1", "true", "on", "yes", "enable", "enabled"}:
                return True
            if normalized in {"0", "false", "off", "no", "disable", "disabled"}:
                return False
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
    ) -> dict[str, Any]:
        profile = CapacitorBankService.get_control_profile(session, device.id)
        source_status = CapacitorBankService.get_profile_source_status(profile)
        if source_status in {"empty", "unknown"}:
            raise ControlProfileWritePreconditionError("当前设备尚未完成真实参数回读，暂不允许下发参数写入。")

        spec = CapacitorBankService.get_parameter_spec(parameter_key)
        normalized_value = CapacitorBankService.normalize_write_value(parameter_key, target_value)
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
            result="accepted",
            reason=" | ".join(log_reason_parts),
        )
        session.add(control_log)
        session.commit()
        session.refresh(control_log)

        publish_parameter_write_async(
            device.id,
            parameter_key,
            normalized_value,
            reason=normalized_reason or None,
            register=spec.register,
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
