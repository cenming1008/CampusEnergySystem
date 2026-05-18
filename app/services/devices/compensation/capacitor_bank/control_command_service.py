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
    "queued": CONTROL_RESULT_RUNNING,
    "queue": CONTROL_RESULT_RUNNING,
    "pending": CONTROL_RESULT_RUNNING,
    "in_queue": CONTROL_RESULT_RUNNING,
    "in-queue": CONTROL_RESULT_RUNNING,
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
        CONTROL_RESULT_SUCCESS: "已处理",
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
    def _lock_device_row(session: Session, device_id: int) -> Optional[Device]:
        stmt = select(Device).where(Device.id == device_id)
        if hasattr(stmt, "with_for_update"):
            stmt = stmt.with_for_update()
        return session.exec(stmt).first()

    @staticmethod
    def _get_pending_remote_control_log(session: Session, device_id: int) -> Optional[DeviceControlLog]:
        stmt = (
            select(DeviceControlLog)
            .where(DeviceControlLog.device_id == device_id)
            .where(DeviceControlLog.result.in_(tuple(PENDING_CONTROL_RESULTS)))
            .where(DeviceControlLog.command_source == "remote-control-api")
            .order_by(DeviceControlLog.created_at.desc())
            .limit(1)
        )
        pending_log = session.exec(stmt).first()
        return pending_log if isinstance(pending_log, DeviceControlLog) else None

    @staticmethod
    def _resolve_control_mode_from_log(log: Optional[DeviceControlLog]) -> Optional[str]:
        if log is None:
            return None
        if CapacitorBankControlCommandService.normalize_control_result(log.result) != CONTROL_RESULT_SUCCESS:
            return None
        if log.action not in {"switch_control_mode", "manual_switch"}:
            return None
        reason = log.reason or ""
        if "控制模式切换" not in reason:
            return None
        if "手动模式" in reason:
            return "manual"
        if "自动模式" in reason:
            return "auto"
        return None

    @staticmethod
    def _get_latest_control_mode_log(session: Session, device_id: int) -> Optional[DeviceControlLog]:
        stmt = (
            select(DeviceControlLog)
            .where(DeviceControlLog.device_id == device_id)
            .where(DeviceControlLog.command_source == "remote-control-api")
            .where(DeviceControlLog.result == CONTROL_RESULT_SUCCESS)
            .where(DeviceControlLog.action.in_(("manual_switch", "switch_control_mode")))
            .order_by(DeviceControlLog.created_at.desc(), DeviceControlLog.id.desc())
            .limit(1)
        )
        log = session.exec(stmt).first()
        return log if isinstance(log, DeviceControlLog) else None

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
        """构造 0x44 手动控制 extras。

        - phase=A/B/C：分补，不允许指定 group。
        - phase=COMMON：公补，必须指定 group=1/2/3，对应 JKWF-LCD 协议的公补 1/2/3 寄存器组。
        - switch_action=none 仅在 manual_mode 切换（mode_change）场景使用，此时 phase=COMMON、group=1。
        """
        args = dict(command_args or {})
        manual_mode = str(args.get("manual_mode") or "").strip().lower()
        phase = str(args.get("phase") or "").strip().upper()
        switch_action = str(args.get("switch_action") or "").strip().lower()
        raw_group = args.get("group")

        if manual_mode not in {"manual", "auto"}:
            raise ValueError("手动投切必须指定 manual_mode=manual/auto。")
        if phase not in {"A", "B", "C", "COMMON"}:
            raise ValueError("手动投切必须指定 phase=A/B/C/COMMON。")
        if switch_action not in {"none", "on", "off"}:
            raise ValueError("手动投切必须指定 switch_action=none/on/off。")

        group: Optional[int]
        if phase == "COMMON":
            try:
                group = int(raw_group) if raw_group is not None else None
            except (TypeError, ValueError) as exc:
                raise ValueError("公补投切的 group 必须是 1/2/3。") from exc
            if group is None:
                if switch_action == "none":
                    # 模式切换桥接：保持向后兼容，默认落到第 1 组寄存器。
                    group = 1
                else:
                    raise ValueError("公补投切必须指定 group=1/2/3。")
            if group not in {1, 2, 3}:
                raise ValueError("公补投切的 group 必须是 1/2/3。")
        else:
            if raw_group is not None:
                raise ValueError("分补投切（phase=A/B/C）不允许指定 group。")
            group = None

        mode_code = 1 if manual_mode == "manual" else 0
        phase_code = {"A": 0, "B": 1, "C": 2, "COMMON": 3}[phase]
        switch_action_code = {"none": 0, "on": 0x11, "off": 0x22}[switch_action]

        extras: dict[str, Any] = {
            "manual_mode": manual_mode,
            "phase": phase,
            "switch_action": switch_action,
            "protocol_function_code": "0x44",
            "manual_mode_code": mode_code,
            "phase_code": phase_code,
            "switch_action_code": switch_action_code,
        }
        if phase == "COMMON" and group is not None:
            extras["common_group"] = group
            extras["common_group_code"] = group - 1
        return extras

    @staticmethod
    def build_control_mode_switch_command_args(reason: Optional[str]) -> dict[str, Any]:
        normalized_reason = (reason or "").strip()
        switch_to_auto = "自动" in normalized_reason and "手动" not in normalized_reason
        return CapacitorBankControlCommandService.build_manual_switch_command_args(
            {
                "manual_mode": "auto" if switch_to_auto else "manual",
                "phase": "COMMON",
                "switch_action": "none",
                "group": 1,
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
    def _manual_switch_target(reason: Optional[str]) -> Optional[tuple[str, str, Optional[int]]]:
        text = reason or ""
        if "手动投切" not in text:
            return None
        if "A 相" in text or "A相" in text:
            phase = "A"
        elif "B 相" in text or "B相" in text:
            phase = "B"
        elif "C 相" in text or "C相" in text:
            phase = "C"
        elif "共补" in text or "公补" in text or "COMMON" in text.upper():
            phase = "COMMON"
        else:
            return None

        if "投入" in text:
            action = "on"
        elif "切除" in text:
            action = "off"
        else:
            return None

        group: Optional[int] = None
        if phase == "COMMON":
            normalized = text.replace(" ", "").replace("\u3000", "").lower()
            for candidate in (1, 2, 3):
                if (
                    f"{candidate}组" in normalized
                    or f"组{candidate}" in normalized
                    or f"common_{candidate}" in normalized
                    or f"common{candidate}" in normalized
                ):
                    group = candidate
                    break
        return phase, action, group

    @staticmethod
    def _manual_switch_count_field(phase: str, group: Optional[int] = None) -> Optional[str]:
        if phase in {"A", "B", "C"}:
            return {
                "A": "phase_a_circuit_running_count",
                "B": "phase_b_circuit_running_count",
                "C": "phase_c_circuit_running_count",
            }[phase]
        if phase == "COMMON":
            if group in {1, 2, 3}:
                return f"common_group_{group}_running_count"
            # 兼容旧日志：reason 里没有 1/2/3 组信息时，回退到公补总投入数。
            return "common_circuit_running_count"
        return None

    @staticmethod
    def _numeric_count(value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _latest_telemetry_before(session: Session, device_id: int, created_at: datetime):
        from app.models.compensation import CapacitorBankTelemetry

        stmt = (
            select(CapacitorBankTelemetry)
            .where(CapacitorBankTelemetry.device_id == device_id)
            .where(CapacitorBankTelemetry.timestamp < created_at)
            .order_by(CapacitorBankTelemetry.timestamp.desc())
            .limit(1)
        )
        return session.exec(stmt).first()

    @staticmethod
    def reconcile_failed_manual_switch_with_telemetry(
        session: Session,
        *,
        device_id: int,
        telemetry: Any,
        control_event_notifier: Optional[ControlEventNotifier] = None,
    ) -> list[DeviceControlLog]:
        """Use fresh circuit telemetry to correct false-negative manual switch receipts."""
        telemetry_time = getattr(telemetry, "timestamp", None)
        if telemetry_time is None:
            return []

        cutoff = telemetry_time - get_control_receipt_timeout()
        stmt = (
            select(DeviceControlLog)
            .where(DeviceControlLog.device_id == device_id)
            .where(DeviceControlLog.action == "manual_switch")
            .where(DeviceControlLog.command_source == "remote-control-api")
            .where(DeviceControlLog.result.in_((CONTROL_RESULT_FAILED, CONTROL_RESULT_TIMEOUT)))
            .where(DeviceControlLog.created_at >= cutoff)
            .where(DeviceControlLog.created_at <= telemetry_time)
            .order_by(DeviceControlLog.created_at.asc())
        )
        candidates = list(session.exec(stmt).all())
        reconciled: list[DeviceControlLog] = []

        for log in candidates:
            target = CapacitorBankControlCommandService._manual_switch_target(log.reason)
            if target is None:
                continue
            phase, switch_action, group = target
            count_field = CapacitorBankControlCommandService._manual_switch_count_field(phase, group)
            if count_field is None:
                continue
            before = CapacitorBankControlCommandService._latest_telemetry_before(session, device_id, log.created_at)
            before_count = CapacitorBankControlCommandService._numeric_count(getattr(before, count_field, None))
            after_count = CapacitorBankControlCommandService._numeric_count(getattr(telemetry, count_field, None))
            if before_count is None or after_count is None:
                continue

            changed_as_requested = (
                (switch_action == "on" and after_count > before_count)
                or (switch_action == "off" and after_count < before_count)
            )
            if not changed_as_requested:
                continue

            target_label = phase if group is None else f"{phase}{group}"
            suffix = f"遥测复核已处理: {target_label} {switch_action} {before_count}->{after_count}"
            log.result = CONTROL_RESULT_SUCCESS
            if log.reason:
                if suffix not in log.reason:
                    log.reason = f"{log.reason} | {suffix}"
            else:
                log.reason = suffix
            session.add(log)
            reconciled.append(log)
            logger.info(
                "manual switch false-negative receipt reconciled: device_id=%s command_id=%s phase=%s group=%s action=%s before=%s after=%s",
                device_id,
                log.id,
                phase,
                group,
                switch_action,
                before_count,
                after_count,
            )

        if reconciled:
            session.flush()
            for log in reconciled:
                CapacitorBankControlCommandService._notify_control_log_update(log, control_event_notifier)
        return reconciled

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

        CapacitorBankControlCommandService._lock_device_row(session, device.id)
        CapacitorBankControlCommandService.expire_pending_control_logs(session, device_id=device.id)
        pending_log = CapacitorBankControlCommandService._get_pending_remote_control_log(session, device.id)
        if pending_log is not None:
            logger.warning(
                "capacitor bank remote control rejected due to pending command: device_id=%s command_id=%s action=%s source=%s",
                device.id,
                pending_log.id,
                pending_log.action,
                "remote-control-api",
            )
            raise ValueError("当前设备已有待完成的远程控制，请等待设备回执或超时收口后再试。")

        if action == "manual_switch":
            latest_mode = CapacitorBankControlCommandService._resolve_control_mode_from_log(
                CapacitorBankControlCommandService._get_latest_control_mode_log(session, device.id)
            )
            if latest_mode == "auto":
                raise ValueError("当前为自动模式，请先切换到手动模式后再执行手动投切。")

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
        if normalized_result == CONTROL_RESULT_SUCCESS:
            suffix = "设备回执已处理"
            if control_log.reason:
                if suffix not in control_log.reason:
                    control_log.reason = f"{control_log.reason} | {suffix}"
            else:
                control_log.reason = suffix
        elif detail_text:
            if normalized_result == CONTROL_RESULT_RUNNING:
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
