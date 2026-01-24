import request from '@/utils/request'

// 维护类型
export type MaintenanceType = 'routine' | 'repair' | 'inspection' | 'upgrade' | 'calibration'

// 维护状态
export type MaintenanceStatus = 'scheduled' | 'in_progress' | 'completed' | 'cancelled'

// 维护类型信息
export interface MaintenanceTypeInfo {
  value: string
  label: string
  description: string
}

// 维护状态信息
export interface MaintenanceStatusInfo {
  value: string
  label: string
  description: string
}

// 维护记录
export interface MaintenanceRecord {
  id: number
  device_id: number
  maintenance_type: MaintenanceType
  status: MaintenanceStatus
  scheduled_time: string
  start_time?: string
  end_time?: string
  title: string
  description?: string
  operator?: string
  created_by?: string
  cost?: number
  parts_replaced?: string
  result?: string
  next_maintenance_date?: string
  created_at: string
  updated_at?: string
}

// 创建维护请求
export interface MaintenanceCreateRequest {
  device_id: number
  maintenance_type: string
  scheduled_time: string
  title: string
  description?: string
  operator?: string
  created_by?: string
}

// 更新维护请求
export interface MaintenanceUpdateRequest {
  scheduled_time?: string
  title?: string
  description?: string
  operator?: string
  cost?: number
  parts_replaced?: string
  result?: string
  next_maintenance_date?: string
}

// 完成维护请求
export interface MaintenanceCompleteRequest {
  result?: string
  cost?: number
  parts_replaced?: string
  next_maintenance_date?: string
}

// 维护统计
export interface MaintenanceStatistics {
  total_count: number
  by_status: Record<string, number>
  by_type: Record<string, number>
  total_cost: number
  avg_duration_hours: number
  completed_count: number
  overdue_count: number
}

// 获取维护记录列表
export function getMaintenanceList(params?: {
  device_id?: number
  maintenance_type?: string
  status?: string
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}) {
  return request.get<any, MaintenanceRecord[]>('/maintenance/', { params })
}

// 获取维护类型列表
export function getMaintenanceTypes() {
  return request.get<any, { code: number; data: MaintenanceTypeInfo[] }>('/maintenance/types')
}

// 获取维护状态列表
export function getMaintenanceStatuses() {
  return request.get<any, { code: number; data: MaintenanceStatusInfo[] }>('/maintenance/statuses')
}

// 获取维护详情
export function getMaintenanceDetail(id: number) {
  return request.get<any, MaintenanceRecord>(`/maintenance/${id}`)
}

// 创建维护记录
export function createMaintenance(data: MaintenanceCreateRequest) {
  return request.post<any, MaintenanceRecord>('/maintenance/', data)
}

// 更新维护记录
export function updateMaintenance(id: number, data: MaintenanceUpdateRequest) {
  return request.put<any, MaintenanceRecord>(`/maintenance/${id}`, data)
}

// 开始维护
export function startMaintenance(id: number, operator?: string) {
  return request.post<any, MaintenanceRecord>(`/maintenance/${id}/start`, { operator })
}

// 完成维护
export function completeMaintenance(id: number, data: MaintenanceCompleteRequest) {
  return request.post<any, MaintenanceRecord>(`/maintenance/${id}/complete`, data)
}

// 取消维护
export function cancelMaintenance(id: number, reason?: string) {
  return request.post<any, MaintenanceRecord>(`/maintenance/${id}/cancel`, { reason })
}

// 删除维护记录
export function deleteMaintenance(id: number) {
  return request.delete<any, any>(`/maintenance/${id}`)
}

// 获取设备维护历史
export function getDeviceMaintenanceHistory(deviceId: number, limit: number = 10) {
  return request.get<any, MaintenanceRecord[]>(`/maintenance/device/${deviceId}/history`, {
    params: { limit }
  })
}

// 获取即将到期的维护
export function getUpcomingMaintenance(days: number = 7) {
  return request.get<any, MaintenanceRecord[]>('/maintenance/upcoming/list', {
    params: { days }
  })
}

// 获取逾期维护
export function getOverdueMaintenance() {
  return request.get<any, MaintenanceRecord[]>('/maintenance/overdue/list')
}

// 获取维护统计
export function getMaintenanceStatistics(params?: {
  device_id?: number
  start_date?: string
  end_date?: string
}) {
  return request.get<any, { code: number; data: MaintenanceStatistics }>('/maintenance/statistics/summary', { params })
}
