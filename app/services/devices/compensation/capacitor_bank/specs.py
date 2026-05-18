"""
电容补偿控制器控制协议与参数规格。

该模块只承载稳定规格常量，不处理数据库、MQTT 下发或业务流程，方便后续新增
其他补偿控制器子型时复用或对比协议边界。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Optional

from app.core.settings import settings

CONTROL_PROFILE_STALE_AFTER = timedelta(hours=1)
CONTROL_RECEIPT_TIMEOUT = timedelta(seconds=120)
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
TERMINAL_CONTROL_RESULTS = {CONTROL_RESULT_SUCCESS, CONTROL_RESULT_FAILED, CONTROL_RESULT_TIMEOUT, CONTROL_RESULT_REJECTED}
GATEWAY_UAT_WRITABLE_PARAMETERS = (
    "switch_on_power_factor",
    "switch_off_power_factor",
    "switch_on_delay_seconds",
    "switch_off_delay_seconds",
    "overvoltage_threshold",
    "voltage_harmonic_threshold",
    "current_harmonic_threshold",
    "temperature_upper_limit",
)


def get_control_receipt_timeout() -> timedelta:
    """返回当前配置的控制回执超时时间。"""
    return timedelta(seconds=max(1, int(settings.compensation_control_receipt_timeout_seconds)))


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
    "voltage_harmonic_threshold": CapacitorBankControlParameterSpec("voltage_harmonic_threshold", "0xDE", "电压谐波门限", "float", 2.9, 50.0),
    "current_harmonic_threshold": CapacitorBankControlParameterSpec("current_harmonic_threshold", "0xDF", "电流谐波门限", "float", 29.0, 200.0),
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

REMOTE_COMMAND_SPECS: dict[str, dict[str, Any]] = {
    "manual_switch": {
        "label": "手动投切",
        "command": "manual_switch",
        "supported": True,
    },
    "manual_switch_test": {
        "label": "手动投切测试",
        "command": "manual_switch_test",
        "supported": True,
    },
    "reset_alarm": {
        "label": "报警复位",
        "command": "reset_alarm",
        "supported": False,
        "disabled_reason": "真实网关暂未提供报警复位寄存器/功能码",
    },
    "switch_control_mode": {
        "label": "控制模式切换",
        "command": "switch_control_mode",
        "supported": True,
    },
}


class ControlProfileWritePreconditionError(RuntimeError):
    """参数写入前置条件不满足。"""


class PendingParameterWriteConflictError(ControlProfileWritePreconditionError):
    """当前设备已有待完成的参数写入，拒绝新的并发写入。"""
