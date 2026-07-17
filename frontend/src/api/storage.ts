import request from '@/utils/request'

export interface StorageTelemetry {
  device_id: number
  timestamp: string
  soc?: number | null
  soh?: number | null
  active_power?: number | null
  reactive_power?: number | null
  dc_voltage?: number | null
  dc_current?: number | null
  ac_voltage_a?: number | null
  ac_voltage_b?: number | null
  ac_voltage_c?: number | null
  ac_current_a?: number | null
  ac_current_b?: number | null
  ac_current_c?: number | null
  frequency?: number | null
  cell_temp_max?: number | null
  cell_temp_min?: number | null
  cell_temp_avg?: number | null
  run_state?: string | null
  control_mode?: string | null
  fault_code?: number | null
  alarm_code?: number | null
  charge_energy_today?: number | null
  discharge_energy_today?: number | null
  charge_energy_total?: number | null
  discharge_energy_total?: number | null
  cycle_count?: number | null
  target_active_power?: number | null
  available_charge_power?: number | null
  available_discharge_power?: number | null
  bms_status?: string | null
  pcs_status?: string | null
  grid_status?: string | null
  command_source?: string | null
  data_source?: 'simulated' | 'real' | string | null
  simulation_run_id?: string | null
}

export interface StorageAssetProfileUpdate {
  rated_energy_kwh: number
  rated_power_kw: number
  max_charge_power_kw?: number | null
  max_discharge_power_kw?: number | null
  charge_efficiency: number
  discharge_efficiency: number
  soc_min: number
  soc_max: number
  soc_soft_min: number
  soc_soft_max: number
  rated_ac_voltage?: number | null
  rated_dc_voltage?: number | null
  battery_type?: string | null
  bms_model?: string | null
  pcs_model?: string | null
  protocol_version?: string | null
  installation_location?: string | null
  commission_date?: string | null
  data_source: string
  ems_auto_enabled: boolean
}

export interface StorageAssetProfile extends StorageAssetProfileUpdate {
  device_id: number
}

export interface StorageControlCapabilities {
  commands: Array<'set_active_power' | 'set_control_mode' | 'stop'>
  sources: Array<'manual' | 'rule' | 'day_ahead'>
  control_modes: Array<'auto' | 'manual'>
  power_sign: { charge: 'positive'; discharge: 'negative' }
  ems_auto_enabled: boolean
  ems_global_enabled: boolean
}

export interface StorageControlRequest {
  command: 'set_active_power' | 'set_control_mode' | 'stop'
  source: 'manual' | 'rule' | 'day_ahead'
  target_active_power?: number
  control_mode?: 'auto' | 'manual'
  reason?: string
}

export interface StorageControlResponse {
  accepted: boolean
  status: string
  command_id: string
  message: string
}

export type StorageSimulationScenario =
  | 'sunny_workday'
  | 'cloudy_workday'
  | 'weekend_low_load'
  | 'pv_surplus'
  | 'evening_peak'

export type StorageSimulationFault =
  | 'low_soc'
  | 'overtemperature'
  | 'pcs_fault'
  | 'communication_loss'
  | 'pv_drop'

export interface StorageSimulationCapabilities {
  enabled: boolean
  actions: Array<'set_scenario' | 'set_speed' | 'inject_fault' | 'clear_fault'>
  scenarios: StorageSimulationScenario[]
  speeds: number[]
  faults: StorageSimulationFault[]
}

export interface StorageMonitorMetric {
  value: string | number | null
  source: string
  state: string
}

export interface StorageMonitor {
  key_metrics: {
    soc: StorageMonitorMetric
    soh: StorageMonitorMetric
    active_power: StorageMonitorMetric
    cell_temp_max: StorageMonitorMetric
    cell_temp_min: StorageMonitorMetric
    cell_temp_avg: StorageMonitorMetric
    run_state: StorageMonitorMetric
    control_mode: StorageMonitorMetric
    charge_energy_today: StorageMonitorMetric
    discharge_energy_today: StorageMonitorMetric
    energy_balance_today: StorageMonitorMetric
    cycle_count: StorageMonitorMetric
  }
  latest_timestamp: string | null
  has_telemetry: boolean
}

export function getStorageTelemetryLatest(deviceId: number) {
  return request.get<never, StorageTelemetry>(
    `/devices/${deviceId}/storage/telemetry/latest`,
    { silent: true },
  )
}

export function getStorageProfile(deviceId: number) {
  return request.get<never, StorageAssetProfile>(`/devices/${deviceId}/storage/profile`)
}

export function updateStorageProfile(deviceId: number, body: StorageAssetProfileUpdate) {
  return request.put<never, StorageAssetProfile>(`/devices/${deviceId}/storage/profile`, body)
}

export function getStorageControlCapabilities(deviceId: number) {
  return request.get<never, StorageControlCapabilities>(
    `/devices/${deviceId}/storage/control/capabilities`,
  )
}

export function sendStorageControl(deviceId: number, body: StorageControlRequest) {
  return request.post<never, StorageControlResponse>(`/devices/${deviceId}/storage/control`, body)
}

export function getStorageSimulationCapabilities(deviceId: number) {
  return request.get<never, StorageSimulationCapabilities>(
    `/devices/${deviceId}/storage/simulation/capabilities`,
    { silent: true },
  )
}

export function getStorageTelemetryHistory(
  deviceId: number,
  params?: { start?: string; end?: string; limit?: number },
) {
  return request.get<never, StorageTelemetry[]>(
    `/devices/${deviceId}/storage/telemetry`,
    { params, silent: true },
  )
}
