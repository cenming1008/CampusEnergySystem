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

interface AlarmRequestOptions {
  silent?: boolean
}

// 获取未处理报警
export function getAlarms(params: {
  limit?: number
  device_id?: number
  resolved?: boolean
  start_time?: string
  end_time?: string
} = {}) {
  return request.get<never, Alarm[]>('/alarms/', {
    params: {
      limit: params.limit ?? 20,
      device_id: params.device_id,
      resolved: params.resolved,
      start_time: params.start_time,
      end_time: params.end_time,
    },
    silent: true
  } as AlarmRequestOptions)
}

// 解决单条报警
export function resolveAlarm(alarmId: number, handlingNote?: string) {
  const params = new URLSearchParams()
  if (handlingNote?.trim()) params.set('handling_note', handlingNote.trim())
  const suffix = params.toString() ? `?${params.toString()}` : ''
  return request.post<never, ApiResponse<{ alarm_id: number }>>(`/alarms/resolve/${alarmId}${suffix}`)
}

// 一键解决所有报警
export function resolveAllAlarms() {
  return request.post<never, ApiResponse<{ count: number }>>('/alarms/resolve-all')
}
