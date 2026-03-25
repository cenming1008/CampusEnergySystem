import request from '@/utils/request'

export interface DeviceArchive {
  id: number
  name: string
  sn: string
  device_type: string
  device_category?: string
  energy_type?: string
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
  pressure?: number | null
  temperature?: number | null
}

export interface DeviceAlarmRecord {
  id: number
  device_id: number
  message: string
  severity?: string
  category?: string
  source?: string
  timestamp: string
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

export interface MonitorOverview {
  archive: DeviceArchive
  runtime_status: RuntimeStatus
  realtime: DeviceRealtime
  ingestion_health: Record<string, any>
  recent_alarms: DeviceAlarmRecord[]
  recent_control_logs: DeviceControlLog[]
}

export interface TrendPoint {
  timestamp: string
  value?: number | null
  consumption?: number | null
  voltage?: number | null
  current?: number | null
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

interface WrappedResponse<T> {
  success: boolean
  message: string
  data: T
  code: string
}

export function getDeviceMonitorOverview(deviceId: number) {
  return request.get<any, WrappedResponse<MonitorOverview>>(`/devices/${deviceId}/monitor/overview`)
}

export function getDeviceMonitorRealtime(deviceId: number) {
  return request.get<any, WrappedResponse<DeviceRealtime>>(`/devices/${deviceId}/monitor/realtime`)
}

export function getDeviceMonitorTrend(deviceId: number, params?: MonitorQueryRange) {
  return request.get<any, WrappedResponse<DeviceTrendResponse>>(`/devices/${deviceId}/monitor/trend`, { params })
}

export function getDeviceMonitorAlarms(deviceId: number, params?: MonitorQueryRange) {
  return request.get<any, WrappedResponse<{ items: DeviceAlarmRecord[] }>>(
    `/devices/${deviceId}/monitor/alarms`,
    { params: { limit: 50, ...params } }
  )
}

export function getDeviceMonitorControlLogs(deviceId: number, params?: MonitorQueryRange) {
  return request.get<any, WrappedResponse<{ items: DeviceControlLog[] }>>(
    `/devices/${deviceId}/monitor/control-logs`,
    { params: { limit: 50, ...params } }
  )
}

export function getDeviceMonitorStatusHistory(deviceId: number, params?: MonitorQueryRange) {
  return request.get<any, WrappedResponse<{ items: DeviceStatusEvent[] }>>(
    `/devices/${deviceId}/monitor/status-history`,
    { params: { limit: 30, hours: 72, ...params } }
  )
}
