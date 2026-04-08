import request from '@/utils/request'
import type { Device } from '@/api/device'
import type { WrappedResponse } from '@/types/api'

// 位置类型
export type LocationType =
  | 'park'
  | 'campus'
  | 'site'
  | 'building'
  | 'unit'
  | 'floor'
  | 'room'
  | 'workshop'
  | 'area'
  | 'zone'

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
  full_path?: string
  level?: number
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
  location?: {
    id: number
    name: string
    location_type: string
    full_path?: string
    level?: number
  }
  area_sqm?: number
  manager?: string
}

interface LocationTreeParams {
  root_id?: number
  max_depth?: number
}

interface LocationMutationResult {
  success?: boolean
  message?: string
}

interface RawLocationTreeNode {
  id: number
  name: string
  type?: string
  location_type?: string
  parent_id?: number
  code?: string
  description?: string
  area_sqm?: number
  manager?: string
  contact?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
  full_path?: string
  level?: number
  device_count?: number
  children?: RawLocationTreeNode[]
}

interface RawLocationStatistics {
  location?: {
    id: number
    name: string
    type?: string
    location_type?: string
    full_path?: string
    level?: number
  }
  device_count?: {
    total?: number
    active?: number
    by_energy_type?: Record<string, number>
    by_category?: Record<string, number>
  }
  child_locations_count?: number
  area_sqm?: number
  manager?: string
}

export interface CampusOverviewEntity {
  id: number
  name: string
  code?: string
  location_type: string
  full_path?: string
  derived?: boolean
}

export interface CampusOverviewHierarchySummary {
  location_counts: Record<string, number>
  device_count: number
  active_device_count: number
  meter_count: number
}

export interface CampusOverviewAnalysisSummary {
  time_window: {
    start_time: string
    end_time: string
  }
  total_consumption: number
  realtime_load: number
  active_alarm_count: number
  device_count: number
  meter_count: number
  building_count: number
  estimated_carbon: number
}

export interface CampusOverviewEnergyCategoryItem {
  energy_category: string
  label: string
  total_consumption: number
  avg_load: number
  ratio: number
  estimated_carbon: number
}

export interface CampusOverviewSubItemStatistic {
  sub_item: string
  label: string
  total_consumption: number
  avg_load: number
  device_count: number
  energy_categories: string[]
}

export interface CampusOverviewRankingItem {
  location_id: number
  name: string
  location_type: string
  full_path?: string
  total_consumption: number
  avg_load: number
  energy_breakdown: Record<string, number>
}

export interface CampusOverviewTrendItem {
  timestamp: string
  total_load: number
  total_consumption: number
}

export interface CampusOverviewAlarmLocation {
  location_id: number
  name: string
  location_type: string
  alarm_count: number
}

export interface CampusOverviewAlarmItem {
  id: number
  device_id: number
  message: string
  severity: string
  category: string
  timestamp: string
  is_resolved: boolean
}

export interface CampusOverviewAlarmSummary {
  time_window?: {
    start_time: string
    end_time: string
  }
  total_count: number
  unresolved_count: number
  resolved_count: number
  by_severity: Record<string, number>
  top_locations: CampusOverviewAlarmLocation[]
  latest: CampusOverviewAlarmItem[]
}

export interface CampusOverview {
  campus_entities: CampusOverviewEntity[]
  hierarchy_summary: CampusOverviewHierarchySummary
  analysis_summary: CampusOverviewAnalysisSummary
  energy_category_summary: CampusOverviewEnergyCategoryItem[]
  subitem_statistics: CampusOverviewSubItemStatistic[]
  location_rankings: {
    areas: CampusOverviewRankingItem[]
    buildings: CampusOverviewRankingItem[]
  }
  realtime_load_trend: CampusOverviewTrendItem[]
  alarm_summary: CampusOverviewAlarmSummary
}

function normalizeLocationTreeNode(node: RawLocationTreeNode): LocationTreeNode {
  return {
    id: node.id,
    name: node.name,
    location_type: (node.location_type || node.type || 'area') as LocationType,
    parent_id: node.parent_id,
    code: node.code,
    description: node.description,
    area_sqm: node.area_sqm,
    manager: node.manager,
    contact: node.contact,
    is_active: node.is_active ?? true,
    created_at: node.created_at || '',
    updated_at: node.updated_at,
    full_path: node.full_path,
    level: node.level,
    device_count: node.device_count,
    children: Array.isArray(node.children) ? node.children.map(normalizeLocationTreeNode) : []
  }
}

function normalizeLocationStatistics(payload: RawLocationStatistics): LocationStatistics {
  return {
    total_devices: payload.device_count?.total || 0,
    active_devices: payload.device_count?.active || 0,
    by_energy_type: payload.device_count?.by_energy_type || {},
    by_device_type: payload.device_count?.by_category || {},
    sub_locations_count: payload.child_locations_count || 0,
    location: payload.location
      ? {
          id: payload.location.id,
          name: payload.location.name,
          location_type: payload.location.location_type || payload.location.type || 'area',
          full_path: payload.location.full_path,
          level: payload.location.level
        }
      : undefined,
    area_sqm: payload.area_sqm,
    manager: payload.manager
  }
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
  return request
    .get<never, WrappedResponse<LocationTypeInfo[]>>('/locations/types')
    .then((response) => response.data || [])
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
  return request
    .get<never, WrappedResponse<RawLocationTreeNode[]>>('/locations/tree', { params })
    .then((response) => (response.data || []).map(normalizeLocationTreeNode))
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
  return request
    .get<never, WrappedResponse<RawLocationStatistics>>(`/locations/${id}/statistics`, {
      params: { recursive }
    })
    .then((response) => normalizeLocationStatistics(response.data || {}))
}

export function getCampusOverview() {
  return request.get<never, CampusOverview>('/campus/overview')
}
