import request from '@/utils/request'

// 历史数据模型（对应后端 EnergyData 表）
export interface DeviceData {
  device_id: number
  timestamp: string
  voltage: number | null
  current: number | null
  power: number | null  // 对应后端的 flow_rate（瞬时功率/流量）
  energy: number  // 对应后端的 consumption（累计消耗量）
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
