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

from app.core.settings import settings
from app.integrations.jkwf_lcd.capacity import build_capacity_expansion
from app.models.tables import CapacitorBankControlProfile, Device, DeviceControlLog
from app.repositories.device_repository import DeviceRepository
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_publisher import publish_control_payload_async, publish_parameter_write_async

CONTROL_PROFILE_STALE_AFTER = timedelta(hours=1)
CONTROL_RECEIPT_TIMEOUT = timedelta(minutes=2)
CONTROL_PROTOCOL_VERSION = "campus-control.v1"
CONTROL_COMMAND_MESSAGE_TYPE = "control_command"
CONTROL_RECEIPT_MESSAGE_TYPE = "control_receipt"
CONTROL_RESULT_ACCEPTED = "accepted"
CONTROL_RESULT_RUNNING = "running"
CONTROL_RESULT_SUCCESS = "success"
CONTROL_RESULT_FAILED = "failed"
CONTROL_RESULT_TIMEOUT = "timeout"
CONTROL_RESULT_REJECTED = "rejected"
PENDING_CONTROL_RESULTS = {CONTROL_RESULT_ACCEPTED, CONTROL_RESULT_RUNNING}
SUPPORTED_CONTROL_RESULTS = (
    CONTROL_RESULT_ACCEPTED,
    CONTROL_RESULT_RUNNING,
    CONTROL_RESULT_SUCCESS,
    CONTROL_RESULT_FAILED,
    CONTROL_RESULT_TIMEOUT,
    CONTROL_RESULT_REJECTED,
)


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
    "alarm_drive_event": CapacitorBankControlParameterSpec("alarm_drive_event", "0xE1", "报警驱动事件", "int", 0, 4),
    "baud_rate": CapacitorBankControlParameterSpec(
        "baud_rate",
        "0xE2",
        "通讯速率",
        "enum",
        allowed_values=(2400, 9600, 19200, 38400, 115200),
    ),
    "terminal_assignment_scheme": CapacitorBankControlParameterSpec("terminal_assignment_scheme", "0xE3", "端子分配方案", "int", 0, 3),
    "current_polarity_identification_enabled": CapacitorBankControlParameterSpec(
        "current_polarity_identification_enabled",
        "0xE4",
        "电流极性识别",
        "bool",
    ),
}

REMOTE_COMMAND_SPECS: dict[str, dict[str, str]] = {
    "manual_switch": {
        "label": "手动投切",
        "command": "manual_switch",
    },
    "manual_switch_test": {
        "label": "手动投切测试",
        "command": "manual_switch_test",
    },
    "reset_alarm": {
        "label": "报警复位",
        "command": "reset_alarm",
    },
    "switch_control_mode": {
        "label": "控制模式切换",
        "command": "switch_control_mode",
    },
}


