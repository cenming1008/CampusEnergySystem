import request from '@/utils/request'

export interface CompensationSvgOperationsProfile {
  id?: number
  device_id: number
  model_number?: string | null
  rated_voltage?: number | null
  rated_frequency?: number | null
  comm_address?: string | null
  software_version?: string | null
  hardware_version?: string | null
  protocol_version?: string | null
  module_count?: number | null
  single_module_capacity?: number | null
  device_label_zh?: string | null
  asset_number?: string | null
  fixed_asset_code?: string | null
  qr_code_number?: string | null
  asset_group?: string | null
  distribution_room?: string | null
  distribution_cabinet?: string | null
  circuit?: string | null
  area?: string | null
  building?: string | null
  install_date?: string | null
  commission_date?: string | null
  field_number?: string | null
  om_responsible?: string | null
  inspection_responsible?: string | null
  department?: string | null
  management_unit?: string | null
  contact_phone?: string | null
  warranty_expiry?: string | null
  maintenance_cycle_days?: number | null
  device_group?: string | null
  device_tree_level?: string | null
  monitor_screen_position?: string | null
  alarm_policy?: string | null
  device_alias?: string | null
  display_name?: string | null
  created_at?: string
  updated_at?: string
}

export interface CompensationSvgTelemetry {
  device_id: number
  timestamp: string
  voltage_a?: number | null
  voltage_b?: number | null
  voltage_c?: number | null
  current_a?: number | null
  current_b?: number | null
  current_c?: number | null
  frequency?: number | null
  svg_reactive_output?: number | null
  capacity_utilization?: number | null
  output_direction?: string | null
  run_status?: boolean | null
  stop_status?: boolean | null
  auto_mode?: boolean | null
  local_mode?: boolean | null
  breaker_status?: boolean | null
  module_status?: boolean | null
  fan_status?: boolean | null
  comm_status?: boolean | null
  overvoltage_fault?: boolean | null
  undervoltage_fault?: boolean | null
  overcurrent_fault?: boolean | null
  overtemp_fault?: boolean | null
  module_fault?: boolean | null
  fan_fault?: boolean | null
  comm_fault?: boolean | null
  current_fault_code?: string | null
  current_alarm_code?: string | null
  cabinet_temp?: number | null
  module_temp?: number | null
  igbt_temp?: number | null
  dc_bus_voltage?: number | null
  heatsink_temp?: number | null
}

export interface CompensationCapacitorBankTelemetry {
  device_id: number
  timestamp: string
  voltage_a?: number | null
  voltage_b?: number | null
  voltage_c?: number | null
  current_a?: number | null
  current_b?: number | null
  current_c?: number | null
  power_factor_a?: number | null
  power_factor_b?: number | null
  power_factor_c?: number | null
  active_power_a?: number | null
  active_power_b?: number | null
  active_power_c?: number | null
  reactive_power_a?: number | null
  reactive_power_b?: number | null
  reactive_power_c?: number | null
  apparent_power_a?: number | null
  apparent_power_b?: number | null
  apparent_power_c?: number | null
  voltage_thd_a?: number | null
  voltage_thd_b?: number | null
  voltage_thd_c?: number | null
  current_harmonic_a?: number | null
  current_harmonic_b?: number | null
  current_harmonic_c?: number | null
  frequency?: number | null
  temperature?: number | null
  leading_a?: boolean | null
  leading_b?: boolean | null
  leading_c?: boolean | null
  undercurrent_a?: boolean | null
  undercurrent_b?: boolean | null
  undercurrent_c?: boolean | null
  overvoltage_alarm_a?: boolean | null
  overvoltage_alarm_b?: boolean | null
  overvoltage_alarm_c?: boolean | null
  voltage_thd_alarm_a?: boolean | null
  voltage_thd_alarm_b?: boolean | null
  voltage_thd_alarm_c?: boolean | null
  current_thd_alarm_a?: boolean | null
  current_thd_alarm_b?: boolean | null
  current_thd_alarm_c?: boolean | null
  temp_alarm?: boolean | null
  circuit_state_phase_a?: number | null
  circuit_state_phase_b?: number | null
  circuit_state_phase_c?: number | null
  circuit_state_common_1?: number | null
  circuit_state_common_2?: number | null
  circuit_state_common_3?: number | null
}

export interface CompensationCapacitorBankControlCapabilities {
  supports_read: boolean
  supports_write: boolean
  supports_remote_control: boolean
  write_status_message: string
  remote_control_status_message: string
  protocol_version: string
  command_message_type: string
  receipt_message_type: string
  control_topic_template: string
  receipt_topic: string
  receipt_timeout_seconds: number
  supported_results: string[]
}

