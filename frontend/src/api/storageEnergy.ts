import request from '@/utils/request'

export type StorageScenarioKey =
  | 'sunny_workday'
  | 'cloudy_workday'
  | 'weekend_low_load'
  | 'pv_surplus'
  | 'evening_peak'

export interface StorageEnergyCurrent {
  load_kw: number
  pv_kw: number
  grid_kw: number
  storage_kw: number
  soc: number | null
}

export interface StorageDispatchOverview {
  actual_power_kw: number
  target_power_kw: number
  deviation_kw: number
  strategy: string | null
  plan_status: string
  solver_status: string | null
  fallback_reason: string | null
  slot_index: number | null
  plan_generated_at: string | null
}

export interface StorageEnergyProvenance {
  load_timestamp: string | null
  pv_timestamp: string | null
  storage_timestamp: string | null
  time_skew_seconds: number | null
  is_stale: boolean
}

export interface StorageEnergyOverview {
  current: StorageEnergyCurrent
  storage_device_ids: number[]
  data_source: string
  simulation_run_id: string | null
  plan_execution_rate: number
  dispatch: StorageDispatchOverview
  provenance: StorageEnergyProvenance
  timestamp: string
}

export interface StorageStrategyMetrics {
  grid_import_kwh: number
  grid_export_kwh: number
  energy_cost: number
  demand_cost: number
  degradation_cost: number
  curtailment_cost: number
  cost: number
  peak_grid_kw: number
  pv_self_use_rate: number
  curtailment_kwh: number
  throughput_kwh: number
  equivalent_cycles: number
  terminal_soc: number
  plan_execution_rate: number | null
  feasible_slot_rate: number
}

export interface StorageStrategyComparisonResult {
  device_id: number
  data_source: string
  scenario_key: StorageScenarioKey
  seed: number
  initial_soc: number
  input_series_checksum: string
  solver_status: string
  strategies: {
    baseline: StorageStrategyMetrics
    rule: StorageStrategyMetrics
    day_ahead: StorageStrategyMetrics
  }
}

export interface StorageStrategyComparisonQuery {
  scenario_key: StorageScenarioKey
  seed: number
  initial_soc: number
  device_id?: number
}

export interface StorageDispatchGenerateRequest {
  dispatch_date: string
  scenario_key: StorageScenarioKey
  seed: number
  initial_soc: number
  terminal_soc_target?: number | null
}

export interface StorageDispatchPlanRow {
  id?: number | null
  device_id: number
  dispatch_date: string
  slot_index: number
  interval_minutes: number
  target_active_power: number
  forecast_load_power: number | null
  forecast_pv_power: number | null
  tariff_price: number | null
  expected_soc: number | null
  strategy: string
  strategy_version: string
  solver_status: string
  is_valid: boolean
  failure_reason: string | null
  generated_at: string
  data_source: string
  simulation_run_id: string | null
}

export interface StorageDispatchGenerationResult {
  status: string
  solver_status: string
  dispatch_date: string
  plans: StorageDispatchPlanRow[]
  failure_reason: string | null
}

export function getStorageEnergyOverview(deviceId?: number) {
  return request.get<never, StorageEnergyOverview>('/energy/storage/overview', {
    params: deviceId === undefined ? undefined : { device_id: deviceId },
    silent: true,
  })
}

export function getStorageStrategyComparison(params: StorageStrategyComparisonQuery) {
  return request.get<never, StorageStrategyComparisonResult>('/energy/storage/comparison', {
    params,
    silent: true,
  })
}

export function generateStorageDispatchPlan(
  deviceId: number,
  body: StorageDispatchGenerateRequest,
) {
  return request.post<StorageDispatchGenerateRequest, StorageDispatchGenerationResult>(
    `/devices/${deviceId}/storage/dispatch/generate`,
    body,
  )
}
