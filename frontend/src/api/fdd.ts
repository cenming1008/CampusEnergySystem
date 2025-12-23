import request from '@/utils/request'

export interface FDDReport {
  device_id: number
  device_name: string
  alarm_count: number
  health_score: number
}

// 获取 FDD 诊断排行
export function getFDDStats() {
  return request.get<any, FDDReport[]>('/fdd/stats')
}