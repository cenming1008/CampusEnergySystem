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

export function downloadReport(params: ReportDownloadParams) {
  return request.get<never, Blob>('/reports/export_csv', {
    params,
    responseType: 'blob',
    timeout: 120000
  })
}
