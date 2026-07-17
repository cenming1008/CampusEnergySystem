"""
能源接口请求与响应模型
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EnergyDataCreate(BaseModel):
    """能源数据创建模型"""

    device_id: int
    energy_type: str
    consumption: float
    flow_rate: Optional[float] = None
    timestamp: Optional[datetime] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_factor: Optional[float] = None
    reactive_power: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    supply_temp: Optional[float] = None
    return_temp: Optional[float] = None
    heat_flow: Optional[float] = None


class CarbonSummaryResponse(BaseModel):
    """碳排放汇总响应"""

    total_carbon: float
    by_energy_type: dict
    boundary: Optional[str] = None
    calculation_method: Optional[str] = None
    is_accounting_grade: Optional[bool] = None
    note: Optional[str] = None
    summary_basis: Optional[str] = None


class EnergyStatisticsResponse(BaseModel):
    """能源统计响应"""

    total_consumption: float
    avg_consumption: float
    avg_flow_rate: float
    peak_flow_rate: float
    data_count: int
    consumption_unit: Optional[str] = None
    flow_unit: Optional[str] = None
    consumption_semantics: Optional[str] = None
    consumption_stat_basis: Optional[str] = None
    flow_semantics: Optional[str] = None
    flow_stat_basis: Optional[str] = None
    meter_reset_suspected: Optional[bool] = None
    data_object_kind: Optional[str] = None
    point_kind: Optional[str] = None
    public_fields: Optional[list[str]] = None
    specialized_fields: Optional[list[str]] = None
    null_field_rule: Optional[str] = None


class EnergyOverviewResponse(BaseModel):
    """多能源管理聚合响应。"""

    statistics: dict
    carbon_summary: CarbonSummaryResponse
    overview_boundary: Optional[str] = None
    unit_rule: Optional[str] = None
    cross_energy_mix_allowed: Optional[bool] = None
    field_boundary_rule: Optional[str] = None
    energy_profiles: Optional[dict] = None
    # 合并自原 /analysis/overview 的分析字段；当 include_analysis=False 时为 None
    time_window: Optional[dict] = None
    scope: Optional[dict] = None
    summary: Optional[dict] = None
    trend: Optional[dict] = None
    comparison: Optional[dict] = None
    ranking: Optional[dict] = None
    anomaly: Optional[dict] = None
    insights: Optional[list] = None


class StorageCurrentResponse(BaseModel):
    load_kw: float
    pv_kw: float
    grid_kw: float
    storage_kw: float
    soc: Optional[float] = None


class StorageDispatchOverviewResponse(BaseModel):
    actual_power_kw: float
    target_power_kw: float
    deviation_kw: float
    strategy: Optional[str] = None
    plan_status: str
    solver_status: Optional[str] = None
    fallback_reason: Optional[str] = None
    slot_index: Optional[int] = None
    plan_generated_at: Optional[datetime] = None


class StorageProvenanceResponse(BaseModel):
    load_timestamp: Optional[datetime] = None
    pv_timestamp: Optional[datetime] = None
    storage_timestamp: Optional[datetime] = None
    time_skew_seconds: Optional[float] = None
    is_stale: bool


class StorageEnergyOverviewResponse(BaseModel):
    current: StorageCurrentResponse
    storage_device_ids: list[int]
    data_source: str
    simulation_run_id: Optional[str] = None
    plan_execution_rate: float
    dispatch: StorageDispatchOverviewResponse
    provenance: StorageProvenanceResponse
    timestamp: datetime


class StorageStrategyMetricsResponse(BaseModel):
    grid_import_kwh: float
    grid_export_kwh: float
    energy_cost: float
    demand_cost: float
    degradation_cost: float
    curtailment_cost: float
    cost: float
    peak_grid_kw: float
    pv_self_use_rate: float
    curtailment_kwh: float
    throughput_kwh: float
    equivalent_cycles: float
    terminal_soc: float
    plan_execution_rate: Optional[float] = None
    feasible_slot_rate: float


class StorageStrategiesResponse(BaseModel):
    baseline: StorageStrategyMetricsResponse
    rule: StorageStrategyMetricsResponse
    day_ahead: StorageStrategyMetricsResponse


class StorageStrategyComparisonResponse(BaseModel):
    device_id: int
    data_source: str
    scenario_key: str
    seed: int
    initial_soc: float
    input_series_checksum: str
    solver_status: str
    strategies: StorageStrategiesResponse
