import request from '@/utils/request'
import type { Device } from '@/api/device'
import type { WrappedResponse } from '@/types/api'

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

interface LocationTreeParams {
  root_id?: number
  max_depth?: number
}

interface LocationMutationResult {
  success?: boolean
  message?: string
}

// 获取位置列表
export function getLocations(params?: {
  location_type?: string
  parent_id?: number
  is_active?: boolean
}) {
  return request.get<never, Location[]>('/locations/', { params })
}

// 获取位置类型列表
export function getLocationTypes() {
  return request.get<never, WrappedResponse<LocationTypeInfo[]>>('/locations/types')
}

// 获取顶级位置
export function getRootLocations() {
  return request.get<never, Location[]>('/locations/roots')
}

// 获取位置树
export function getLocationTree(rootId?: number, maxDepth?: number) {
  const params: LocationTreeParams = {}
  if (rootId) params.root_id = rootId
  if (maxDepth) params.max_depth = maxDepth
  return request.get<never, WrappedResponse<LocationTreeNode[]>>('/locations/tree', { params })
}

// 搜索位置
export function searchLocations(keyword: string) {
  return request.get<never, Location[]>('/locations/search', { params: { keyword } })
}

// 获取位置详情
export function getLocationDetail(id: number) {
  return request.get<never, Location>(`/locations/${id}`)
}

// 创建位置
export function createLocation(data: LocationCreateRequest) {
  return request.post<LocationCreateRequest, Location>('/locations/', data)
}

// 更新位置
export function updateLocation(id: number, data: LocationUpdateRequest) {
  return request.put<LocationUpdateRequest, Location>(`/locations/${id}`, data)
}

// 删除位置
export function deleteLocation(id: number, force: boolean = false) {
  return request.delete<never, LocationMutationResult>(`/locations/${id}`, { params: { force } })
}

// 获取子位置
export function getChildLocations(id: number, recursive: boolean = false) {
  return request.get<never, Location[]>(`/locations/${id}/children`, { params: { recursive } })
}

// 获取位置下的设备
export function getLocationDevices(id: number, params?: {
  recursive?: boolean
  energy_type?: string
  is_active?: boolean
}) {
  return request.get<never, Device[]>(`/locations/${id}/devices`, { params })
}

// 将设备分配到位置
export function assignDeviceToLocation(locationId: number, deviceId: number) {
  return request.post<{ device_id: number }, LocationMutationResult>(`/locations/${locationId}/devices`, { device_id: deviceId })
}

// 获取位置统计
export function getLocationStatistics(id: number, recursive: boolean = true) {
  return request.get<never, WrappedResponse<LocationStatistics>>(`/locations/${id}/statistics`, {
    params: { recursive }
  })
}