export interface CompensationCapacitorBankControlProfile {
  device_id: number
  switch_on_power_factor?: number | null
  switch_off_power_factor?: number | null
  switch_on_delay_seconds?: number | null
  switch_off_delay_seconds?: number | null
  common_output_circuit_count?: number | null
  split_output_circuit_count?: number | null
  common_capacity_code?: string | null
  split_capacity_code?: string | null
  common_step_capacity_kvar?: number | null
  split_step_capacity_kvar?: number | null
  ct_primary_current?: number | null
  overvoltage_threshold?: number | null
  voltage_harmonic_threshold?: number | null
  current_harmonic_threshold?: number | null
  temperature_upper_limit?: number | null
  alarm_drive_event?: string | null
  baud_rate?: number | null
  terminal_assignment_scheme?: string | null
  current_polarity_identification_enabled?: boolean | null
  source?: string | null
  snapshot_timestamp?: string | null
  source_status: 'fresh' | 'stale' | 'empty' | 'unknown'
  is_stale: boolean
  created_at?: string | null
  updated_at?: string | null
  capabilities: CompensationCapacitorBankControlCapabilities
}

export interface CompensationCapacitorBankControlWriteRequest {
  parameter_key: string
  target_value: string | number | boolean
  reason?: string
}

export interface CompensationCapacitorBankControlWriteResponse {
  accepted: boolean
  status: string
  message: string
  command_id?: string | null
}

export interface CompensationCapacitorBankRemoteCommandRequest {
  action: 'manual_switch_test' | 'reset_alarm' | 'switch_control_mode'
  reason?: string
}

export interface CompensationCapacitorBankRemoteCommandResponse {
  accepted: boolean
  status: string
  message: string
  command_id?: string | null
}

export function getCompensationSvgOperationsProfile(deviceId: number) {
  return request
    .get<never, CompensationSvgOperationsProfile>(`/devices/${deviceId}/compensation/svg/operations-profile`, { silent: true })
}

export function upsertCompensationSvgOperationsProfile(
  deviceId: number,
  data: Partial<CompensationSvgOperationsProfile>,
) {
  return request
    .put<Partial<CompensationSvgOperationsProfile>, CompensationSvgOperationsProfile>(
      `/devices/${deviceId}/compensation/svg/operations-profile`,
      data,
    )
}

export function getCompensationSvgTelemetryLatest(deviceId: number) {
  return request
    .get<never, CompensationSvgTelemetry>(`/devices/${deviceId}/compensation/svg/telemetry/latest`, { silent: true })
}

export function getCompensationSvgTelemetryHistory(
  deviceId: number,
  params?: { start?: string; end?: string; limit?: number },
) {
  return request
    .get<never, CompensationSvgTelemetry[]>(`/devices/${deviceId}/compensation/svg/telemetry`, { params, silent: true })
}

export function getCompensationCapacitorBankTelemetryLatest(deviceId: number) {
  return request
    .get<never, CompensationCapacitorBankTelemetry>(
      `/devices/${deviceId}/compensation/capacitor-bank/telemetry/latest`,
      { silent: true },
    )
}

export function getCompensationCapacitorBankTelemetryHistory(
  deviceId: number,
  params?: { start?: string; end?: string; limit?: number },
) {
  return request
    .get<never, CompensationCapacitorBankTelemetry[]>(
      `/devices/${deviceId}/compensation/capacitor-bank/telemetry`,
      { params, silent: true },
    )
}

export function getCompensationCapacitorBankControlProfile(deviceId: number) {
  return request
    .get<never, CompensationCapacitorBankControlProfile>(
      `/devices/${deviceId}/compensation/capacitor-bank/control-profile`,
      { silent: true },
    )
}

export function writeCompensationCapacitorBankControlProfile(
  deviceId: number,
  data: CompensationCapacitorBankControlWriteRequest,
) {
  return request
    .post<CompensationCapacitorBankControlWriteRequest, CompensationCapacitorBankControlWriteResponse>(
      `/devices/${deviceId}/compensation/capacitor-bank/control-profile/write`,
      data,
    )
}

export function sendCompensationCapacitorBankRemoteCommand(
  deviceId: number,
  data: CompensationCapacitorBankRemoteCommandRequest,
) {
  return request
    .post<CompensationCapacitorBankRemoteCommandRequest, CompensationCapacitorBankRemoteCommandResponse>(
      `/devices/${deviceId}/compensation/capacitor-bank/remote-command`,
      data,
    )
}
