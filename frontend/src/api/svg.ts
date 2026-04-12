import request from '@/utils/request'

export interface SVGOperationsProfile {
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
  created_at?: string
  updated_at?: string
    device_label_zh?: string | null
    asset_number?: string | null
  fixed_asset_code?: string | null
  qr_code_number?: string | null
  asset_group?: string | null
  // 现场安装类
  distribution_room?: string | null
  distribution_cabinet?: string | null
  circuit?: string | null
  area?: string | null
  building?: string | null
  install_date?: string | null
  commission_date?: string | null
  field_number?: string | null
  // 管理责任类
  om_responsible?: string | null
  inspection_responsible?: string | null
  department?: string | null
  management_unit?: string | null
  contact_phone?: string | null
  warranty_expiry?: string | null
  maintenance_cycle_days?: number | null
  // 平台建模类
  device_group?: string | null
  device_tree_level?: string | null
  monitor_screen_position?: string | null
  alarm_policy?: string | null
  device_alias?: string | null
  display_name?: string | null
  created_at?: string
  updated_at?: string
}

export function getSVGOperationsProfile(deviceId: number) {
  return request
    .get<never, SVGOperationsProfile>(`/svg/${deviceId}/operations-profile`)
}

export function upsertSVGOperationsProfile(deviceId: number, data: Partial<SVGOperationsProfile>) {
  return request
    .put<Partial<SVGOperationsProfile>, SVGOperationsProfile>(`/svg/${deviceId}/operations-profile`, data)
}

// ── 遥测扩展数据 ──────────────────────────────────────────────────────────────

export interface SVGTelemetry {
  device_id: number
  timestamp: string
  // 三相电压 (V)
  voltage_a?: number | null
  voltage_b?: number | null
  voltage_c?: number | null
  // 三相电流 (A)
  current_a?: number | null
  current_b?: number | null
  current_c?: number | null
  frequency?: number | null
  svg_reactive_output?: number | null
  capacity_utilization?: number | null
  output_direction?: string | null
  // 状态位
  run_status?: boolean | null
  stop_status?: boolean | null
  auto_mode?: boolean | null
  local_mode?: boolean | null
  breaker_status?: boolean | null
  module_status?: boolean | null
  fan_status?: boolean | null
  comm_status?: boolean | null
  // 故障位
  overvoltage_fault?: boolean | null
  undervoltage_fault?: boolean | null
  overcurrent_fault?: boolean | null
  overtemp_fault?: boolean | null
  module_fault?: boolean | null
  fan_fault?: boolean | null
  comm_fault?: boolean | null
  current_fault_code?: string | null
  current_alarm_code?: string | null
  // 温度和内部量
  cabinet_temp?: number | null
  module_temp?: number | null
  igbt_temp?: number | null
  dc_bus_voltage?: number | null
  heatsink_temp?: number | null
}

export function getSVGTelemetryLatest(deviceId: number) {
  return request
    .get<never, SVGTelemetry>(`/svg/${deviceId}/telemetry/latest`)
}

export function getSVGTelemetryHistory(
  deviceId: number,
  params?: { start?: string; end?: string; limit?: number },
) {
  return request
    .get<never, SVGTelemetry[]>(`/svg/${deviceId}/telemetry`, { params })
}
