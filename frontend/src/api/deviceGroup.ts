import request from '@/utils/request'

// 分组类型
export type GroupType = 'production' | 'office' | 'critical' | 'backup'

// 分组类型信息
export interface GroupTypeInfo {
  value: string
  label: string
  description: string
}

// 设备分组
export interface DeviceGroup {
  id: number
  name: string
  code?: string
  description?: string
  group_type?: GroupType
  parent_id?: number
  manager?: string
  contact?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

// 创建分组请求
export interface GroupCreateRequest {
  name: string
  code?: string
  description?: string
  group_type?: string
  parent_id?: number
  manager?: string
  contact?: string
}

// 更新分组请求
export interface GroupUpdateRequest {
  name?: string
  code?: string
  description?: string
  group_type?: string
  parent_id?: number
  manager?: string
  contact?: string
}

// 分组统计
export interface GroupStatistics {
  total_devices: number
  active_devices: number
  by_energy_type: Record<string, number>
  by_device_type: Record<string, number>
}

// 所有分组统计
export interface AllGroupStatistics {
  group_id: number
  group_name: string
  device_count: number
  active_count: number
}

// 获取分组列表
export function getDeviceGroups(params?: {
  group_type?: string
  parent_id?: number
  is_active?: boolean
}) {
  return request.get<any, DeviceGroup[]>('/device-groups/', { params })
}

// 获取分组类型列表
export function getGroupTypes() {
  return request.get<any, { code: number; data: GroupTypeInfo[] }>('/device-groups/types')
}

// 搜索分组
export function searchGroups(keyword: string) {
  return request.get<any, DeviceGroup[]>('/device-groups/search', { params: { keyword } })
}

// 获取所有分组统计
export function getAllGroupStatistics() {
  return request.get<any, { code: number; data: AllGroupStatistics[] }>('/device-groups/statistics')
}

// 获取分组详情
export function getGroupDetail(id: number) {
  return request.get<any, DeviceGroup>(`/device-groups/${id}`)
}

// 创建分组
export function createGroup(data: GroupCreateRequest) {
  return request.post<any, DeviceGroup>('/device-groups/', data)
}

// 更新分组
export function updateGroup(id: number, data: GroupUpdateRequest) {
  return request.put<any, DeviceGroup>(`/device-groups/${id}`, data)
}

// 删除分组
export function deleteGroup(id: number, force: boolean = false) {
  return request.delete<any, any>(`/device-groups/${id}`, { params: { force } })
}

// 获取分组中的设备
export function getGroupDevices(id: number, params?: {
  energy_type?: string
  is_active?: boolean
}) {
  return request.get<any, any[]>(`/device-groups/${id}/devices`, { params })
}

// 添加设备到分组
export function addDeviceToGroup(groupId: number, deviceId: number, note?: string) {
  return request.post<any, any>(`/device-groups/${groupId}/devices`, {
    device_id: deviceId,
    note
  })
}

// 批量添加设备到分组
export function batchAddDevicesToGroup(groupId: number, deviceIds: number[]) {
  return request.post<any, { code: number; data: { success_count: number; total: number } }>(
    `/device-groups/${groupId}/devices/batch`,
    { device_ids: deviceIds }
  )
}

// 从分组中移除设备
export function removeDeviceFromGroup(groupId: number, deviceId: number) {
  return request.delete<any, any>(`/device-groups/${groupId}/devices/${deviceId}`)
}

// 获取分组统计
export function getGroupStatistics(id: number) {
  return request.get<any, { code: number; data: GroupStatistics }>(`/device-groups/${id}/statistics`)
}

// 获取分组设备数量
export function getGroupDeviceCount(id: number) {
  return request.get<any, { code: number; data: { count: number } }>(`/device-groups/${id}/devices/count`)
}
