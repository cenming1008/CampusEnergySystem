import request from '@/utils/request'
import type { WrappedResponse } from '@/types/api'

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

function unwrapResponse<T>(payload: T | WrappedResponse<T>): T {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return (payload as WrappedResponse<T>).data
  }
  return payload as T
}

function normalizeDeviceData(item: Partial<DeviceData>): DeviceData {
  return {
    device_id: Number(item.device_id || 0),
    timestamp: item.timestamp || '',
    energy_type: item.energy_type,
    voltage: item.voltage ?? null,
    current: item.current ?? null,
    flow_rate: item.flow_rate ?? null,
    consumption: Number(item.consumption || 0),
    power_factor: item.power_factor ?? null,
    pressure: item.pressure ?? null,
    temperature: item.temperature ?? null,
  }
}

function normalizeAnalysis(payload: Partial<DeviceAnalysis>): DeviceAnalysis {
  return {
    device_id: Number(payload.device_id || 0),
    is_active: Boolean(payload.is_active),
    current_power: Number(payload.current_power || 0),
    voltage: Number(payload.voltage || 0),
    current: Number(payload.current || 0),
    today_energy: Number(payload.today_energy || 0),
    today_cost: Number(payload.today_cost || 0),
  }
}

// 获取单个设备的历史趋势 (默认取最近50条)
// 注意：已修改为使用新的设备数据端点
export function getHistory(deviceId: number, limit: number = 50) {
  return request
    .get<never, DeviceData[] | WrappedResponse<DeviceData[]>>(`/devices/${deviceId}/data`, {
      params: { limit }
    })
    .then((payload) => {
      const history = unwrapResponse<DeviceData[]>(payload)
      return Array.isArray(history) ? history.map(normalizeDeviceData) : []
    })
}

// 获取单个设备的实时分析数据 (用于仪表盘卡片)
export function getAnalysis(deviceId: number) {
  return request
    .get<never, DeviceAnalysis | WrappedResponse<DeviceAnalysis>>(`/analysis/${deviceId}`)
    .then((payload) => normalizeAnalysis(unwrapResponse<DeviceAnalysis>(payload)))
}
