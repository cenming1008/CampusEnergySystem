"""
告警领域规则：故障检测、告警生命周期状态机。

所有函数为纯函数，不依赖数据库或 I/O。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


# ==================== 数据结构 ====================


@dataclass(frozen=True)
class FaultDetection:
    """单条故障检测结果。"""
    category: str
    severity: str
    message: str
    source: str


@dataclass(frozen=True)
class CapacitorThresholds:
    """电容补偿控制器阈值配置。"""
    temperature_upper_limit: Optional[float] = None
    overvoltage_threshold: Optional[float] = None
    voltage_harmonic_threshold: Optional[float] = None
    voltage_harmonic_trigger_margin: float = 0.0
    current_harmonic_threshold: Optional[float] = None


@dataclass(frozen=True)
class ThresholdConfig:
    """通用阈值配置（电压/电流）。"""
    current_max: float = 45.0
    voltage_max: float = 250.0
    voltage_min: float = 190.0


@dataclass(frozen=True)
class MediaThresholds:
    """介质表计公共字段阈值配置。"""
    flow_rate_min: Optional[float] = None
    flow_rate_max: Optional[float] = None
    pressure_min: Optional[float] = None
    pressure_max: Optional[float] = None
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None


@dataclass(frozen=True)
class StorageThresholds:
    """储能设备平台阈值配置。"""
    soc_min: Optional[float] = None
    soc_max: Optional[float] = None
    soh_min: Optional[float] = None
    cell_temp_max: Optional[float] = None
    active_power_abs_max: Optional[float] = None


@dataclass(frozen=True)
class ActiveAlarmState:
    """活跃告警快照，供 domain 逻辑消费。"""
    id: int
    device_id: int
    instance_key: Optional[str]
    category: str
    source: str
    message: str
    severity: str
    timestamp: datetime
    last_seen_at: Optional[datetime]


@dataclass(frozen=True)
class AlarmCreateFields:
    """创建新告警所需字段。"""
    device_id: int
    instance_key: str
    message: str
    severity: str
    category: str
    source: str
    timestamp: datetime
    last_seen_at: datetime


@dataclass(frozen=True)
class AlarmRefreshFields:
    """刷新已有告警所需字段。"""
    instance_key: str
    message: str
    severity: str
    last_seen_at: datetime


@dataclass(frozen=True)
class AlarmRecoverFields:
    """恢复告警所需字段。"""
    recovered_at: datetime


@dataclass(frozen=True)
class ResolveTransition:
    """人工处理告警所需字段。"""
    is_resolved: bool
    resolved_at: datetime
    resolved_by: Optional[str]
    handling_note: Optional[str]


@dataclass
class AlarmTransitionPlan:
    """一次故障检测周期的完整转换计划。"""
    creates: list[AlarmCreateFields] = field(default_factory=list)
    refreshes: list[tuple[int, AlarmRefreshFields]] = field(default_factory=list)  # (alarm_id, fields)
    recoveries: list[tuple[int, AlarmRecoverFields]] = field(default_factory=list)  # (alarm_id, fields)


# ==================== 常量 ====================

SOURCE_DEVICE_NATIVE = "device_native"
SOURCE_PLATFORM_RULE = "platform_rule"
SOURCE_PLATFORM_COMM = "platform_comm"

SVG_FAULT_RULES: list[tuple[str, str, str, str]] = [
    ("overvoltage_fault", "svg_overvoltage", "critical", "SVG 过压故障"),
    ("undervoltage_fault", "svg_undervoltage", "critical", "SVG 欠压故障"),
    ("overcurrent_fault", "svg_overcurrent", "critical", "SVG 过流故障"),
    ("overtemp_fault", "svg_overtemp", "warning", "SVG 过温告警"),
    ("module_fault", "svg_module_fault", "critical", "SVG 模块故障"),
    ("fan_fault", "svg_fan_fault", "warning", "SVG 风机故障"),
    ("comm_fault", "svg_comm_fault", "warning", "SVG 通信故障"),
]


# ==================== 公共工具函数 ====================


def build_instance_key(device_id: int, category: str, source: str) -> str:
    """构造稳定告警实例键。"""
    return f"{device_id}:{source}:{category}"


def infer_severity(message: str) -> str:
    """根据消息内容推断告警级别。"""
    if any(keyword in message for keyword in ("故障", "中断", "离线")):
        return "critical"
    if any(keyword in message for keyword in ("过载", "异常", "超限", "偏高", "偏低")):
        return "warning"
    return "info"


# ==================== 故障检测纯函数 ====================


def evaluate_svg_faults(svg_data: dict[str, Any]) -> list[FaultDetection]:
    """评估 SVG 遥测数据中的故障位，返回检测到的故障列表。"""
    faults: list[FaultDetection] = []

    for field_name, category, severity, base_msg in SVG_FAULT_RULES:
        if svg_data.get(field_name) is True:
            faults.append(FaultDetection(
                category=category,
                severity=severity,
                message=base_msg,
                source=SOURCE_DEVICE_NATIVE,
            ))

    fault_code = svg_data.get("current_fault_code")
    if fault_code:
        faults.append(FaultDetection(
            category="svg_fault_code",
            severity="critical",
            message=f"SVG 故障代码: {fault_code}",
            source=SOURCE_DEVICE_NATIVE,
        ))

    return faults


def evaluate_capacitor_bank_faults(
    cap_data: dict[str, Any],
    thresholds: CapacitorThresholds,
    rated_capacity: float,
    platform_rules_enabled: bool = True,
) -> list[FaultDetection]:
    """评估电容补偿控制器遥测数据中的故障，返回检测到的故障列表。"""
    faults: list[FaultDetection] = []

    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _effective_harmonic_limit(kind: str, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        if kind == "voltage" and value == 2.9:
            return None
        if kind == "current" and value == 29:
            return None
        return value

    # 温度超限
    temperature = _to_float(cap_data.get("temperature"))
    temp_limit = thresholds.temperature_upper_limit
    if cap_data.get("temp_alarm") is True:
        detail = f"{temperature:.1f}°C" if temperature is not None else "状态位触发"
        limit_text = f"（上限 {temp_limit:.1f}°C）" if temp_limit is not None else ""
        faults.append(FaultDetection(
            category="cap_temp_alarm",
            severity="warning",
            message=f"电容补偿柜温度超限：{detail}{limit_text}",
            source=SOURCE_DEVICE_NATIVE,
        ))
    elif platform_rules_enabled and temperature is not None and temp_limit is not None and temperature >= temp_limit:
        detail = f"{temperature:.1f}°C"
        limit_text = f"（上限 {temp_limit:.1f}°C）"
        faults.append(FaultDetection(
            category="cap_temp_alarm",
            severity="warning",
            message=f"电容补偿柜温度超限：{detail}{limit_text}",
            source=SOURCE_PLATFORM_RULE,
        ))

    # 各相检测
    overvoltage_limit = thresholds.overvoltage_threshold
    voltage_harmonic_limit = _effective_harmonic_limit("voltage", thresholds.voltage_harmonic_threshold)
    voltage_harmonic_trigger_limit = (
        voltage_harmonic_limit + thresholds.voltage_harmonic_trigger_margin
        if voltage_harmonic_limit is not None
        else None
    )
    current_harmonic_limit = _effective_harmonic_limit("current", thresholds.current_harmonic_threshold)

    for phase in ("a", "b", "c"):
        phase_upper = phase.upper()
        phase_voltage = _to_float(cap_data.get(f"voltage_{phase}"))

        # 过压
        if cap_data.get(f"overvoltage_alarm_{phase}") is True:
            detail = f"{phase_voltage:.1f}V" if phase_voltage is not None else "状态位触发"
            limit_text = f"（门限 {overvoltage_limit:.1f}V）" if overvoltage_limit is not None else ""
            faults.append(FaultDetection(
                category=f"cap_overvoltage_{phase}",
                severity="warning",
                message=f"{phase_upper} 相过压告警：{detail}{limit_text}",
                source=SOURCE_DEVICE_NATIVE,
            ))
        elif platform_rules_enabled and phase_voltage is not None and overvoltage_limit is not None and phase_voltage >= overvoltage_limit:
            detail = f"{phase_voltage:.1f}V"
            limit_text = f"（门限 {overvoltage_limit:.1f}V）"
            faults.append(FaultDetection(
                category=f"cap_overvoltage_{phase}",
                severity="warning",
                message=f"{phase_upper} 相过压告警：{detail}{limit_text}",
                source=SOURCE_PLATFORM_RULE,
            ))

        # 电压谐波超限
        phase_voltage_thd = _to_float(cap_data.get(f"voltage_thd_{phase}"))
        if cap_data.get(f"voltage_thd_alarm_{phase}") is True:
            detail = f"{phase_voltage_thd:.2f}%" if phase_voltage_thd is not None else "状态位触发"
            limit_text = f"（门限 {voltage_harmonic_limit:.2f}%）" if voltage_harmonic_limit is not None else ""
            faults.append(FaultDetection(
                category=f"cap_voltage_thd_{phase}",
                severity="warning",
                message=f"{phase_upper} 相电压谐波超限：{detail}{limit_text}",
                source=SOURCE_DEVICE_NATIVE,
            ))
        elif (
            platform_rules_enabled
            and
            phase_voltage_thd is not None
            and voltage_harmonic_trigger_limit is not None
            and phase_voltage_thd >= voltage_harmonic_trigger_limit
        ):
            detail = f"{phase_voltage_thd:.2f}%"
            limit_text = f"（门限 {voltage_harmonic_limit:.2f}%）"
            faults.append(FaultDetection(
                category=f"cap_voltage_thd_{phase}",
                severity="warning",
                message=f"{phase_upper} 相电压谐波超限：{detail}{limit_text}",
                source=SOURCE_PLATFORM_RULE,
            ))

        # 电流谐波超限
        phase_current_harmonic = _to_float(cap_data.get(f"current_harmonic_{phase}"))
        if cap_data.get(f"current_thd_alarm_{phase}") is True:
            detail = f"{phase_current_harmonic:.2f}A" if phase_current_harmonic is not None else "状态位触发"
            limit_text = f"（门限 {current_harmonic_limit:.2f}A）" if current_harmonic_limit is not None else ""
            faults.append(FaultDetection(
                category=f"cap_current_thd_{phase}",
                severity="warning",
                message=f"{phase_upper} 相电流谐波超限：{detail}{limit_text}",
                source=SOURCE_DEVICE_NATIVE,
            ))
        elif (
            platform_rules_enabled
            and
            phase_current_harmonic is not None
            and current_harmonic_limit is not None
            and phase_current_harmonic >= current_harmonic_limit
        ):
            detail = f"{phase_current_harmonic:.2f}A"
            limit_text = f"（门限 {current_harmonic_limit:.2f}A）"
            faults.append(FaultDetection(
                category=f"cap_current_thd_{phase}",
                severity="warning",
                message=f"{phase_upper} 相电流谐波超限：{detail}{limit_text}",
                source=SOURCE_PLATFORM_RULE,
            ))

        # 欠流
        if cap_data.get(f"undercurrent_{phase}") is True:
            faults.append(FaultDetection(
                category=f"cap_undercurrent_{phase}",
                severity="info",
                message=f"{phase_upper} 相欠流告警",
                source=SOURCE_DEVICE_NATIVE,
            ))

    # 过补偿
    reactive_power = _to_float(cap_data.get("reactive_power"))
    leading_count = sum(
        1
        for f in ("leading_a", "leading_b", "leading_c")
        if cap_data.get(f) is True
    )
    overcomp_limit = max(5.0, rated_capacity * 0.1)
    if platform_rules_enabled and reactive_power is not None and reactive_power <= -overcomp_limit and leading_count >= 2:
        faults.append(FaultDetection(
            category="cap_overcompensation",
            severity="warning",
            message=f"电容补偿器过补偿：Q={reactive_power:.2f}kVar，{leading_count} 相超前",
            source=SOURCE_PLATFORM_RULE,
        ))

    return faults


def evaluate_threshold_faults(
    data: dict[str, Any],
    thresholds: ThresholdConfig,
    device_category: Optional[str] = None,
) -> list[FaultDetection]:
    """评估通用阈值规则（电压/电流），返回检测到的故障列表。"""
    if device_category == "compensation":
        return []

    faults: list[FaultDetection] = []

    if "current" in data and data["current"] is not None:
        current = float(data["current"])
        if current > thresholds.current_max:
            faults.append(FaultDetection(
                category="current_overload",
                severity="critical",
                message=f"⚠️ 过载报警! 当前: {current}A (上限: {thresholds.current_max}A)",
                source=SOURCE_PLATFORM_RULE,
            ))

    if "voltage" in data and data["voltage"] is not None:
        voltage = float(data["voltage"])
        if voltage > thresholds.voltage_max or voltage < thresholds.voltage_min:
            faults.append(FaultDetection(
                category="voltage_out_of_range",
                severity="warning",
                message=f"⚡ 电压异常! 读数: {voltage}V (范围: {thresholds.voltage_min}-{thresholds.voltage_max}V)",
                source=SOURCE_PLATFORM_RULE,
            ))

    return faults


def evaluate_media_threshold_faults(
    data: dict[str, Any],
    thresholds: MediaThresholds,
) -> list[FaultDetection]:
    """评估介质表计公共字段阈值规则。"""
    faults: list[FaultDetection] = []

    flow_rate = _to_optional_float(data.get("flow_rate"))
    if flow_rate is not None and _outside_range(flow_rate, thresholds.flow_rate_min, thresholds.flow_rate_max):
        faults.append(FaultDetection(
            category="flow_rate_out_of_range",
            severity="warning",
            message=_range_message("流量异常", flow_rate, thresholds.flow_rate_min, thresholds.flow_rate_max),
            source=SOURCE_PLATFORM_RULE,
        ))

    pressure = _to_optional_float(data.get("pressure"))
    if pressure is not None and _outside_range(pressure, thresholds.pressure_min, thresholds.pressure_max):
        faults.append(FaultDetection(
            category="pressure_out_of_range",
            severity="warning",
            message=_range_message("压力异常", pressure, thresholds.pressure_min, thresholds.pressure_max),
            source=SOURCE_PLATFORM_RULE,
        ))

    temperature = _to_optional_float(data.get("temperature"))
    if temperature is not None and _outside_range(temperature, thresholds.temperature_min, thresholds.temperature_max):
        faults.append(FaultDetection(
            category="temperature_out_of_range",
            severity="warning",
            message=_range_message("温度异常", temperature, thresholds.temperature_min, thresholds.temperature_max),
            source=SOURCE_PLATFORM_RULE,
        ))

    return faults


def evaluate_storage_threshold_faults(
    data: dict[str, Any],
    thresholds: StorageThresholds,
) -> list[FaultDetection]:
    """评估储能设备平台阈值规则。"""
    faults: list[FaultDetection] = []

    soc = _to_optional_float(data.get("soc"))
    if soc is not None and _outside_range(soc, thresholds.soc_min, thresholds.soc_max):
        faults.append(FaultDetection(
            category="storage_soc_low" if thresholds.soc_min is not None and soc < thresholds.soc_min else "storage_soc_out_of_range",
            severity="warning",
            message=_range_message("储能 SOC 异常", soc, thresholds.soc_min, thresholds.soc_max),
            source=SOURCE_PLATFORM_RULE,
        ))

    soh = _to_optional_float(data.get("soh"))
    if soh is not None and thresholds.soh_min is not None and soh < thresholds.soh_min:
        faults.append(FaultDetection(
            category="storage_soh_low",
            severity="warning",
            message=_range_message("储能 SOH 偏低", soh, thresholds.soh_min, None),
            source=SOURCE_PLATFORM_RULE,
        ))

    cell_temp_max = _to_optional_float(data.get("cell_temp_max"))
    if cell_temp_max is not None and thresholds.cell_temp_max is not None and cell_temp_max > thresholds.cell_temp_max:
        faults.append(FaultDetection(
            category="storage_cell_temp_high",
            severity="warning",
            message=_range_message("储能最高单体温度偏高", cell_temp_max, None, thresholds.cell_temp_max),
            source=SOURCE_PLATFORM_RULE,
        ))

    active_power = _to_optional_float(data.get("active_power"))
    if (
        active_power is not None
        and thresholds.active_power_abs_max is not None
        and abs(active_power) > thresholds.active_power_abs_max
    ):
        faults.append(FaultDetection(
            category="storage_active_power_out_of_range",
            severity="warning",
            message=f"储能充放电功率异常: {active_power:g} (绝对值上限: {thresholds.active_power_abs_max:g})",
            source=SOURCE_PLATFORM_RULE,
        ))

    return faults


def _to_optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _outside_range(value: float, min_value: Optional[float], max_value: Optional[float]) -> bool:
    if min_value is not None and value < min_value:
        return True
    if max_value is not None and value > max_value:
        return True
    return False


def _range_message(label: str, value: float, min_value: Optional[float], max_value: Optional[float]) -> str:
    if min_value is not None and max_value is not None:
        return f"{label}: {value:g} (范围: {min_value:g}-{max_value:g})"
    if max_value is not None:
        return f"{label}: {value:g} (上限: {max_value:g})"
    if min_value is not None:
        return f"{label}: {value:g} (下限: {min_value:g})"
    return f"{label}: {value:g}"


# ==================== 告警生命周期状态机 ====================


def compute_alarm_transition(
    device_id: int,
    detected_faults: list[FaultDetection],
    active_alarms: list[ActiveAlarmState],
    timestamp: datetime,
    managed_categories: set[str],
) -> AlarmTransitionPlan:
    """
    根据本轮检测到的故障和当前活跃告警，计算 create/refresh/recover 转换计划。
    """
    plan = AlarmTransitionPlan()

    # 按 (source, category) 索引活跃告警
    active_by_key: dict[str, ActiveAlarmState] = {}
    for alarm in active_alarms:
        key = build_instance_key(alarm.device_id, alarm.category, alarm.source)
        active_by_key[key] = alarm

    # 本轮命中的 instance_key 集合
    hit_keys: set[str] = set()

    for fault in detected_faults:
        instance_key = build_instance_key(device_id, fault.category, fault.source)
        hit_keys.add(instance_key)

        existing = active_by_key.get(instance_key)
        if existing is not None:
            # 刷新
            plan.refreshes.append((existing.id, AlarmRefreshFields(
                instance_key=instance_key,
                message=fault.message,
                severity=fault.severity,
                last_seen_at=timestamp,
            )))
        else:
            # 创建
            plan.creates.append(AlarmCreateFields(
                device_id=device_id,
                instance_key=instance_key,
                message=fault.message,
                severity=fault.severity,
                category=fault.category,
                source=fault.source,
                timestamp=timestamp,
                last_seen_at=timestamp,
            ))

    # 恢复：活跃告警中属于 managed_categories 但本轮未命中的
    for key, alarm in active_by_key.items():
        if alarm.category in managed_categories and key not in hit_keys:
            plan.recoveries.append((alarm.id, AlarmRecoverFields(recovered_at=timestamp)))

    return plan


def compute_resolve_transition(
    resolved_by: Optional[str],
    handling_note: Optional[str],
    timestamp: datetime,
) -> ResolveTransition:
    """生成人工处理转换。"""
    return ResolveTransition(
        is_resolved=True,
        resolved_at=timestamp,
        resolved_by=resolved_by,
        handling_note=handling_note,
    )


def get_svg_managed_categories() -> set[str]:
    """返回 SVG 故障检测管理的告警类别集合。"""
    return {rule[1] for rule in SVG_FAULT_RULES} | {"svg_fault_code"}


def get_capacitor_bank_managed_categories() -> set[str]:
    """返回电容补偿控制器故障检测管理的告警类别集合。"""
    return {
        "cap_temp_alarm",
        "cap_overcompensation",
        *(f"cap_overvoltage_{phase}" for phase in ("a", "b", "c")),
        *(f"cap_voltage_thd_{phase}" for phase in ("a", "b", "c")),
        *(f"cap_current_thd_{phase}" for phase in ("a", "b", "c")),
        *(f"cap_undercurrent_{phase}" for phase in ("a", "b", "c")),
    }
