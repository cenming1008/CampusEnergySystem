"""
故障诊断领域规则：健康分数计算、报警/运行数据分析、诊断建议生成。

所有函数为纯函数，不依赖数据库或 I/O。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


# 电压稳定性判定的额定电压
RATED_VOLTAGE = 380.0


# ==================== 数据结构 ====================


@dataclass(frozen=True)
class FDDConfig:
    """故障诊断阈值配置（来自 settings）。"""
    voltage_fluctuation_limit: float
    overload_ratio: float
    rated_power: float
    alarm_threshold: int


@dataclass(frozen=True)
class AlarmStats:
    """报警统计快照。"""
    total_count: int
    unresolved_count: int


@dataclass(frozen=True)
class RunningStats:
    """运行数据统计快照。"""
    voltage_stability: str  # "Good" | "Poor" | "Unknown"
    avg_load_factor: float
    is_overloaded: bool
    fluctuation: float  # 百分比
    max_current: float
    avg_current: float


@dataclass(frozen=True)
class TelemetrySample:
    """单条遥测样本，用于 RunningStats 计算。"""
    voltage: Optional[float]
    current: Optional[float]
    flow_rate: Optional[float]


@dataclass(frozen=True)
class HealthScore:
    """健康分数评估结果。"""
    score: int  # 0-100
    deductions: list[str]


# ==================== 规则函数 ====================


def empty_running_stats() -> RunningStats:
    """无数据时的运行统计占位。"""
    return RunningStats(
        voltage_stability="Unknown",
        avg_load_factor=0.0,
        is_overloaded=False,
        fluctuation=0.0,
        max_current=0.0,
        avg_current=0.0,
    )


def compute_running_stats(
    samples: Iterable[TelemetrySample],
    config: FDDConfig,
) -> RunningStats:
    """根据遥测样本和配置计算运行统计。"""
    samples_list = list(samples)
    if not samples_list:
        return empty_running_stats()

    # 电压
    voltages = [s.voltage or 0 for s in samples_list if s.voltage is not None]
    if not voltages:
        voltages = [0]
    max_v = max(voltages)
    min_v = min(voltages)
    max_deviation = max(abs(max_v - RATED_VOLTAGE), abs(min_v - RATED_VOLTAGE))
    fluctuation = max_deviation / RATED_VOLTAGE
    voltage_stability = "Poor" if fluctuation > config.voltage_fluctuation_limit else "Good"

    # 电流
    currents = [s.current or 0 for s in samples_list if s.current is not None]
    if not currents:
        currents = [0]
    max_c = max(currents)
    avg_c = sum(currents) / len(currents)

    # 功率与负载率
    avg_power = sum((s.flow_rate or 0) for s in samples_list) / len(samples_list)
    load_factor = avg_power / config.rated_power if config.rated_power else 0.0
    is_overloaded = load_factor > config.overload_ratio

    return RunningStats(
        voltage_stability=voltage_stability,
        avg_load_factor=round(load_factor, 2),
        is_overloaded=is_overloaded,
        fluctuation=round(fluctuation * 100, 1),  # 百分比
        max_current=round(max_c, 2),
        avg_current=round(avg_c, 2),
    )


def calculate_health_score(
    alarm_stats: AlarmStats,
    running_stats: RunningStats,
    config: FDDConfig,
) -> HealthScore:
    """
    计算设备健康分数和扣分明细。

    评分规则：
    - 基础分 100
    - 未解决报警：每个扣 10 分
    - 报警次数超过阈值：超出部分每个扣 10 分
    - 负载过高：扣 20 分
    - 电压不稳定：扣 10 分
    """
    score = 100
    deductions: list[str] = []

    if alarm_stats.unresolved_count > 0:
        deduct = alarm_stats.unresolved_count * 10
        deductions.append(
            f"未解决报警 {alarm_stats.unresolved_count} 个，扣 {deduct} 分"
        )
        score -= deduct

    if alarm_stats.total_count > config.alarm_threshold:
        excess = alarm_stats.total_count - config.alarm_threshold
        deduct = excess * 10
        deductions.append(
            f"报警次数过多（{alarm_stats.total_count} 次，超过阈值 {config.alarm_threshold} 次），扣 {deduct} 分"
        )
        score -= deduct

    if running_stats.is_overloaded:
        deduct = 20
        deductions.append(
            f"负载过高（负载率 {running_stats.avg_load_factor}），扣 {deduct} 分"
        )
        score -= deduct

    if running_stats.voltage_stability == "Poor":
        deduct = 10
        deductions.append(
            f"电压不稳定（波动 {running_stats.fluctuation}%），扣 {deduct} 分"
        )
        score -= deduct

    return HealthScore(score=max(0, score), deductions=deductions)


def generate_suggestions(deductions: list[str]) -> list[str]:
    """根据扣分明细生成诊断建议。"""
    if not deductions:
        return ["设备运行正常，无需处理"]

    suggestions: list[str] = ["设备故障诊断建议："]
    for deduction in deductions:
        if "报警" in deduction:
            if "未解决" in deduction:
                suggestions.append("• 请及时处理未解决的报警，避免故障扩大")
            elif "过多" in deduction:
                suggestions.append("• 报警频率过高，建议检查设备运行状态和报警阈值设置")
        elif "负载" in deduction:
            suggestions.append("• 设备负载过高，建议减少负载或检查设备容量配置")
        elif "电压" in deduction:
            suggestions.append("• 电压波动较大，建议检查供电系统稳定性")
        else:
            suggestions.append(f"• {deduction}")
    return suggestions


def classify_simple_health_status(alarm_count: int) -> tuple[int, str]:
    """根据未解决报警数量计算简化健康分数与状态。"""
    score = max(0, 100 - alarm_count * 10)
    if score >= 80:
        status = "healthy"
    elif score >= 60:
        status = "warning"
    else:
        status = "critical"
    return score, status
