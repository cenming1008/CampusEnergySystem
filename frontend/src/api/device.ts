import request from '@/utils/request'
import type { SuccessResponse } from '@/types/api'

// 对应后端 Device 模型
export interface Device {
  id?: number
  name: string
  sn: string
  device_type: string
  device_category?: string
  energy_type?: string
  unit?: string
  rated_capacity?: number
  location?: string
  is_active: boolean
  description?: string
  created_at?: string
}

// 设备类型配置（来自后端注册表）
export interface DeviceTypeConfig {
  device_type: string
  category: string
  energy_type: string
  name_zh: string
  name_en: string
  unit: string
  default_capacity: number
  required_fields: string[]
  optional_fields: string[]
  icon: string
  color: string
}

// 1. 获取所有设备
export function getDevices() {
  return request.get<never, Device[]>('/devices/')
}

// 2. 新增设备（智能创建）
export function createDevice(data: Partial<Device>) {
  return request.post<Partial<Device>, Device>('/devices/', data)
}

// 3. 修改设备 (Put)
export function updateDevice(id: number, data: Partial<Device>) {
  return request.put<Partial<Device>, Device>(`/devices/${id}`, data)
}

// 4. 删除设备
export function deleteDevice(id: number) {
  return request.delete<never, void>(`/devices/${id}`)
}

// 5. 启停控制 (反向控制)
export function toggleDeviceStatus(id: number, active: boolean, reason?: string) {
  const params = new URLSearchParams({ active: String(active) })
  if (reason?.trim()) params.set('reason', reason.trim())
  return request.post<never, Device>(`/devices/${id}/toggle?${params.toString()}`)
}

// 6. 获取支持的设备类型列表（从后端动态获取）
export function getDeviceTypes() {
  return request
    .get<never, SuccessResponse<DeviceTypeConfig[]>>('/devices/types')
    .then((response) => response.data)
}

// 7. 获取单个设备类型详情
export function getDeviceTypeInfo(deviceType: string) {
  return request
    .get<never, SuccessResponse<DeviceTypeConfig>>(`/devices/types/${deviceType}`)
    .then((response) => response.data)
}
