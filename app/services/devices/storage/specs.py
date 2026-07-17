"""储能控制命令与回执协议常量。"""

from datetime import timedelta

CONTROL_COMMAND_MESSAGE_TYPE = "control_command"
CONTROL_PROTOCOL_VERSION = "storage-v1"
CONTROL_COMMAND_SOURCE = "storage-control-api"
CONTROL_RECEIPT_TIMEOUT = timedelta(seconds=120)

SUPPORTED_STORAGE_COMMANDS = {"set_active_power", "set_control_mode", "stop"}
SUPPORTED_COMMAND_SOURCES = {"manual", "rule", "day_ahead"}
SUPPORTED_CONTROL_MODES = {"auto", "manual"}

SUPPORTED_RESULTS = {"accepted", "running", "success", "failed", "timeout", "rejected"}
PENDING_RESULTS = {"accepted", "running"}
TERMINAL_RESULTS = {"success", "failed", "timeout", "rejected"}
