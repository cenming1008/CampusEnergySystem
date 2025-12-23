import request from '@/utils/request'

// 对应后端 Device 模型
export interface Device {
  id?: number
  name: string
  sn: string
  device_type: string
  location?: string
  is_active: boolean
  description?: string
  created_at?: string
}

// 1. 获取所有设备
export function getDevices() {
  return request.get<any, Device[]>('/devices/')
}

// 2. 新增设备
export function createDevice(data: Device) {
  return request.post<any, Device>('/devices/', data)
}

// 3. 修改设备 (Put)
export function updateDevice(id: number, data: Device) {
  return request.put<any, Device>(`/devices/${id}`, data)
}

// 4. 删除设备
export function deleteDevice(id: number) {
  return request.delete<any, any>(`/devices/${id}`)
}

// 5. 启停控制 (反向控制)
export function toggleDeviceStatus(id: number, active: boolean) {
  return request.post<any, Device>(`/devices/${id}/toggle?active=${active}`)
}