import request from '@/utils/request'

export interface Alarm {
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

// 后端响应格式
export interface ApiResponse<T> {
  success: boolean
  message: string
  data: T
  code: string
}

// 获取未处理报警
export function getAlarms(limit: number = 20) {
  return request.get<any, Alarm[]>(`/alarms/?limit=${limit}`, { silent: true } as any)
}

// 解决单条报警
export function resolveAlarm(alarmId: number, handlingNote?: string) {
  const params = new URLSearchParams()
  if (handlingNote?.trim()) params.set('handling_note', handlingNote.trim())
  const suffix = params.toString() ? `?${params.toString()}` : ''
  return request.post<any, ApiResponse<{ alarm_id: number }>>(`/alarms/resolve/${alarmId}${suffix}`)
}

// 一键解决所有报警
export function resolveAllAlarms() {
  return request.post<any, ApiResponse<{ count: number }>>('/alarms/resolve-all')
}
