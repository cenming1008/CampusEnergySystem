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

export function getStorageTelemetryHistory(
  deviceId: number,
  params?: { start?: string; end?: string; limit?: number },
) {
  return request.get<never, StorageTelemetry[]>(
    `/devices/${deviceId}/storage/telemetry`,
    { params, silent: true },
  )
}
