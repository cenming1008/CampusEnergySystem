import request from '@/utils/request'
import type { WrappedResponse, JsonObject } from '@/types/api'
import { normalizeCompensationDevice } from '@/shared/compensationDevices'

export interface DeviceArchive {
  id: number
  name: string
  sn: string
  device_type: string
  device_subtype?: string
  device_category?: string
  energy_type?: string
  archive_status?: 'pending' | 'complete'
  location?: string
  rated_capacity?: number
  unit?: string
  description?: string
  created_at?: string
  updated_at?: string
}

export interface RuntimeStatus {
  device_id: number
  code: string
  label: string
  is_active: boolean
  is_online: boolean
  ingestion_status?: string
  unresolved_alarm_count: number
  last_message_at?: string | null
  last_success_at?: string | null
  latest_timestamp?: string | null
}

export interface DeviceRealtime {
  device_id: number
  timestamp?: string | null
  energy_type?: string
  consumption?: number | null
  flow_rate?: number | null
  voltage?: number | null
  current?: number | null
  power_factor?: number | null
  reactive_power?: number | null
  pressure?: number | null
  temperature?: number | null
  supply_temp?: number | null
  return_temp?: number | null
  heat_flow?: number | null
  temperature_delta?: number | null
}

export interface DeviceAlarmRecord {
  id: number
  device_id: number
  message: string
  severity?: string
  category?: string
  source?: string
  timestamp: string
  last_seen_at?: string | null
  recovered_at?: string | null
  is_resolved: boolean
  resolved_at?: string | null
  resolved_by?: string | null
  handling_note?: string | null
}

export interface DeviceControlLog {
  id: number
  device_id: number
  action: string
  target_status: boolean
  previous_status?: boolean | null
  operator?: string | null
  command_source?: string
  result?: string
  reason?: string | null
  created_at: string
}

export interface DeviceStatusEvent {
  timestamp: string
  event_type: string
  status: string
  title: string
  detail?: string | null
}

export interface CompensationMonitorSemanticValue {
  value: string | number | null
  source: string
  state: string
}

export interface CompensationMonitorControlMode {
  value: string
  source: string
  state: string
}

export interface CompensationMonitorCircuitSummary {
  running_count: number | null
  total_count: number | null
  has_realtime_state: boolean
  source: string
  state: string
}

export interface CompensationMonitorProfileStatus {
  source_status: string
  is_stale: boolean
}

export interface CompensationMonitorCapabilitiesSummary {
  supports_read: boolean
  supports_write: boolean
  supports_remote_control: boolean
}

export interface CompensationMonitor {
  subtype: 'svg' | 'capacitor_bank_controller'
  control_mode: CompensationMonitorControlMode
  circuit_summary: CompensationMonitorCircuitSummary
  profile_status?: CompensationMonitorProfileStatus | null
  key_metrics: Record<string, CompensationMonitorSemanticValue>
  capabilities_summary: CompensationMonitorCapabilitiesSummary
  status_tags?: string[]
}

export interface MonitorTemplate {
  template_key: string
  category?: string | null
  subtype?: string | null
  display_name?: string
  specific_panels: string[]
}

export interface MonitorMetricCard {
  key: string
  label: string
  value?: string | number | null
  unit?: string | null
  precision?: number
  source?: string
  state?: string
}

export interface MonitorTrendField {
  key: string
  label: string
  unit?: string | null
  precision?: number
}

export interface MonitorControlSummary {
  supports_remote_control: boolean
  receipt_required: boolean
  supported_commands: string[]
}

export interface MonitorDiagnosticsSummary {
  ingestion_status?: string | null
  is_online?: boolean
  last_message_at?: string | null
  last_success_at?: string | null
}

export interface MonitorTemplateDiagnostics {
  template_key: string
  display_name?: string | null
  category?: string | null
  subtype?: string | null
  metric_coverage: {
    total: number
    live: number
    missing: number
    missing_keys: string[]
  }
  trend_coverage: {
    declared_keys: string[]
    drawable_keys: string[]
    unsupported_keys: string[]
  }
  panel_coverage: {
    specific_panels: string[]
  }
  ingestion_health: MonitorDiagnosticsSummary
  overall_status: 'passed' | 'partial' | 'missing' | 'offline'
}