class CapacitorBankService:
    """传统电容补偿控制器控制台参数服务。"""

    CONTROL_ACTION_LABELS = {
        "start": "启用设备",
        "stop": "停用设备",
        "manual_switch": "手动投切",
        "manual_switch_test": "手动投切测试",
        "reset_alarm": "报警复位",
        "switch_control_mode": "控制模式切换",
    }

    CONTROL_RESULT_LABELS = {
        CONTROL_RESULT_ACCEPTED: "已入队",
        CONTROL_RESULT_RUNNING: "设备执行中",
        CONTROL_RESULT_SUCCESS: "执行成功",
        CONTROL_RESULT_FAILED: "执行失败",
        CONTROL_RESULT_TIMEOUT: "设备回执超时",
        CONTROL_RESULT_REJECTED: "设备拒绝执行",
    }

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
    def build_capacity_expansion_payload(profile: Optional[CapacitorBankControlProfile]) -> dict[str, Any]:
        if profile is None:
            return {
                "split_capacity_expansion": {
                    "phase_a_groups": [],
                    "phase_b_groups": [],
                    "phase_c_groups": [],
                },
                "common_capacity_expansion": {
                    "common_1_groups": [],
                    "common_2_groups": [],
                    "common_3_groups": [],
                },
            }
        return build_capacity_expansion(
            common_capacity_code=profile.common_capacity_code,
            split_capacity_code=profile.split_capacity_code,
            common_step_capacity_kvar=profile.common_step_capacity_kvar,
            split_step_capacity_kvar=profile.split_step_capacity_kvar,
            common_output_circuit_count=profile.common_output_circuit_count,
            split_output_circuit_count=profile.split_output_circuit_count,
        )

    @staticmethod
    def get_control_capabilities() -> dict[str, Any]:
        return {
            "supports_read": True,
            "supports_write": True,
            "supports_remote_control": True,
            "write_status_message": "参数写入已接入正式控制链路，仅管理员可发起；accepted 仅表示指令入队，仍需结合设备回执与最新回读确认。",
            "remote_control_status_message": "远程控制已收敛到正式控制链路：命令下发到 campus/control/{device_id}，设备通过 control_receipt 回执执行状态。",
            "protocol_version": CONTROL_PROTOCOL_VERSION,
            "command_message_type": CONTROL_COMMAND_MESSAGE_TYPE,
            "receipt_message_type": CONTROL_RECEIPT_MESSAGE_TYPE,
            "control_topic_template": f"{settings.mqtt_control_topic_prefix}{{device_id}}",
            "receipt_topic": settings.mqtt_topic,
            "receipt_timeout_seconds": int(CONTROL_RECEIPT_TIMEOUT.total_seconds()),
            "supported_results": list(SUPPORTED_CONTROL_RESULTS),
        }

    @staticmethod
    def get_remote_command_spec(action: str) -> dict[str, str]:
        spec = REMOTE_COMMAND_SPECS.get(action)
        if spec is None:
            raise ValueError(f"当前不支持远程控制动作 `{action}`。")
        return spec

    @staticmethod
    def get_action_label(action: str) -> str:
        if action.startswith("write:"):
            parameter_key = action[6:]
            spec = PARAMETER_WRITE_SPECS.get(parameter_key)
            if spec:
                return f"参数写入 · {spec.label}"
            return f"参数写入 · {parameter_key}"
        return CapacitorBankService.CONTROL_ACTION_LABELS.get(action, action)

    @staticmethod
    def normalize_control_result(result: Optional[str]) -> str:
        normalized = str(result or "").strip().lower()
        if normalized in SUPPORTED_CONTROL_RESULTS:
            return normalized
        return CONTROL_RESULT_FAILED

    @staticmethod
    def get_result_label(result: Optional[str]) -> str:
        return CapacitorBankService.CONTROL_RESULT_LABELS.get(
            CapacitorBankService.normalize_control_result(result),
            "执行异常",
        )

    @staticmethod
    def build_command_payload(
        device_id: int,
        *,
        command: str,
        command_id: str,
        reason: Optional[str] = None,
        extras: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "message_type": CONTROL_COMMAND_MESSAGE_TYPE,
            "protocol_version": CONTROL_PROTOCOL_VERSION,
            "timestamp": datetime.now().isoformat(),
            "device_id": device_id,
            "command": command,
            "command_id": command_id,
        }
        if reason:
            payload["reason"] = reason
        if extras:
            payload.update(extras)
        return payload

    @staticmethod
    def build_manual_switch_command_args(command_args: Optional[dict[str, Any]]) -> dict[str, Any]:
        args = dict(command_args or {})
        manual_mode = str(args.get("manual_mode") or "").strip().lower()
        phase = str(args.get("phase") or "").strip().upper()
        switch_action = str(args.get("switch_action") or "").strip().lower()

        if manual_mode not in {"manual", "auto"}:
            raise ValueError("手动投切必须指定 manual_mode=manual/auto。")
        if phase not in {"A", "B", "C", "COMMON"}:
            raise ValueError("手动投切必须指定 phase=A/B/C/COMMON。")
        if switch_action not in {"none", "on", "off"}:
            raise ValueError("手动投切必须指定 switch_action=none/on/off。")

        mode_code = 1 if manual_mode == "manual" else 0
        phase_code = {"A": 0, "B": 1, "C": 2, "COMMON": 3}[phase]
        switch_action_code = {"none": 0, "on": 0x11, "off": 0x22}[switch_action]

        return {
            "manual_mode": manual_mode,
            "phase": phase,
            "switch_action": switch_action,
            "protocol_function_code": "0x44",
            "manual_mode_code": mode_code,
            "phase_code": phase_code,
            "switch_action_code": switch_action_code,
        }

    @staticmethod
    def expire_pending_control_logs(
        session: Session,
        *,
        device_id: Optional[int] = None,
        now: Optional[datetime] = None,
    ) -> list[DeviceControlLog]:
        cutoff = (now or datetime.now()) - CONTROL_RECEIPT_TIMEOUT
        stmt = select(DeviceControlLog).where(DeviceControlLog.result.in_(tuple(PENDING_CONTROL_RESULTS)))
        if device_id is not None:
            stmt = stmt.where(DeviceControlLog.device_id == device_id)
        stmt = stmt.where(DeviceControlLog.created_at <= cutoff)
        expired_logs = list(session.exec(stmt).all())
        if not expired_logs:
            return []

        timeout_suffix = "设备回执超时：在约定等待时间内未收到回执"
        for log in expired_logs:
            log.result = CONTROL_RESULT_TIMEOUT
            if log.reason:
                if timeout_suffix not in log.reason:
                    log.reason = f"{log.reason} | {timeout_suffix}"
            else:
                log.reason = timeout_suffix
            session.add(log)
        session.commit()
        return expired_logs

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
    ) -> dict[str, Any]:
        health = IngestionHealthService.get_device_health(session, device.id)
        if health.get("is_online") is False:
            raise ControlProfileWritePreconditionError("当前设备离线，暂不允许下发参数写入。")

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
            result=CONTROL_RESULT_ACCEPTED,
            reason=" | ".join(log_reason_parts),
        )
        session.add(control_log)
        session.commit()
        session.refresh(control_log)

        publish_parameter_write_async(
            device.id,
            parameter_key,
            normalized_value,
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
        spec = CapacitorBankService.get_remote_command_spec(action)
        normalized_reason = reason.strip() if reason else ""
        log_reason = normalized_reason or f"控制台{spec['label']}"
        normalized_command_args: dict[str, Any] = {}
        if action == "manual_switch":
            normalized_command_args = CapacitorBankService.build_manual_switch_command_args(command_args)

        control_log = DeviceControlLog(
            device_id=device.id,
            action=action,
            target_status=device.is_active,
            previous_status=device.is_active,
            operator=operator,
            command_source="remote-control-api",
            result=CONTROL_RESULT_ACCEPTED,
            reason=log_reason,
        )
        session.add(control_log)
        session.commit()
        session.refresh(control_log)

        publish_control_payload_async(
            device.id,
            CapacitorBankService.build_command_payload(
                device.id,
                command=spec["command"],
                command_id=str(control_log.id),
                reason=normalized_reason or spec["label"],
                extras=normalized_command_args or None,
            ),
            worker_name=f"mqtt-remote-{action}",
        )
        return {
            "accepted": True,
            "status": CONTROL_RESULT_ACCEPTED,
            "message": f"{spec['label']}指令已入队",
            "command_id": str(control_log.id),
        }

    @staticmethod
    def apply_control_receipt(
        session: Session,
        *,
        device_id: int,
        command_id: str | int,
        result: str,
        detail: Optional[str] = None,
    ) -> DeviceControlLog:
        try:
            control_log_id = int(command_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("控制回执缺少有效 command_id。") from exc

        control_log = DeviceRepository.get_control_log_by_id(session, control_log_id)
        if control_log is None or control_log.device_id != device_id:
            raise ValueError(f"控制回执找不到匹配日志：device_id={device_id}, command_id={command_id}")

        normalized_result = CapacitorBankService.normalize_control_result(result)
        if normalized_result not in set(SUPPORTED_CONTROL_RESULTS) - {CONTROL_RESULT_ACCEPTED}:
            raise ValueError("控制回执 result 仅支持 running/success/failed/timeout/rejected。")

        control_log.result = normalized_result
        detail_text = (detail or "").strip()
        if detail_text:
            if normalized_result == CONTROL_RESULT_SUCCESS:
                prefix = "设备回执成功"
            elif normalized_result == CONTROL_RESULT_RUNNING:
                prefix = "设备执行中"
            elif normalized_result == CONTROL_RESULT_TIMEOUT:
                prefix = "设备回执超时"
            elif normalized_result == CONTROL_RESULT_REJECTED:
                prefix = "设备拒绝执行"
            else:
                prefix = "设备回执失败"
            suffix = f"{prefix}: {detail_text}"
            if control_log.reason:
                if suffix not in control_log.reason:
                    control_log.reason = f"{control_log.reason} | {suffix}"
            else:
                control_log.reason = suffix

        session.add(control_log)
        session.flush()
        return control_log
