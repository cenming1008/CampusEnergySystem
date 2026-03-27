import request from '@/utils/request'

export type ReportType = 'energy_detail' | 'alarm_history' | 'carbon_emission'

export interface ReportDownloadParams {
  report_type: ReportType
  device_id?: number
  energy_type?: string
  resolved?: boolean
  start_time?: string
  end_time?: string
  limit?: number
}

function resolveReportDateSegment(params: ReportDownloadParams) {
  const raw = params.end_time || params.start_time || new Date().toISOString()
  return raw.slice(0, 10).replaceAll('-', '')
}

export function buildReportDownloadName(params: ReportDownloadParams) {
  return `${params.report_type}_${resolveReportDateSegment(params)}.csv`
}

export function downloadReport(params: ReportDownloadParams) {
  return request.get<never, Blob>('/reports/export_csv', {
    params,
    responseType: 'blob',
    timeout: 120000
  })
}
