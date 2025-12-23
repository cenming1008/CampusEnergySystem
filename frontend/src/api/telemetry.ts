import request from '@/utils/request'

// 历史数据模型
export interface DeviceData {
  device_id: number
  timestamp: string
  voltage: number
  current: number
  power: number
  energy: number
}

// 实时分析结果模型 (对应后端 /analysis 接口返回)
export interface DeviceAnalysis {
  device_id: number
  is_active: boolean
  current_power: number
  voltage: number
  current: number
  today_energy: number
  today_cost: number
}

// 获取单个设备的历史趋势 (默认取最近50条)
export function getHistory(deviceId: number, limit: number = 50) {
  return request.get<any, DeviceData[]>(`/telemetry/${deviceId}?limit=${limit}`)
}

// 获取单个设备的实时分析数据 (用于仪表盘卡片)
export function getAnalysis(deviceId: number) {
  return request.get<any, DeviceAnalysis>(`/analysis/${deviceId}`)
}