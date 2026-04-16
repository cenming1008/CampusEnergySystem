"""
JKWF-LCD 无功补偿控制器集成

支持通过 MQTT 网关接入 JKWF-LCD V5.0 协议设备数据。
"""
"""JKWF-LCD 协议工具。"""

from .capacity import (
    build_capacity_expansion,
    build_common_stage_slot_kvar,
    build_split_phase_slot_kvar,
    expand_capacity_slots,
    resolve_capacity_pattern,
)

__all__ = [
    "build_capacity_expansion",
    "build_common_stage_slot_kvar",
    "build_split_phase_slot_kvar",
    "expand_capacity_slots",
    "resolve_capacity_pattern",
]
