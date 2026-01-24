import request from '@/utils/request'

// 位置类型
export type LocationType = 'building' | 'unit' | 'floor' | 'room' | 'workshop' | 'area' | 'zone'

// 位置类型信息
export interface LocationTypeInfo {
  value: string
  label: string
  description: string
}

// 位置
export interface Location {
  id: number
  name: string
  location_type: LocationType
  parent_id?: number
  code?: string
  description?: string
  area_sqm?: number
  manager?: string
  contact?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

// 位置树节点
export interface LocationTreeNode extends Location {
  children?: LocationTreeNode[]
  device_count?: number
}

// 创建位置请求
export interface LocationCreateRequest {
  name: string
  location_type: string
  parent_id?: number
  code?: string
  description?: string
  area_sqm?: number
  manager?: string
  contact?: string
}

// 更新位置请求
export interface LocationUpdateRequest {
  name?: string
  location_type?: string
  parent_id?: number
  code?: string
  description?: string
  area_sqm?: number
  manager?: string
  contact?: string
}

// 位置统计
export interface LocationStatistics {
  total_devices: number
  active_devices: number
  by_energy_type: Record<string, number>
  by_device_type: Record<string, number>
  sub_locations_count: number
}

// 获取位置列表
export function getLocations(params?: {
  location_type?: string
  parent_id?: number
  is_active?: boolean
}) {
  return request.get<any, Location[]>('/locations/', { params })
}

// 获取位置类型列表
export function getLocationTypes() {
  return request.get<any, { code: number; data: LocationTypeInfo[] }>('/locations/types')
}

// 获取顶级位置
export function getRootLocations() {
  return request.get<any, Location[]>('/locations/roots')
}

// 获取位置树
export function getLocationTree(rootId?: number, maxDepth?: number) {
  const params: any = {}
  if (rootId) params.root_id = rootId
  if (maxDepth) params.max_depth = maxDepth
  return request.get<any, { code: number; data: LocationTreeNode[] }>('/locations/tree', { params })
}

// 搜索位置
export function searchLocations(keyword: string) {
  return request.get<any, Location[]>('/locations/search', { params: { keyword } })
}

// 获取位置详情
export function getLocationDetail(id: number) {
  return request.get<any, Location>(`/locations/${id}`)
}

// 创建位置
export function createLocation(data: LocationCreateRequest) {
  return request.post<any, Location>('/locations/', data)
}

// 更新位置
export function updateLocation(id: number, data: LocationUpdateRequest) {
  return request.put<any, Location>(`/locations/${id}`, data)
}

// 删除位置
export function deleteLocation(id: number, force: boolean = false) {
  return request.delete<any, any>(`/locations/${id}`, { params: { force } })
}

// 获取子位置
export function getChildLocations(id: number, recursive: boolean = false) {
  return request.get<any, Location[]>(`/locations/${id}/children`, { params: { recursive } })
}

// 获取位置下的设备
export function getLocationDevices(id: number, params?: {
  recursive?: boolean
  energy_type?: string
  is_active?: boolean
}) {
  return request.get<any, any[]>(`/locations/${id}/devices`, { params })
}

// 将设备分配到位置
export function assignDeviceToLocation(locationId: number, deviceId: number) {
  return request.post<any, any>(`/locations/${locationId}/devices`, { device_id: deviceId })
}

// 获取位置统计
export function getLocationStatistics(id: number, recursive: boolean = true) {
  return request.get<any, { code: number; data: LocationStatistics }>(`/locations/${id}/statistics`, {
    params: { recursive }
  })
}
