"""
JKWF-LCD V5.0 协议解码

负责将协议原始寄存器值解码为语义字段：
- 寄存器 0x00：16 位状态标志位 → 各相超前/滞后、欠流、过压、谐波告警、温度告警
- 寄存器 0x01~0x03：电容回路投切状态（高/低各 8 bit 对应 8 路）

数值单位换算（设备原始值 → 工程量）：
  电压   × 0.1  → V
  电流   × 0.1  → A
  功率因数 × 0.001 → 无单位 (-1.000 ~ +1.000)
  THD   × 0.1  → %
  频率   × 0.01 → Hz
  温度   × 0.1  → °C
"""

from __future__ import annotations

from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# 寄存器 0x00 状态标志位定义（位序 0=LSB）
# ──────────────────────────────────────────────────────────────────────────────

STATUS_BITS: dict[str, int] = {
    "leading_a": 0,           # A 相超前（1=超前, 0=滞后）
    "leading_b": 1,           # B 相超前
    "leading_c": 2,           # C 相超前
    "undercurrent_a": 3,      # A 相欠流
    "undercurrent_b": 4,      # B 相欠流
    "undercurrent_c": 5,      # C 相欠流
    "overvoltage_alarm_a": 6,  # A 相过压
    "overvoltage_alarm_b": 7,  # B 相过压
    "overvoltage_alarm_c": 8,  # C 相过压
    "voltage_thd_alarm_a": 9,  # A 相电压谐波超限
    "voltage_thd_alarm_b": 10, # B 相电压谐波超限
    "voltage_thd_alarm_c": 11, # C 相电压谐波超限
    "current_thd_alarm_a": 12, # A 相电流谐波超限
    "current_thd_alarm_b": 13, # B 相电流谐波超限
    "current_thd_alarm_c": 14, # C 相电流谐波超限
    "temp_alarm": 15,          # 温度超限
}


def decode_status_flags(raw: int) -> dict[str, bool]:
    """将寄存器 0x00 原始值解码为各状态布尔字段。"""
    return {name: bool(raw & (1 << bit)) for name, bit in STATUS_BITS.items()}


# ──────────────────────────────────────────────────────────────────────────────
# 投切状态寄存器解码（0x01 ~ 0x03）
# ──────────────────────────────────────────────────────────────────────────────

def decode_circuit_states(
    reg1: int,
    reg2: int,
    reg3: int,
) -> dict[str, int]:
    """
    将三个 16-bit 投切状态寄存器解码为 6 个 8-bit 分组。

    协议定义：
      reg1 (0x01): 高 8 位 = A 相回路 1-8，低 8 位 = B 相回路 1-8
      reg2 (0x02): 高 8 位 = C 相回路 1-8，低 8 位 = 公补 1-8
      reg3 (0x03): 高 8 位 = 公补 9-16，低 8 位 = 公补 17-24

    每个 bit=1 表示对应回路已投入，bit=0 表示已切除。
    """
    return {
        "circuit_state_phase_a": (reg1 >> 8) & 0xFF,
        "circuit_state_phase_b": reg1 & 0xFF,
        "circuit_state_phase_c": (reg2 >> 8) & 0xFF,
        "circuit_state_common_1": reg2 & 0xFF,
        "circuit_state_common_2": (reg3 >> 8) & 0xFF,
        "circuit_state_common_3": reg3 & 0xFF,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 完整遥测解码入口
# ──────────────────────────────────────────────────────────────────────────────

def decode_jkwf_payload(data: dict[str, Any]) -> dict[str, Any]:
    """
    对已经过字段别名归一化的 payload 应用 JKWF-LCD 特有解码：
    - 解码状态标志位
    - 解码投切状态寄存器

    仅当对应字段存在时才写入，不覆盖已有值。
    """
    result: dict[str, Any] = {}

    # 状态标志位解码
    raw_flags = data.get("jkwf_status_flags")
    if raw_flags is not None:
        try:
            result.update(decode_status_flags(int(raw_flags)))
        except (ValueError, TypeError):
            pass

    # 投切状态寄存器解码（三个寄存器必须同时存在）
    reg1 = data.get("circuit_state_reg_1")
    reg2 = data.get("circuit_state_reg_2")
    reg3 = data.get("circuit_state_reg_3")
    if reg1 is not None and reg2 is not None and reg3 is not None:
        try:
            result.update(decode_circuit_states(int(reg1), int(reg2), int(reg3)))
        except (ValueError, TypeError):
            pass

    return result
