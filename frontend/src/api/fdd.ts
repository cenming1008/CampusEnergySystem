import request from '@/utils/request'

// 设备诊断统计报告
export interface FDDReport {
  device_id: number
  device_name: string
  alarm_count: number
  health_score: number
  status: 'healthy' | 'warning' | 'critical'  // 健康状态
}

// 单个设备详细诊断结果
export interface FDDDiagnosis {
  device_id: number
  device_name: string
  health_score: number
  suggestions: string[]  // 诊断建议列表
}

// 获取所有设备的故障诊断统计
export function getFDDStats() {
  return request.get<never, FDDReport[]>('/fdd/stats')
}

// 诊断指定设备的健康状况
export function diagnoseDevice(deviceId: number) {
  return request.get<never, FDDDiagnosis>(`/fdd/diagnose/${deviceId}`)
}
