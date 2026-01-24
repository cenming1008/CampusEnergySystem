import request from '@/utils/request'

// ==================== 类型定义 ====================

// 能源类型
export type EnergyType = 'electricity' | 'water' | 'gas' | 'heat' | 'cooling' | 'steam'

// 能源数据模型
export interface EnergyData {
  device_id: number
  timestamp: string
  energy_type: string
  consumption: number  // 累计消耗量
  flow_rate: number | null  // 瞬时流量/功率
  
  // 电力专用
  voltage?: number | null
  current?: number | null
  power_factor?: number | null
  
  // 水/气专用
  pressure?: number | null
  temperature?: number | null
  
  // 热力专用
  supply_temp?: number | null
  return_temp?: number | null
  heat_flow?: number | null
  
  // 质量指标
  quality_index?: number | null
}

// 碳排放数据模型
export interface CarbonEmission {
  device_id: number
  timestamp: string
  energy_type: string
  energy_consumption: number
  consumption_unit: string
  carbon_factor: number
  carbon_emission: number
  scope?: number
  calculation_method?: string
}

// 碳排放汇总
export interface CarbonSummary {
  total_carbon: number
  by_energy_type: {
    [key: string]: {
      carbon_emission: number       // 修正：与后端字段名一致
      energy_consumption: number    // 修正：与后端字段名一致
      unit: string
    }
  }
}

// 能源统计
export interface EnergyStatistics {
  total_consumption: number
  avg_consumption: number
  avg_flow_rate: number
  peak_flow_rate: number
  data_count: number
}

// 能源类型信息
export interface EnergyTypeInfo {
  value: string
  label: string
  unit: string
}

// 碳排放因子
export interface CarbonFactor {
  factor: number
  unit: string
}

// ==================== API 函数 ====================

/**
 * 获取设备能源数据
 */
export function getEnergyData(params: {
  device_id: number
  energy_type?: string
  start_time?: string
  end_time?: string
  limit?: number
}) {
  return request.get<any, EnergyData[]>(`/energy/data/${params.device_id}`, {
    params: {
      energy_type: params.energy_type,
      start_time: params.start_time,
      end_time: params.end_time,
      limit: params.limit
    }
  })
}

/**
 * 获取能源统计数据
 */
export function getEnergyStatistics(params: {
  energy_type: string
  start_time: string
  end_time: string
  device_id?: number
  period_type?: string
}) {
  return request.get<any, EnergyStatistics>('/energy/statistics', { params })
}

/**
 * 获取碳排放数据
 */
export function getCarbonEmissions(params: {
  device_id?: number
  energy_type?: string
  start_time?: string
  end_time?: string
}) {
  return request.get<any, CarbonEmission[]>('/energy/carbon/emissions', { params })
}

/**
 * 获取碳排放汇总
 */
export function getCarbonSummary(params: {
  start_time: string
  end_time: string
  device_id?: number
}) {
  return request.get<any, CarbonSummary>('/energy/carbon/summary', { params })
}

/**
 * 获取支持的能源类型列表
 */
export function getEnergyTypes() {
  return request.get<any, {
    energy_types: EnergyTypeInfo[]
    device_categories: Array<{ value: string; label: string }>
  }>('/energy/types')
}

/**
 * 获取碳排放因子
 */
export function getCarbonFactors() {
  return request.get<any, {
    carbon_factors: { [key: string]: CarbonFactor }
    description: string
  }>('/energy/carbon/factors')
}

/**
 * 手动计算碳排放
 */
export function calculateCarbon(params: {
  energy_type: string
  consumption: number
}) {
  return request.post<any, {
    success: boolean
    data: {
      energy_type: string
      consumption: number
      consumption_unit: string
      carbon_factor: number
      carbon_emission: number
      emission_unit: string
    }
  }>('/energy/carbon/calculate', null, { params })
}

/**
 * 保存能源数据（一般由后端自动处理，此API用于手动补录）
 */
export function saveEnergyData(data: {
  device_id: number
  energy_type: string
  consumption: number
  flow_rate?: number
  timestamp?: string
  [key: string]: any
}) {
  return request.post<any, EnergyData>('/energy/data', data)
}
