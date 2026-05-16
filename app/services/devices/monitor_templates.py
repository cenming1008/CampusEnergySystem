"""
设备监控模板静态规格。

该模块只承载模板契约常量，不读取数据库、不编排监控主流程。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MonitorMetricSpec:
    key: str
    label: str
    unit: Optional[str]
    precision: int


@dataclass(frozen=True)
class MonitorTemplateSpec:
    template_key: str
    category: str
    subtype: Optional[str]
    display_name: str
    metric_specs: tuple[MonitorMetricSpec, ...]
    trend_specs: tuple[MonitorMetricSpec, ...]
    specific_panels: tuple[str, ...] = ()
    supports_remote_control: bool = False
    receipt_required: bool = False
    supported_commands: tuple[str, ...] = ()


CAPACITOR_BANK_COMMANDS = ("manual_switch", "switch_control_mode", "reset_alarm", "write_parameter")

DRAWABLE_TREND_KEYS = {
    "flow_rate",
    "value",
    "voltage",
    "current",
    "reactive_power",
    "power_factor",
    "consumption",
}

GENERIC_TEMPLATE = MonitorTemplateSpec(
    template_key="generic_device",
    category="generic",
    subtype=None,
    display_name="通用设备",
    metric_specs=(
        MonitorMetricSpec("flow_rate", "实时功率/流量", None, 2),
        MonitorMetricSpec("consumption", "累计读数", None, 2),
        MonitorMetricSpec("voltage", "电压", "V", 1),
        MonitorMetricSpec("current", "电流", "A", 1),
        MonitorMetricSpec("pressure", "压力", None, 2),
        MonitorMetricSpec("temperature", "温度", "degC", 1),
    ),
    trend_specs=(
        MonitorMetricSpec("flow_rate", "实时功率/流量", None, 2),
        MonitorMetricSpec("consumption", "累计读数", None, 2),
        MonitorMetricSpec("voltage", "电压", "V", 1),
        MonitorMetricSpec("current", "电流", "A", 1),
        MonitorMetricSpec("pressure", "压力", None, 2),
        MonitorMetricSpec("temperature", "温度", "degC", 1),
    ),
)

ELECTRIC_TRENDS = (
    MonitorMetricSpec("reactive_power", "无功功率", "kvar", 2),
    MonitorMetricSpec("power_factor", "功率因数", None, 3),
    MonitorMetricSpec("voltage", "电压", "V", 1),
    MonitorMetricSpec("current", "电流", "A", 1),
)

CAPACITOR_BANK_TEMPLATE = MonitorTemplateSpec(
    template_key="capacitor_bank_controller",
    category="compensation",
    subtype="capacitor_bank_controller",
    display_name="电容补偿控制器",
    metric_specs=(
        MonitorMetricSpec("reactive_power", "无功功率", "kvar", 2),
        MonitorMetricSpec("power_factor", "功率因数", None, 3),
        MonitorMetricSpec("voltage", "电压", "V", 1),
        MonitorMetricSpec("current", "电流", "A", 1),
        MonitorMetricSpec("running_circuit_count", "投入回路", "路", 0),
        MonitorMetricSpec("capacity_utilization", "容量利用率", "%", 1),
    ),
    trend_specs=ELECTRIC_TRENDS,
    specific_panels=("three_phase", "circuit_state", "harmonic_spectrum", "control_profile", "control_summary"),
    supports_remote_control=True,
    receipt_required=True,
    supported_commands=CAPACITOR_BANK_COMMANDS,
)

SVG_TEMPLATE = MonitorTemplateSpec(
    template_key="svg",
    category="compensation",
    subtype="svg",
    display_name="SVG 无功补偿装置",
    metric_specs=(
        MonitorMetricSpec("reactive_power", "无功功率", "kvar", 2),
        MonitorMetricSpec("power_factor", "功率因数", None, 3),
        MonitorMetricSpec("capacity_utilization", "容量利用率", "%", 1),
        MonitorMetricSpec("cabinet_temperature", "柜内温度", "degC", 1),
        MonitorMetricSpec("module_count", "模块数", "个", 0),
    ),
    trend_specs=ELECTRIC_TRENDS,
    specific_panels=("three_phase", "module_status", "device_profile"),
)

STORAGE_TEMPLATE = MonitorTemplateSpec(
    template_key="storage",
    category="storage",
    subtype=None,
    display_name="储能设备",
    metric_specs=(
        MonitorMetricSpec("soc", "SOC", "%", 1),
        MonitorMetricSpec("soh", "SOH", "%", 1),
        MonitorMetricSpec("active_power", "有功功率", "kW", 2),
        MonitorMetricSpec("run_state", "运行状态", None, 0),
        MonitorMetricSpec("cell_temp_max", "最高温度", "degC", 1),
        MonitorMetricSpec("charge_energy_today", "今日充电量", "kWh", 2),
        MonitorMetricSpec("discharge_energy_today", "今日放电量", "kWh", 2),
    ),
    trend_specs=(
        MonitorMetricSpec("flow_rate", "功率", "kW", 2),
        MonitorMetricSpec("voltage", "电压", "V", 1),
        MonitorMetricSpec("current", "电流", "A", 1),
        MonitorMetricSpec("temperature", "温度", "degC", 1),
    ),
    specific_panels=("storage_realtime", "storage_trend", "storage_status"),
)

METER_TEMPLATE_REGISTRY: dict[str, MonitorTemplateSpec] = {
    "water_meter": MonitorTemplateSpec(
        template_key="water_meter",
        category="water_meter",
        subtype=None,
        display_name="水表",
        metric_specs=(
            MonitorMetricSpec("flow_rate", "瞬时流量", "m³/h", 2),
            MonitorMetricSpec("consumption", "累计读数", "m³", 2),
            MonitorMetricSpec("pressure", "压力", "MPa", 2),
            MonitorMetricSpec("temperature", "温度", "degC", 1),
        ),
        trend_specs=(
            MonitorMetricSpec("flow_rate", "瞬时流量", "m³/h", 2),
            MonitorMetricSpec("consumption", "累计读数", "m³", 2),
            MonitorMetricSpec("pressure", "压力", "MPa", 2),
            MonitorMetricSpec("temperature", "温度", "degC", 1),
        ),
    ),
    "gas_meter": MonitorTemplateSpec(
        template_key="gas_meter",
        category="gas_meter",
        subtype=None,
        display_name="燃气表",
        metric_specs=(
            MonitorMetricSpec("flow_rate", "瞬时流量", "m³/h", 2),
            MonitorMetricSpec("consumption", "累计读数", "m³", 2),
            MonitorMetricSpec("pressure", "压力", "kPa", 2),
        ),
        trend_specs=(
            MonitorMetricSpec("flow_rate", "瞬时流量", "m³/h", 2),
            MonitorMetricSpec("consumption", "累计读数", "m³", 2),
            MonitorMetricSpec("pressure", "压力", "kPa", 2),
        ),
    ),
    "heat_meter": MonitorTemplateSpec(
        template_key="heat_meter",
        category="heat_meter",
        subtype=None,
        display_name="热量表",
        metric_specs=(
            MonitorMetricSpec("consumption", "累计热量", "GJ", 2),
            MonitorMetricSpec("flow_rate", "瞬时热功率", "kW", 2),
            MonitorMetricSpec("supply_temp", "供水温度", "degC", 1),
            MonitorMetricSpec("return_temp", "回水温度", "degC", 1),
            MonitorMetricSpec("temperature_delta", "供回水温差", "degC", 1),
            MonitorMetricSpec("pressure", "压力", "MPa", 2),
        ),
        trend_specs=(
            MonitorMetricSpec("consumption", "累计热量", "GJ", 2),
            MonitorMetricSpec("flow_rate", "瞬时热功率", "kW", 2),
        ),
    ),
    "cooling_meter": MonitorTemplateSpec(
        template_key="cooling_meter",
        category="cooling_meter",
        subtype=None,
        display_name="冷量表",
        metric_specs=(
            MonitorMetricSpec("consumption", "累计冷量", "GJ", 2),
            MonitorMetricSpec("flow_rate", "瞬时冷功率", "kW", 2),
            MonitorMetricSpec("supply_temp", "供水温度", "degC", 1),
            MonitorMetricSpec("return_temp", "回水温度", "degC", 1),
            MonitorMetricSpec("temperature_delta", "供回水温差", "degC", 1),
            MonitorMetricSpec("pressure", "压力", "MPa", 2),
        ),
        trend_specs=(
            MonitorMetricSpec("consumption", "累计冷量", "GJ", 2),
            MonitorMetricSpec("flow_rate", "瞬时冷功率", "kW", 2),
        ),
    ),
}

TEMPLATE_REGISTRY: dict[str, MonitorTemplateSpec] = {
    "generic_device": GENERIC_TEMPLATE,
    "capacitor_bank_controller": CAPACITOR_BANK_TEMPLATE,
    "svg": SVG_TEMPLATE,
    "storage": STORAGE_TEMPLATE,
    **METER_TEMPLATE_REGISTRY,
}

STORAGE_STATE_LABELS = {
    "idle": "空闲",
    "charging": "充电中",
    "discharging": "放电中",
    "fault": "故障",
    "standby": "待机",
}


__all__ = [
    "CAPACITOR_BANK_COMMANDS",
    "CAPACITOR_BANK_TEMPLATE",
    "DRAWABLE_TREND_KEYS",
    "GENERIC_TEMPLATE",
    "METER_TEMPLATE_REGISTRY",
    "MonitorMetricSpec",
    "MonitorTemplateSpec",
    "STORAGE_STATE_LABELS",
    "STORAGE_TEMPLATE",
    "SVG_TEMPLATE",
    "TEMPLATE_REGISTRY",
]
