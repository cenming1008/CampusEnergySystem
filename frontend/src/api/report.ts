import request from '@/utils/request'

export type ReportType = 'energy_detail' | 'alarm_history' | 'carbon_emission' | 'multi_energy_summary' | 'device_history'

export interface ReportDownloadParams {
  report_type: ReportType
  device_id?: number
  energy_type?: string
  resolved?: boolean
  start_time?: string
  end_time?: string
  limit?: number
  fields?: string
}

export interface DeviceHistoryFieldOption {
  key: string
  label: string
  default: boolean
}

export interface DeviceHistoryFieldGroup {
  key: string
  label: string
  fields: DeviceHistoryFieldOption[]
}

export interface DeviceHistoryFieldConfig {
  device_id: number
  template: string
  required_fields: string[]
  default_fields: string[]
  groups: DeviceHistoryFieldGroup[]
}

function resolveReportDateSegment(params: ReportDownloadParams) {
  const raw = params.end_time || params.start_time || new Date().toISOString()
  return raw.slice(0, 10).replace(/-/g, '')
}

export function buildReportDownloadName(params: ReportDownloadParams) {
  if (params.report_type === 'device_history' && params.device_id) {
    return `${params.report_type}_${params.device_id}_${resolveReportDateSegment(params)}.csv`
  }
  return `${params.report_type}_${resolveReportDateSegment(params)}.csv`
}

export function downloadReport(params: ReportDownloadParams) {
  return request.get<never, Blob>('/reports/export_csv', {
    params,
    responseType: 'blob',
    timeout: 120000
  })
}

export function getDeviceHistoryFields(deviceId: number) {
  return request.get<never, DeviceHistoryFieldConfig>('/reports/device-history-fields', {
    params: { device_id: deviceId }
  })
}
