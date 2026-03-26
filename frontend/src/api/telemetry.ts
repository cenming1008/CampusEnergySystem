import request from '@/utils/request'

export interface DeviceData {
  device_id: number
  timestamp: string
  energy_type?: string
  voltage: number | null
  current: number | null
  flow_rate: number | null
  consumption: number
  power_factor?: number | null
  pressure?: number | null
  temperature?: number | null
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
// 注意：已修改为使用新的设备数据端点
export function getHistory(deviceId: number, limit: number = 50) {
  return request.get<never, DeviceData[]>(`/devices/${deviceId}/data?limit=${limit}`)
}

// 获取单个设备的实时分析数据 (用于仪表盘卡片)
export function getAnalysis(deviceId: number) {
  return request.get<never, DeviceAnalysis>(`/analysis/${deviceId}`)
}
