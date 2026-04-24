"""
电容补偿控制器远程控制命令服务。

负责远程控制命令编码、控制日志状态收敛与设备回执落库，不处理参数快照读写。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Optional

from sqlmodel import Session, select

from app.models.tables import Device, DeviceControlLog
from app.repositories.device_repository import DeviceRepository
from app.services.devices.compensation.capacitor_bank.specs import (
    CONTROL_COMMAND_MESSAGE_TYPE,
    CONTROL_PROTOCOL_VERSION,
    CONTROL_RECEIPT_TIMEOUT,
    CONTROL_RESULT_ACCEPTED,
    CONTROL_RESULT_FAILED,
    CONTROL_RESULT_REJECTED,
    CONTROL_RESULT_RUNNING,
    CONTROL_RESULT_SUCCESS,
    CONTROL_RESULT_TIMEOUT,
    PARAMETER_WRITE_SPECS,
    PENDING_CONTROL_RESULTS,
    REMOTE_COMMAND_SPECS,
    SUPPORTED_CONTROL_RESULTS,
    TERMINAL_CONTROL_RESULTS,
    get_control_receipt_timeout,
)
from app.services.mqtt_publisher import publish_control_payload_async

logger = logging.getLogger(__name__)
ControlEventNotifier = Callable[[dict[str, Any]], None]
CONTROL_RECEIPT_RESULT_ALIASES = {
    "unsupported": CONTROL_RESULT_REJECTED,
    "not_supported": CONTROL_RESULT_REJECTED,
    "not-supported": CONTROL_RESULT_REJECTED,
    "refused": CONTROL_RESULT_REJECTED,
    "invalid": CONTROL_RESULT_REJECTED,
    "reject": CONTROL_RESULT_REJECTED,
}


class CapacitorBankControlCommandService:
    """电容补偿控制器专属控制命令层。"""

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
    def get_remote_command_spec(action: str) -> dict[str, Any]:
        spec = REMOTE_COMMAND_SPECS.get(action)
        if spec is None:
            raise ValueError(f"当前不支持远程控制动作 `{action}`。")
        return spec

    @staticmethod
    def get_remote_command_capabilities() -> list[dict[str, Any]]:
        return [
            {
                "action": action,
                "label": spec["label"],
                "supported": bool(spec.get("supported", True)),
                **({"disabled_reason": spec["disabled_reason"]} if spec.get("disabled_reason") else {}),
            }
            for action, spec in REMOTE_COMMAND_SPECS.items()
        ]

    @staticmethod
    def get_action_label(action: str) -> str:
        if action.startswith("write:"):
            parameter_key = action[6:]
            spec = PARAMETER_WRITE_SPECS.get(parameter_key)
            if spec:
                return f"参数写入 · {spec.label}"
            return f"参数写入 · {parameter_key}"
        return CapacitorBankControlCommandService.CONTROL_ACTION_LABELS.get(action, action)

    @staticmethod
    def normalize_control_result(result: Optional[str]) -> str:
        normalized = str(result or "").strip().lower()
        normalized = CONTROL_RECEIPT_RESULT_ALIASES.get(normalized, normalized)
        if normalized in SUPPORTED_CONTROL_RESULTS:
            return normalized
        return CONTROL_RESULT_FAILED

    @staticmethod
    def _is_terminal_result(result: Optional[str]) -> bool:
        return CapacitorBankControlCommandService.normalize_control_result(result) in TERMINAL_CONTROL_RESULTS

    @staticmethod
    def get_result_label(result: Optional[str]) -> str:
        return CapacitorBankControlCommandService.CONTROL_RESULT_LABELS.get(
            CapacitorBankControlCommandService.normalize_control_result(result),
            "执行异常",
        )

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
        payload: dict[str, Any] = {
            "message_type": CONTROL_COMMAND_MESSAGE_TYPE,
            "protocol_version": CONTROL_PROTOCOL_VERSION,
            "timestamp": datetime.now().isoformat(),
            "device_id": device_id,
            "command": command,
            "command_id": command_id,
        }
        if device_code:
            payload["device_code"] = device_code
        if reason:
            payload["reason"] = reason
        if extras:
            payload.update(extras)
        return payload

    @staticmethod
    def build_control_log_update_event(control_log: DeviceControlLog) -> dict[str, Any]:
        now = datetime.now().isoformat()
        return {
            "type": "device_control_log_update",
            "data": {
                "device_id": control_log.device_id,
                "command_id": str(control_log.id) if control_log.id is not None else None,
                "action": control_log.action,
                "result": control_log.result,
                "reason": control_log.reason,
                "updated_at": now,
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
        event = CapacitorBankControlCommandService.build_control_log_update_event(control_log)
        try:
            control_event_notifier(event)
        except Exception as exc:
            logger.warning(
                "control log notifier failed: device_id=%s command_id=%s action=%s result=%s err=%s",
                control_log.device_id,
                control_log.id,
                control_log.action,
                control_log.result,
                exc,
            )

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
    def build_control_mode_switch_command_args(reason: Optional[str]) -> dict[str, Any]:
        normalized_reason = (reason or "").strip()
        switch_to_auto = "自动" in normalized_reason and "手动" not in normalized_reason
        return CapacitorBankControlCommandService.build_manual_switch_command_args(
            {
                "manual_mode": "auto" if switch_to_auto else "manual",
                "phase": "COMMON",
                "switch_action": "none",
            }
        )

    @staticmethod
    def expire_pending_control_logs(
        session: Session,
        *,
        device_id: Optional[int] = None,
        now: Optional[datetime] = None,
        control_event_notifier: Optional[ControlEventNotifier] = None,
    ) -> list[DeviceControlLog]:
        cutoff = (now or datetime.now()) - get_control_receipt_timeout()
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
            logger.warning(
                "capacitor bank control timeout: device_id=%s command_id=%s action=%s source=%s",
                log.device_id,
                log.id,
                log.action,
                log.command_source,
            )
        session.commit()
        for log in expired_logs:
            CapacitorBankControlCommandService._notify_control_log_update(log, control_event_notifier)
        return expired_logs

    @staticmethod
    def submit_remote_control_command(
        session: Session,
        device: Device,
        *,
        action: str,
        operator: str,
        reason: Optional[str] = None,
        command_args: Optional[dict[str, Any]] = None,
        publish_control_payload=None,
    ) -> dict[str, Any]:
        publish_control_payload = publish_control_payload or publish_control_payload_async

        spec = CapacitorBankControlCommandService.get_remote_command_spec(action)
        if spec.get("supported") is False:
            raise ValueError(str(spec.get("disabled_reason") or f"当前暂不支持远程控制动作 `{action}`。"))
        device_code = getattr(device, "sn", None)
        normalized_reason = reason.strip() if reason else ""
        log_reason = normalized_reason or f"控制台{spec['label']}"
        normalized_command_args: dict[str, Any] = {}
        if action == "manual_switch":
            normalized_command_args = CapacitorBankControlCommandService.build_manual_switch_command_args(command_args)
        elif action == "switch_control_mode":
            normalized_command_args = CapacitorBankControlCommandService.build_control_mode_switch_command_args(normalized_reason or log_reason)

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
        logger.info(
            "capacitor bank remote control queued: device_id=%s device_code=%s command_id=%s action=%s operator=%s source=%s",
            device.id,
            device_code or "-",
            control_log.id,
            action,
            operator,
            "remote-control-api",
        )

        publish_control_payload(
            device.id,
            CapacitorBankControlCommandService.build_command_payload(
                device.id,
                device_code=device_code,
                command="manual_switch" if action == "switch_control_mode" else spec["command"],
                command_id=str(control_log.id),
                reason=normalized_reason or spec["label"],
                extras=normalized_command_args or None,
            ),
            device_code=device_code,
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
        device_repository=None,
        control_event_notifier: Optional[ControlEventNotifier] = None,
    ) -> DeviceControlLog:
        device_repository = device_repository or DeviceRepository

        try:
            control_log_id = int(command_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("控制回执缺少有效 command_id。") from exc

        control_log = device_repository.get_control_log_by_id(session, control_log_id)
        if control_log is None or control_log.device_id != device_id:
            raise ValueError(f"控制回执找不到匹配日志：device_id={device_id}, command_id={command_id}")

        normalized_result = CapacitorBankControlCommandService.normalize_control_result(result)
        if normalized_result not in set(SUPPORTED_CONTROL_RESULTS) - {CONTROL_RESULT_ACCEPTED}:
            raise ValueError("控制回执 result 仅支持 running/success/failed/timeout/rejected。")

        current_result = CapacitorBankControlCommandService.normalize_control_result(control_log.result)
        if current_result in TERMINAL_CONTROL_RESULTS:
            if current_result == normalized_result:
                logger.info(
                    "duplicate terminal control receipt skipped: device_id=%s command_id=%s action=%s result=%s",
                    device_id,
                    control_log.id,
                    control_log.action,
                    normalized_result,
                )
                return control_log

            detail_text = (detail or "").strip()
            suffix = f"迟到回执已忽略: {normalized_result}"
            if detail_text:
                suffix = f"{suffix}: {detail_text}"
            if control_log.reason:
                if suffix not in control_log.reason:
                    control_log.reason = f"{control_log.reason} | {suffix}"
            else:
                control_log.reason = suffix
            session.add(control_log)
            session.flush()
            logger.warning(
                "late terminal receipt ignored: device_id=%s command_id=%s action=%s current_result=%s incoming_result=%s",
                device_id,
                control_log.id,
                control_log.action,
                current_result,
                normalized_result,
            )
            return control_log

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
        logger.info(
            "capacitor bank control receipt applied: device_id=%s command_id=%s action=%s result=%s source=%s",
            device_id,
            control_log.id,
            control_log.action,
            normalized_result,
            control_log.command_source,
        )
        CapacitorBankControlCommandService._notify_control_log_update(control_log, control_event_notifier)
        return control_log
