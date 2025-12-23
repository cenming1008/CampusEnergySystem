import request from '@/utils/request'

export interface Alarm {
  id: number
  device_id: number
  message: string
  timestamp: string
  is_resolved: boolean
}

// 获取未处理报警
export function getAlarms(limit: number = 20) {
  return request.get<any, Alarm[]>(`/alarms/?limit=${limit}`)
}

// 一键解决所有报警
export function resolveAllAlarms() {
  return request.post<any, { ok: boolean; count: number }>('/alarms/resolve-all')
}