export interface MonitorOverview {
  archive: DeviceArchive
  runtime_status: RuntimeStatus
  realtime: DeviceRealtime
  ingestion_health: JsonObject
  recent_alarms: DeviceAlarmRecord[]
  recent_control_logs: DeviceControlLog[]
  compensation_monitor?: CompensationMonitor | null
  storage_monitor?: import('@/api/storage').StorageMonitor | null
  alarm_category_counts?: Record<string, number>
  monitor_template?: MonitorTemplate
  metric_cards?: MonitorMetricCard[]
  trend_fields?: MonitorTrendField[]
  control_summary?: MonitorControlSummary
  diagnostics_summary?: MonitorDiagnosticsSummary
  template_diagnostics?: MonitorTemplateDiagnostics
}

export interface TrendPoint {
  timestamp: string
  value?: number | null
  flow_rate?: number | null
  consumption?: number | null
  voltage?: number | null
  current?: number | null
  reactive_power?: number | null
  power_factor?: number | null
}

export interface TrendSummary {
  latest: number
  peak: number
  valley: number
  average: number
}

export interface DeviceTrendResponse {
  device_id: number
  start_time: string
  end_time: string
  points: TrendPoint[]
  summary: TrendSummary
}

export interface MonitorQueryRange {
  start_time?: string
  end_time?: string
  limit?: number
  resolved?: boolean
  hours?: number
}

export function getDeviceMonitorOverview(deviceId: number, options: { silent?: boolean } = {}) {
  return request
    .get<never, WrappedResponse<MonitorOverview>>(`/devices/${deviceId}/monitor/overview`, { silent: options.silent })
    .then((response) => ({
      ...response.data,
      archive: normalizeCompensationDevice(response.data.archive),
    }))
}

export function getDeviceMonitorRealtime(deviceId: number) {
  return request
    .get<never, WrappedResponse<DeviceRealtime>>(`/devices/${deviceId}/monitor/realtime`)
    .then((response) => response.data)
}

export function getDeviceMonitorTrend(deviceId: number, params?: MonitorQueryRange) {
  return request
    .get<never, WrappedResponse<DeviceTrendResponse>>(`/devices/${deviceId}/monitor/trend`, { params })
    .then((response) => response.data)
}

export function getDeviceMonitorAlarms(deviceId: number, params?: MonitorQueryRange) {
  return request
    .get<never, WrappedResponse<{ items: DeviceAlarmRecord[] }>>(
      `/devices/${deviceId}/monitor/alarms`,
      { params: { limit: 50, ...params } }
    )
    .then((response) => response.data)
}

export function getDeviceMonitorControlLogs(deviceId: number, params?: MonitorQueryRange) {
  return request
    .get<never, WrappedResponse<{ items: DeviceControlLog[] }>>(
      `/devices/${deviceId}/monitor/control-logs`,
      { params: { limit: 50, ...params } }
    )
    .then((response) => response.data)
}

export function getDeviceMonitorStatusHistory(deviceId: number, params?: MonitorQueryRange) {
  return request
    .get<never, WrappedResponse<{ items: DeviceStatusEvent[] }>>(
      `/devices/${deviceId}/monitor/status-history`,
      { params: { limit: 30, hours: 72, ...params } }
    )
    .then((response) => response.data)
}

export interface DeviceIngestionHealthItem {
  device_id: number
  is_online: boolean
  status: 'online' | 'degraded' | 'offline' | 'unknown'
  last_message_at?: string | null
  last_success_at?: string | null
  last_failure_at?: string | null
  last_failure_reason?: string | null
  consecutive_failures: number
  total_messages: number
  total_failures: number
  success_rate?: number | null
  updated_at?: string | null
}

export function getIngestionHealthOverview(options: { silent?: boolean } = {}) {
  return request
    .get<never, WrappedResponse<{ items: DeviceIngestionHealthItem[] }>>(
      '/devices/ingestion-health/overview',
      { silent: options.silent }
    )
    .then((response) => response.data.items)
}
